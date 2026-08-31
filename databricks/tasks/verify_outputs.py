from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pyspark.sql import Row, SparkSession

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

EXPECTED = {
    "P01": "fixtures/p01_full_snapshot/expected/country_current.csv",
    "P02": "fixtures/p02_snapshot_history/expected/customer_history.csv",
    "P07": "fixtures/p07_watermark_soft_delete/expected/customer_current.csv",
    "P10": "fixtures/p10_full_cdc/expected/customer_history.csv",
    "P12": "fixtures/p12_business_events/expected/order_events.csv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--bundle-root", required=True)
    parser.add_argument("--framework-sha", required=True)
    parser.add_argument("--customer-sha", required=True)
    return parser.parse_args()


def require_identifier(value: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"unsafe Unity Catalog identifier: {value!r}")
    return value


def require_sha(value: str, label: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError(f"{label} must be an exact 40-character Git SHA")
    return value


def read_expected(root: Path, pattern: str) -> list[dict[str, str]]:
    with (root / EXPECTED[pattern]).open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.isoformat(timespec="seconds") + "Z"
        return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return str(value)


def canonical(rows: list[dict[str, Any]]) -> list[str]:
    normalized = [{key: as_text(value) for key, value in row.items()} for row in rows]
    return sorted(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in normalized)


def compare(pattern: str, actual: list[dict[str, Any]], expected: list[dict[str, str]]) -> dict[str, Any]:
    actual_canonical = canonical(actual)
    expected_canonical = canonical(expected)
    passed = actual_canonical == expected_canonical
    result: dict[str, Any] = {
        "pattern": pattern,
        "status": "passed" if passed else "failed",
        "actual_count": len(actual),
        "expected_count": len(expected),
    }
    if not passed:
        result["missing"] = sorted(set(expected_canonical) - set(actual_canonical))
        result["unexpected"] = sorted(set(actual_canonical) - set(expected_canonical))
    return result


def rows_for_columns(spark: SparkSession, table: str, columns: list[str]) -> list[dict[str, Any]]:
    return [row.asDict(recursive=True) for row in spark.table(table).select(*columns).collect()]


def sequence_component(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, Row):
        return int(value[field])
    if isinstance(value, dict):
        return int(value[field])
    if hasattr(value, "asDict"):
        return int(value.asDict(recursive=True)[field])
    if isinstance(value, (tuple, list)):
        return int(value[0])
    return int(value)


def p02_rows(spark: SparkSession, catalog: str) -> list[dict[str, Any]]:
    presence = {
        (row["customer_id"], int(row["_snapshot_id"]))
        for row in spark.table(f"{catalog}.legacy_bronze.customer_snapshot")
        .select("customer_id", "_snapshot_id")
        .collect()
    }
    output: list[dict[str, Any]] = []
    for row in spark.table(f"{catalog}.legacy_silver.customer_history").collect():
        data = row.asDict(recursive=True)
        start = sequence_component(data.get("__START_AT"), "_snapshot_id")
        end = sequence_component(data.get("__END_AT"), "_snapshot_id")
        customer_id = data["customer_id"]
        if end is None:
            end_reason = ""
        elif (customer_id, end) in presence:
            end_reason = "changed"
        else:
            end_reason = "absent_delete"
        output.append(
            {
                "customer_id": customer_id,
                "name": data["name"],
                "segment": data["segment"],
                "status": data["status"],
                "start_snapshot": start,
                "end_snapshot": end,
                "is_current": end is None,
                "end_reason": end_reason,
            }
        )
    return output


def p10_rows(spark: SparkSession, catalog: str) -> list[dict[str, Any]]:
    delete_events = {
        (row["customer_id"], int(row["source_lsn"]))
        for row in spark.table(f"{catalog}.sales_bronze.customer_cdc")
        .where("_operation = 'd'")
        .select("customer_id", "source_lsn")
        .collect()
    }
    output: list[dict[str, Any]] = []
    for row in spark.table(f"{catalog}.sales_silver.customer_history").collect():
        data = row.asDict(recursive=True)
        start = sequence_component(data.get("__START_AT"), "source_lsn")
        end = sequence_component(data.get("__END_AT"), "source_lsn")
        customer_id = data["customer_id"]
        if end is None:
            end_reason = ""
        elif (customer_id, end) in delete_events:
            end_reason = "cdc_delete"
        else:
            end_reason = "changed"
        output.append(
            {
                "customer_id": customer_id,
                "name": data["name"],
                "status": data["status"],
                "address": data["address"],
                "start_lsn": start,
                "end_lsn": end,
                "is_current": end is None,
                "end_reason": end_reason,
            }
        )
    return output


def write_verification_record(
    spark: SparkSession,
    catalog: str,
    *,
    framework_sha: str,
    customer_sha: str,
    status: str,
    summary: dict[str, Any],
) -> None:
    payload = [
        {
            "verified_at": datetime.now(timezone.utc),
            "certification_level": "C3",
            "framework_sha": framework_sha,
            "customer_sha": customer_sha,
            "status": status,
            "summary_json": json.dumps(summary, sort_keys=True),
        }
    ]
    spark.createDataFrame(payload).write.mode("append").saveAsTable(
        f"{catalog}.certification_control.c3_verification"
    )


def main() -> None:
    args = parse_args()
    catalog = require_identifier(args.catalog)
    framework_sha = require_sha(args.framework_sha, "framework_sha")
    customer_sha = require_sha(args.customer_sha, "customer_sha")
    root = Path(args.bundle_root)
    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")

    checks = [
        compare(
            "P01",
            rows_for_columns(
                spark,
                f"{catalog}.reference_silver.country",
                ["country_code", "country_name", "region", "active"],
            ),
            read_expected(root, "P01"),
        ),
        compare("P02", p02_rows(spark, catalog), read_expected(root, "P02")),
        compare(
            "P07",
            rows_for_columns(
                spark,
                f"{catalog}.crm_silver.customer_current",
                ["customer_id", "email", "status", "is_deleted", "row_version"],
            ),
            read_expected(root, "P07"),
        ),
        compare("P10", p10_rows(spark, catalog), read_expected(root, "P10")),
        compare(
            "P12",
            rows_for_columns(
                spark,
                f"{catalog}.commerce_silver.order_events",
                ["event_id", "order_id", "event_type", "event_time", "amount"],
            ),
            read_expected(root, "P12"),
        ),
    ]

    failed = [check for check in checks if check["status"] != "passed"]
    summary = {
        "level": "C3",
        "framework_sha": framework_sha,
        "customer_sha": customer_sha,
        "status": "failed" if failed else "passed",
        "patterns": checks,
    }
    write_verification_record(
        spark,
        catalog,
        framework_sha=framework_sha,
        customer_sha=customer_sha,
        status=summary["status"],
        summary=summary,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))

    if failed:
        names = ", ".join(check["pattern"] for check in failed)
        raise AssertionError(f"C3 semantic verification failed for: {names}")

    print("[SUCCESS] C3 actual outputs exactly match platform-neutral expected semantics")


if __name__ == "__main__":
    main()
