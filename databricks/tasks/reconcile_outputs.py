from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from edp_framework.metadata.loader import load_table_specs
from edp_framework.metadata.models import DQAction, TableSpec
from edp_framework.quality import rules_for_action, valid_expression
from edp_framework.reconciliation import (
    ReconciliationContext,
    SparkMeasureProvider,
    evaluate_reconciliation,
    persist_reconciliation_report,
)
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql.functions import col, row_number
from pyspark.sql.functions import max as spark_max

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SHA = re.compile(r"^[0-9a-f]{40}$")
PLAN_PATH = "certification/reconciliation-runtime.yml"


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
    if not _SHA.fullmatch(value):
        raise ValueError(f"{label} must be an exact 40-character Git SHA")
    return value


def load_plan(root: Path) -> dict[str, Any]:
    plan = yaml.safe_load((root / PLAN_PATH).read_text(encoding="utf-8"))
    if plan["status"] != "not_run":
        raise ValueError("static reconciliation plan must remain not_run until real C3 evidence exists")
    if plan["cutoff_consistency_required"] is not True:
        raise ValueError("C3 reconciliation plan must require cutoff consistency")
    return plan


def validate_plan(specs: list[TableSpec], plan: dict[str, Any]) -> None:
    planned = plan["patterns"]
    enabled = {spec.pattern_id: spec for spec in specs if spec.enabled}
    if set(planned) != set(enabled):
        raise ValueError(
            f"reconciliation plan pattern mismatch: planned={sorted(planned)}, enabled={sorted(enabled)}"
        )

    for pattern, spec in enabled.items():
        entry = planned[pattern]
        if entry["dataset_id"] != spec.dataset_id:
            raise ValueError(
                f"{pattern}: reconciliation plan dataset {entry['dataset_id']!r} does not match "
                f"metadata dataset {spec.dataset_id!r}"
            )

        declared = {rule.name: rule.kind for rule in spec.reconciliation.rules}
        grouped_names = [name for names in entry["groups"].values() for name in names]
        gaps = entry.get("declared_gaps", [])
        gap_names = [gap["rule_name"] for gap in gaps]
        accounted = grouped_names + gap_names
        if len(accounted) != len(set(accounted)):
            raise ValueError(f"{pattern}: reconciliation plan accounts for a rule more than once")
        if set(accounted) != set(declared):
            missing = sorted(set(declared) - set(accounted))
            unexpected = sorted(set(accounted) - set(declared))
            raise ValueError(
                f"{pattern}: every declared reconciliation rule must be accounted for; "
                f"missing={missing}, unexpected={unexpected}"
            )
        for gap in gaps:
            rule_name = gap["rule_name"]
            if declared[rule_name] != gap["rule_kind"]:
                raise ValueError(
                    f"{pattern}: declared gap {rule_name!r} kind {gap['rule_kind']!r} does not "
                    f"match metadata kind {declared[rule_name]!r}"
                )
            if not str(gap.get("reason", "")).strip():
                raise ValueError(f"{pattern}: declared reconciliation gap {rule_name!r} needs a reason")


def subset_spec(spec: TableSpec, rule_names: list[str]) -> TableSpec:
    wanted = set(rule_names)
    rules = [rule for rule in spec.reconciliation.rules if rule.name in wanted]
    if {rule.name for rule in rules} != wanted:
        raise ValueError(f"{spec.pattern_id}: reconciliation group references an unknown rule")
    return spec.model_copy(
        update={"reconciliation": spec.reconciliation.model_copy(update={"rules": rules})}
    )


def temp_relation(frame: DataFrame, name: str) -> str:
    require_identifier(name)
    frame.createOrReplaceTempView(name)
    return name


def max_integer(frame: DataFrame, column: str) -> int:
    row = frame.agg(spark_max(col(column)).alias("value")).first()
    if row is None or row["value"] is None:
        raise ValueError(f"cannot determine reconciliation cutoff from empty column {column!r}")
    return int(row["value"])


def max_sequence(frame: DataFrame, columns: list[str]) -> str:
    if not columns:
        raise ValueError("source-position reconciliation requires ordering columns")
    row = frame.orderBy(*[col(name).desc() for name in columns]).select(*columns).first()
    if row is None:
        raise ValueError("cannot determine source position from an empty relation")
    return json.dumps({name: row[name] for name in columns}, sort_keys=True, separators=(",", ":"))


def kafka_partition_offsets(frame: DataFrame) -> str:
    rows = (
        frame.groupBy("_kafka_partition")
        .agg(spark_max(col("_kafka_offset")).alias("_max_offset"))
        .collect()
    )
    if not rows:
        raise ValueError("cannot determine Kafka cutoff from an empty relation")
    offsets = {str(int(row["_kafka_partition"])): int(row["_max_offset"]) for row in rows}
    return json.dumps(offsets, sort_keys=True, separators=(",", ":"))


def quarantine_valid_frame(spec: TableSpec, frame: DataFrame) -> DataFrame:
    quarantine_rules = rules_for_action(spec.quality.rules, DQAction.QUARANTINE)
    expression = valid_expression(quarantine_rules)
    return frame.filter(expression) if expression else frame


