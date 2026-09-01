from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CERTIFIED = {"P01", "P02", "P07", "P10", "P12"}
EXACT_SHA = re.compile(r"^[0-9a-f]{40}$")


def load_yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def test_c3_bundle_pins_framework_artifact_and_current_serverless_environment() -> None:
    bundle = load_yaml("databricks.yml")
    resources = load_yaml("databricks/resources/c3-certification.yml")["resources"]

    assert bundle["bundle"]["databricks_cli_version"] == ">= 1.3.0"
    assert bundle["include"] == ["databricks/resources/*.yml"]
    assert bundle["artifacts"]["framework"]["type"] == "whl"
    assert bundle["artifacts"]["framework"]["path"] == "./.framework"
    assert "fixtures/**" in bundle["sync"]["include"]
    assert "c3" in bundle["targets"]

    pipeline = resources["pipelines"]["c3_reference_runtime"]
    assert pipeline["serverless"] is True
    assert pipeline["environment"]["environment_version"] == "4"
    assert any(".framework/dist/*.whl" in item for item in pipeline["environment"]["dependencies"])

    job = resources["jobs"]["c3_certification"]
    default_environment = job["environments"][0]
    assert default_environment["spec"]["environment_version"] == "4"
    assert any(
        ".framework/dist/*.whl" in item
        for item in default_environment["spec"]["dependencies"]
    )


def test_c3_job_enforces_seed_runtime_reconcile_verifier_chain() -> None:
    job = load_yaml("databricks/resources/c3-certification.yml")["resources"]["jobs"][
        "c3_certification"
    ]
    tasks = {task["task_key"]: task for task in job["tasks"]}

    assert set(tasks) == {
        "seed_fixtures",
        "run_reference_runtime",
        "reconcile_outputs",
        "verify_outputs",
    }
    assert tasks["run_reference_runtime"]["depends_on"] == [{"task_key": "seed_fixtures"}]
    assert tasks["run_reference_runtime"]["pipeline_task"]["full_refresh"] is True
    assert tasks["reconcile_outputs"]["depends_on"] == [{"task_key": "run_reference_runtime"}]
    assert tasks["verify_outputs"]["depends_on"] == [{"task_key": "reconcile_outputs"}]
    assert tasks["seed_fixtures"]["environment_key"] == "default"
    assert tasks["reconcile_outputs"]["environment_key"] == "default"
    assert tasks["verify_outputs"]["environment_key"] == "default"


def test_c3_machine_contract_and_matrix_do_not_claim_unrun_workspace_evidence() -> None:
    contract = load_yaml("certification/c3-runtime.yml")
    matrix = load_yaml("certification/matrix.yml")
    lock = load_yaml("certification/framework-lock.yml")

    assert contract["status"] == "not_run"
    assert set(contract["patterns"]) == CERTIFIED
    assert contract["execution"]["stages"] == [
        "seed_fixtures",
        "run_reference_runtime",
        "reconcile_outputs",
        "verify_outputs",
    ]
    assert contract["claims"]["local_green_implies_c3"] is False
    assert contract["claims"]["pipeline_success_without_verifier_implies_c3"] is False
    assert contract["claims"]["reconciliation_task_success_without_verifier_implies_c3"] is False
    assert contract["claims"]["declared_reconciliation_gap_is_not_reconciliation_pass"] is True
    assert contract["framework_subject"]["source"] == "certification/framework-lock.yml"
    assert contract["framework_subject"]["require_exact_sha"] is True
    assert lock["certification_policy"]["require_exact_framework_sha"] is True
    assert EXACT_SHA.fullmatch(lock["framework"]["ref"])

    for pattern in CERTIFIED:
        assert matrix["patterns"][pattern]["databricks_runtime"] == "not_run"
    assert matrix["capabilities"]["reconciliation_runtime"] == "not_run"


def test_reconciliation_plan_accounts_for_every_declared_rule_exactly_once() -> None:
    plan = load_yaml("certification/reconciliation-runtime.yml")
    assert plan["status"] == "not_run"
    assert plan["cutoff_consistency_required"] is True
    assert set(plan["patterns"]) == CERTIFIED

    specs = {}
    for path in (ROOT / "metadata/table_specs").glob("*.yml"):
        spec = load_yaml(str(path.relative_to(ROOT)))
        specs[spec["pattern_id"]] = spec

    for pattern in CERTIFIED:
        spec = specs[pattern]
        entry = plan["patterns"][pattern]
        assert entry["dataset_id"] == spec["dataset_id"]
        declared = {rule["name"]: rule["kind"] for rule in spec["reconciliation"]["rules"]}
        grouped = [rule for rules in entry["groups"].values() for rule in rules]
        gaps = entry.get("declared_gaps", [])
        gap_names = [gap["rule_name"] for gap in gaps]
        accounted = grouped + gap_names
        assert len(accounted) == len(set(accounted))
        assert set(accounted) == set(declared)
        for gap in gaps:
            assert declared[gap["rule_name"]] == gap["rule_kind"]
            assert gap["reason"].strip()

    p10 = plan["patterns"]["P10"]
    assert p10["groups"]["application_feed_parity"] == [
        "application_feed_rows",
        "application_feed_identity_count",
        "application_feed_identity_presence",
        "operation_counts",
    ]
    assert p10["declared_gaps"] == []

    p10_spec = specs["P10"]
    p10_rules = {rule["name"]: rule for rule in p10_spec["reconciliation"]["rules"]}
    identity = ["_kafka_topic", "_kafka_partition", "_kafka_offset"]
    assert p10_rules["application_feed_rows"]["kind"] == "row_count"
    assert p10_rules["application_feed_identity_count"]["kind"] == "key_count"
    assert p10_rules["application_feed_identity_count"]["options"]["keys"] == identity
    assert p10_rules["application_feed_identity_presence"]["kind"] == "pk_presence"
    assert p10_rules["application_feed_identity_presence"]["options"]["keys"] == identity
    assert p10_rules["operation_counts"]["options"]["operation_column"] == "_operation"


def test_pipeline_reconciliation_and_verifier_cover_exact_same_pattern_set() -> None:
    pipeline_source = (ROOT / "databricks/pipelines/reference_runtime.py").read_text(encoding="utf-8")
    reconcile_source = (ROOT / "databricks/tasks/reconcile_outputs.py").read_text(encoding="utf-8")
    verifier_source = (ROOT / "databricks/tasks/verify_outputs.py").read_text(encoding="utf-8")
    seed_source = (ROOT / "databricks/tasks/seed_fixtures.py").read_text(encoding="utf-8")

    for pattern in CERTIFIED:
        assert f'"{pattern}"' in pipeline_source
        assert f'"{pattern}"' in reconcile_source
        assert f'"{pattern}"' in verifier_source

    assert "PatternRegistry(load_plugins=False)" in pipeline_source
    assert "snapshot_source_factory" in pipeline_source
    assert "fixtures/p01_full_snapshot" in seed_source
    assert "persist_reconciliation_report" in reconcile_source
    assert "every declared reconciliation rule must be accounted for" in reconcile_source
    assert "application_feed_parity" in reconcile_source
    assert "c3_reconciliation" in reconcile_source
    assert "read_reconciliation_summary" in verifier_source
    assert "c3_verification" in verifier_source
