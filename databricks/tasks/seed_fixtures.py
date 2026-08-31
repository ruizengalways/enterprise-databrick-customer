from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from pyspark.sql import SparkSession

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

SCHEMAS = (
    "customer_source",
    "reference_bronze",
    "reference_silver",
    "legacy_bronze",
    "legacy_silver",
    "crm_bronze",
    "crm_silver",
    "crm_quarantine",
    "sales_bronze",
    "sales_silver",
    "sales_quarantine",
    "commerce_bronze",
    "commerce_silver",
    "commerce_quarantine",
    "certification_control",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--bundle-root", required=True)
    return parser.parse_args()


def require_identifier(value: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"unsafe Unity Catalog identifier: {value!r}")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"expected boolean, got {value!r}")


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def write_table(spark: SparkSession, table: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to seed empty certification table: {table}")
    spark.createDataFrame(rows).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
        table
    )
    count = spark.table(table).count()
    if count != len(rows):
        raise AssertionError(f"seed verification failed for {table}: expected {len(rows)}, got {count}")
    print(f"[SEEDED] {table}: {count} rows")


def country_rows(root: Path) -> list[dict[str, Any]]:
    rows = read_csv(root / "fixtures/p01_full_snapshot/input/country_current.csv")
    return [
        {
            "country_code": row["country_code"],
            "country_name": row["country_name"],
            "region": row["region"],
            "active": parse_bool(row["active"]),
        }
        for row in rows
    ]


def legacy_snapshot_rows(root: Path) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for snapshot_id in (1, 2, 3):
        path = root / f"fixtures/p02_snapshot_history/input/snapshot_{snapshot_id:03d}.csv"
        for row in read_csv(path):
            output.append(
                {
                    "customer_id": row["customer_id"],
                    "name": row["name"],
                    "segment": row["segment"],
                    "status": row["status"],
                    "_snapshot_id": snapshot_id,
                }
            )
    return output


def crm_observation_rows(root: Path) -> list[dict[str, Any]]:
    rows = read_csv(root / "fixtures/p07_watermark_soft_delete/input/observations.csv")
    return [
        {
            "customer_id": row["customer_id"],
            "email": row["email"] or None,
            "status": row["status"],
            "is_deleted": parse_bool(row["is_deleted"]),
            "row_version": int(row["row_version"]),
            "_ingest_run_id": row["_ingest_run_id"],
        }
        for row in rows
    ]


def sales_cdc_rows(root: Path) -> list[dict[str, Any]]:
    rows = read_jsonl(root / "fixtures/p10_full_cdc/input/debezium_normalized.jsonl")
    for row in rows:
        row["source_lsn"] = int(row["source_lsn"])
        row["source_event_sequence"] = int(row["source_event_sequence"])
        row["_kafka_partition"] = int(row["_kafka_partition"])
        row["_kafka_offset"] = int(row["_kafka_offset"])
        row["updated_at"] = parse_timestamp(str(row["updated_at"]))
    return rows


def order_event_rows(root: Path) -> list[dict[str, Any]]:
    rows = read_jsonl(root / "fixtures/p12_business_events/input/events.jsonl")
    for row in rows:
        row["event_time"] = parse_timestamp(str(row["event_time"]))
        row["amount"] = float(row["amount"])
        row["_kafka_partition"] = int(row["_kafka_partition"])
        row["_kafka_offset"] = int(row["_kafka_offset"])
    return rows


def main() -> None:
    args = parse_args()
    catalog = require_identifier(args.catalog)
    root = Path(args.bundle_root)
    spark = SparkSession.builder.getOrCreate()

    for schema in SCHEMAS:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")

    write_table(spark, f"{catalog}.customer_source.country_snapshot", country_rows(root))

    # P02's retained snapshot-history Bronze belongs to the workload/capture adapter.
    write_table(
        spark,
        f"{catalog}.legacy_bronze.customer_snapshot",
        legacy_snapshot_rows(root),
    )
    write_table(
        spark,
        f"{catalog}.customer_source.crm_customer_observations",
        crm_observation_rows(root),
    )
    write_table(
        spark,
        f"{catalog}.customer_source.sales_customer_cdc",
        sales_cdc_rows(root),
    )
    write_table(
        spark,
        f"{catalog}.customer_source.order_events",
        order_event_rows(root),
    )

    print("[SUCCESS] deterministic C3 fixtures seeded")


if __name__ == "__main__":
    main()