def latest_state(frame: DataFrame, keys: list[str], order_columns: list[str]) -> DataFrame:
    window = Window.partitionBy(*keys).orderBy(*[col(name).desc() for name in order_columns])
    return frame.withColumn("_c3_reconciliation_rank", row_number().over(window)).where(
        col("_c3_reconciliation_rank") == 1
    ).drop("_c3_reconciliation_rank")


def run_group(
    spark: SparkSession,
    catalog: str,
    spec: TableSpec,
    *,
    group_name: str,
    rule_names: list[str],
    source_relation: str,
    target_relation: str,
    cutoff_type: str,
    cutoff_value: str,
    observed_target_position: str | None = None,
) -> dict[str, Any]:
    group_spec = subset_spec(spec, rule_names)
    report = evaluate_reconciliation(
        group_spec,
        ReconciliationContext(
            cutoff_type=cutoff_type,
            cutoff_value=cutoff_value,
            source_relation=source_relation,
            target_relation=target_relation,
            business_keys=tuple(spec.identity.business_keys),
            observed_target_position=observed_target_position,
        ),
        SparkMeasureProvider(spark),
    )
    persist_reconciliation_report(spark, catalog, report, ensure_schema=True)
    return {
        "group": group_name,
        "status": report.status,
        "cutoff_type": cutoff_type,
        "cutoff_value": cutoff_value,
        "reconciliation_run_id": report.reconciliation_run_id,
        "rules": [
            {
                "name": result.rule_name,
                "kind": result.rule_kind,
                "status": "passed" if result.passed else "failed",
                "expected": result.expected_value,
                "actual": result.actual_value,
                "variance": result.variance,
            }
            for result in report.results
        ],
    }


def run_p01(
    spark: SparkSession,
    catalog: str,
    spec: TableSpec,
    groups: dict[str, list[str]],
) -> list[dict[str, Any]]:
    return [
        run_group(
            spark,
            catalog,
            spec,
            group_name="current_snapshot",
            rule_names=groups["current_snapshot"],
            source_relation=f"{catalog}.customer_source.country_snapshot",
            target_relation=f"{catalog}.reference_silver.country",
            cutoff_type="snapshot_id",
            cutoff_value="c3-country-fixture-v1",
        )
    ]


def run_p02(
    spark: SparkSession,
    catalog: str,
    spec: TableSpec,
    groups: dict[str, list[str]],
) -> list[dict[str, Any]]:
    source_history = spark.table(f"{catalog}.legacy_bronze.customer_snapshot")
    latest_snapshot = max_integer(source_history, "_snapshot_id")
    source_current = temp_relation(
        source_history.where(col("_snapshot_id") == latest_snapshot),
        "c3_recon_p02_source_current",
    )
    target_history_frame = spark.table(f"{catalog}.legacy_silver.customer_history")
    target_current = temp_relation(
        target_history_frame.where(col("__END_AT").isNull()),
        "c3_recon_p02_target_current",
    )
    target_history = f"{catalog}.legacy_silver.customer_history"
    cutoff = str(latest_snapshot)
    return [
        run_group(
            spark,
            catalog,
            spec,
            group_name="current_snapshot",
            rule_names=groups["current_snapshot"],
            source_relation=source_current,
            target_relation=target_current,
            cutoff_type="snapshot_id",
            cutoff_value=cutoff,
        ),
        run_group(
            spark,
            catalog,
            spec,
            group_name="history_integrity",
            rule_names=groups["history_integrity"],
            source_relation=source_current,
            target_relation=target_history,
            cutoff_type="snapshot_id",
            cutoff_value=cutoff,
        ),
    ]


def run_p07(
    spark: SparkSession,
    catalog: str,
    spec: TableSpec,
    groups: dict[str, list[str]],
) -> list[dict[str, Any]]:
    source_frame = spark.table(f"{catalog}.customer_source.crm_customer_observations")
    cutoff = max_integer(source_frame, "row_version")
    valid = quarantine_valid_frame(spec, source_frame.where(col("row_version") <= cutoff))
    source_current = temp_relation(
        latest_state(valid, list(spec.identity.business_keys), ["row_version", "_ingest_run_id"]),
        "c3_recon_p07_source_current",
    )
    observed = str(
        max_integer(spark.table(f"{catalog}.crm_bronze.customer_observation"), "row_version")
    )
    return [
        run_group(
            spark,
            catalog,
            spec,
            group_name="current_state",
            rule_names=groups["current_state"],
            source_relation=source_current,
            target_relation=f"{catalog}.crm_silver.customer_current",
            cutoff_type="rowversion",
            cutoff_value=str(cutoff),
            observed_target_position=observed,
        )
    ]


