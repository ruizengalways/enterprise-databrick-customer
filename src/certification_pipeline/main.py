from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from edp_framework.metadata.loader import load_table_specs
from edp_framework.patterns.contracts import RuntimeContext
from edp_framework.patterns.registry import PatternRegistry
from pyspark import pipelines as dp
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col

CERTIFIED_PATTERNS = {"P01", "P02", "P07", "P10", "P12"}

spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
catalog = spark.conf.get("edp.catalog")
bundle_root = Path(spark.conf.get("edp.bundle_root"))
specs = load_table_specs(bundle_root / "metadata/table_specs")
registry = PatternRegistry(load_plugins=False)


def snapshot_source_factory(spec: Any) -> Callable[[Any], tuple[DataFrame, int] | None]:
    configured = spec.capture.options.get("reference_snapshot_versions")
    if not isinstance(configured, list) or not configured or not all(
        isinstance(value, int) for value in configured
    ):
        raise ValueError(
            f"{spec.dataset_id}: C3 fixture adapter requires integer reference_snapshot_versions"
        )
    versions = sorted(configured)
    bronze = f"{catalog}.{spec.bronze.table}"

    def next_snapshot(latest_snapshot_version: Any) -> tuple[DataFrame, int] | None:
        latest = None if latest_snapshot_version is None else int(latest_snapshot_version)
        next_version = next((version for version in versions if latest is None or version > latest), None)
        if next_version is None:
            return None
        frame = spark.read.table(bronze).where(col("_snapshot_id") == next_version).drop(
            "_snapshot_id"
        )
        return frame, next_version

    return next_snapshot


def canonical_order_event(frame: DataFrame) -> DataFrame:
    return frame.select("event_id", "order_id", "event_type", "event_time", "amount")


seen: set[str] = set()
for spec in specs:
    if not spec.enabled:
        continue
    if spec.pattern_id not in CERTIFIED_PATTERNS:
        raise ValueError(
            f"C3 bundle contains unsupported reference pattern {spec.pattern_id} for {spec.dataset_id}"
        )

    options: dict[str, Any] = {}
    if spec.pattern_id == "P02":
        options["snapshot_source"] = snapshot_source_factory(spec)
    if spec.pattern_id == "P12":
        options["transform"] = canonical_order_event

    context = RuntimeContext(
        spark=spark,
        pipelines=dp,
        environment="c3",
        catalog=catalog,
        options=options,
    )
    registry.build_runtime(spec, context)
    seen.add(spec.pattern_id)

if seen != CERTIFIED_PATTERNS:
    missing = sorted(CERTIFIED_PATTERNS - seen)
    unexpected = sorted(seen - CERTIFIED_PATTERNS)
    raise ValueError(f"C3 pattern registration mismatch: missing={missing}, unexpected={unexpected}")
