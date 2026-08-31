from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CERTIFIED = {"P01", "P02", "P07", "P10", "P12"}


def load_yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def test_c3_bundle_pins_framework_artifact_and_current_serverless_environment() -> None:
    bundle = load_yaml("databricks.yml")
    resources = load_yaml("resources/c3.yml")["resources"]
    contract = load_yaml("certification/c3-runtime.yml")

    assert bundle["bundle"]["databricks_cli_version"] == ">= 1.3.0"
    assert contract["bundle"]["required_cli_version"] == ">= 1.3.0"
    assert contract["bundle"]["workflow_cli_version"] == "1.14.0"
    assert bundle["artifacts"]["framework"]["type"] == "whl"
    assert bundle["artifacts"]["framework"]["path"] == "./.framework"
    assert "c3" in bundle["targets"]

    pipeline = resources["pipelines"]["c3_reference_runtime"]
    assert pipeline["serverless"] is True
    assert pipeline["environment"]["environment_version"] == "4"
    assert any(".framework/dist/*.whl" in item for item in pipeline["environment"]["dependencies"])

    job = resources["jobs"]["c3_certification"]
    assert job["environments"][0]["spec"]["environment_version"] == "4"


def test_c3_job_enforces_seed_then_full_refresh_then_verifier() -> None:
    job = load_yaml("resources/c3.yml")["resources"]["jobs"]["c3_certification"]
    tasks = {task["task_key"]: task for task in job["tasks"]}

    assert set(tasks) == {"seed_fixtures", "run_reference_runtime", "verify_outputs"}
    assert tasks["run_reference_runtime"]["depends_on"] == [{"task_key": "seed_fixtures"}]
    assert tasks["run_reference_runtime"]["pipeline_task"]["full_refresh"] is True
    assert tasks["verify_outputs"]["depends_on"] == [{"task_key": "run_reference_runtime"}]
    assert tasks["seed_fixtures"]["environment_key"] == "default"
    assert tasks["verify_outputs"]["environment_key"] == "default"


def test_c3_machine_contract_and_matrix_do_not_claim_unrun_workspace_evidence() -> None:
    contract = load_yaml("certification/c3-runtime.yml")
    matrix = load_yaml("certification/matrix.yml")
    lock = load_yaml("certification/framework-lock.yml")

    assert contract["status"] == "not_run"
    assert set(contract["patterns"]) == CERTIFIED
    assert contract["claims"]["local_green_implies_c3"] is False
    assert contract["claims"]["pipeline_success_without_verifier_implies_c3"] is False
    assert lock["framework"]["ref"] == "20983d0960e82c8857f4b023f2331f6840149355"

    for pattern in CERTIFIED:
        assert matrix["patterns"][pattern]["databricks_runtime"] == "not_run"


def test_pipeline_registration_and_verifier_cover_exact_same_pattern_set() -> None:
    pipeline_source = (ROOT / "src/certification_pipeline/main.py").read_text(encoding="utf-8")
    verifier_source = (ROOT / "src/certification/verify_outputs.py").read_text(encoding="utf-8")

    for pattern in CERTIFIED:
        assert f'"{pattern}"' in pipeline_source
        assert f'"{pattern}"' in verifier_source

    assert "PatternRegistry(load_plugins=False)" in pipeline_source
    assert "snapshot_source_factory" in pipeline_source
    assert "c3_verification" in verifier_source