def run_p10(
    spark: SparkSession,
    catalog: str,
    spec: TableSpec,
    groups: dict[str, list[str]],
) -> list[dict[str, Any]]:
    source = spark.table(f"{catalog}.customer_source.sales_customer_cdc")
    bronze = spark.table(f"{catalog}.sales_bronze.customer_cdc")
    ordering = list(spec.ordering.columns) if spec.ordering is not None else []
    cutoff = max_sequence(source, ordering)
    observed = max_sequence(bronze, ordering)
    target = f"{catalog}.sales_silver.customer_history"
    return [
        run_group(
            spark,
            catalog,
            spec,
            group_name="consumed_position",
            rule_names=groups["consumed_position"],
            source_relation=f"{catalog}.customer_source.sales_customer_cdc",
            target_relation=target,
            cutoff_type="source_sequence",
            cutoff_value=cutoff,
            observed_target_position=observed,
        ),
        run_group(
            spark,
            catalog,
            spec,
            group_name="history_integrity",
            rule_names=groups["history_integrity"],
            source_relation=f"{catalog}.customer_source.sales_customer_cdc",
            target_relation=target,
            cutoff_type="source_sequence",
            cutoff_value=cutoff,
        ),
    ]


def run_p12(
    spark: SparkSession,
    catalog: str,
    spec: TableSpec,
    groups: dict[str, list[str]],
) -> list[dict[str, Any]]:
    source_raw = spark.table(f"{catalog}.customer_source.order_events")
    source_valid = quarantine_valid_frame(spec, source_raw)
    source_comparable = temp_relation(
        source_valid.dropDuplicates(spec.identity.event_identity_columns),
        "c3_recon_p12_source_canonical",
    )
    cutoff = kafka_partition_offsets(source_raw)
    observed = kafka_partition_offsets(spark.table(f"{catalog}.commerce_bronze.order_events"))
    return [
        run_group(
            spark,
            catalog,
            spec,
            group_name="canonical_events",
            rule_names=groups["canonical_events"],
            source_relation=source_comparable,
            target_relation=f"{catalog}.commerce_silver.order_events",
            cutoff_type="kafka_partition_offsets",
            cutoff_value=cutoff,
            observed_target_position=observed,
        )
    ]


RUNNERS = {
    "P01": run_p01,
    "P02": run_p02,
    "P07": run_p07,
    "P10": run_p10,
    "P12": run_p12,
}


def write_certification_summary(
    spark: SparkSession,
    catalog: str,
    *,
    framework_sha: str,
    customer_sha: str,
    status: str,
    summary: dict[str, Any],
) -> None:
    spark.createDataFrame(
        [
            {
                "recorded_at": datetime.now(timezone.utc),
                "certification_level": "C3",
                "framework_sha": framework_sha,
                "customer_sha": customer_sha,
                "status": status,
                "summary_json": json.dumps(summary, sort_keys=True),
            }
        ]
    ).write.mode("append").saveAsTable(f"{catalog}.certification_control.c3_reconciliation")


def main() -> None:
    args = parse_args()
    catalog = require_identifier(args.catalog)
    framework_sha = require_sha(args.framework_sha, "framework_sha")
    customer_sha = require_sha(args.customer_sha, "customer_sha")
    root = Path(args.bundle_root)
    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")

    specs = [spec for spec in load_table_specs(root / "metadata/table_specs") if spec.enabled]
    plan = load_plan(root)
    validate_plan(specs, plan)

    pattern_summaries: list[dict[str, Any]] = []
    failed_groups: list[str] = []
    declared_gaps: list[dict[str, Any]] = []

    by_pattern = {spec.pattern_id: spec for spec in specs}
    for pattern in sorted(plan["patterns"]):
        spec = by_pattern[pattern]
        entry = plan["patterns"][pattern]
        groups = RUNNERS[pattern](spark, catalog, spec, entry["groups"])
        for group in groups:
            if group["status"] != "passed":
                failed_groups.append(f"{pattern}:{group['group']}")
        gaps = [
            {
                "rule_name": gap["rule_name"],
                "rule_kind": gap["rule_kind"],
                "status": "blocked_declared",
                "reason": gap["reason"],
            }
            for gap in entry.get("declared_gaps", [])
        ]
        declared_gaps.extend({"pattern": pattern, **gap} for gap in gaps)
        pattern_summaries.append(
            {
                "pattern": pattern,
                "dataset_id": spec.dataset_id,
                "status": "failed"
                if any(group["status"] != "passed" for group in groups)
                else ("passed_with_declared_gaps" if gaps else "passed"),
                "groups": groups,
                "declared_gaps": gaps,
            }
        )

    status = "failed" if failed_groups else (
        "passed_with_declared_gaps" if declared_gaps else "passed"
    )
    summary = {
        "level": "C3-reconciliation",
        "framework_sha": framework_sha,
        "customer_sha": customer_sha,
        "status": status,
        "patterns": pattern_summaries,
        "declared_gaps": declared_gaps,
    }
    write_certification_summary(
        spark,
        catalog,
        framework_sha=framework_sha,
        customer_sha=customer_sha,
        status=status,
        summary=summary,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))

    if failed_groups:
        raise AssertionError(
            "C3 reconciliation failed for executable groups: " + ", ".join(failed_groups)
        )

    print(f"[SUCCESS] C3 reconciliation completed with status={status}")


if __name__ == "__main__":
    main()
