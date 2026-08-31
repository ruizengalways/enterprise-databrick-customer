from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def test_human_and_machine_documentation_are_separated() -> None:
    docs_files = [path for path in (ROOT / "docs").rglob("*") if path.is_file()]
    project_files = [path for path in (ROOT / "project").rglob("*") if path.is_file()]

    assert docs_files
    assert project_files
    assert all(path.suffix == ".md" for path in docs_files)
    assert all(path.suffix in {".yml", ".yaml", ".json"} for path in project_files)


def test_machine_context_has_required_read_order_and_repo_roles() -> None:
    context = load_yaml("project/context.yml")

    assert context["kind"] == "ecosystem_context"
    assert context["machine_read_order"][:4] == [
        "project/context.yml",
        "project/state.yml",
        "certification/framework-lock.yml",
        "certification/matrix.yml",
    ]

    repos = context["repositories"]
    assert set(repos) == {
        "data-engineering-cheetsheet",
        "enterprise-databrick-framework",
        "enterprise-databrick-customer",
        "enterprise-databrick-infra",
    }


def test_dynamic_state_tracks_subject_without_fabricating_new_evidence() -> None:
    state = load_yaml("project/state.yml")
    lock = load_yaml("certification/framework-lock.yml")
    matrix = load_yaml("certification/matrix.yml")

    framework_sha = lock["framework"]["ref"]
    assert state["certification_subject"]["framework_sha"] == framework_sha

    verified = state["latest_verified_local_package_run"]
    assert verified["status"] == "passed"
    assert len(verified["framework_sha"]) == 40
    if verified["framework_sha"] != framework_sha:
        assert verified["superseded_by_certification_subject"] is True

    assert state["runtime_certification"]["C3_real_databricks_runtime"] == "not_run"
    assert state["runtime_certification"]["C4_failure_recovery"] == "not_run"

    for pattern in ("P01", "P02", "P07", "P10", "P12"):
        assert matrix["patterns"][pattern]["package_integration"] == "passed"
        assert matrix["patterns"][pattern]["databricks_runtime"] == "not_run"


def test_repository_contract_matches_customer_role() -> None:
    repository = load_yaml("project/repository.yml")

    assert repository["repository"] == "ruizengalways/enterprise-databrick-customer"
    assert repository["role"] == "reference_customer"
    assert "certification_harness" in repository["owns"]
    assert "reusable_framework_internals" in repository["must_not_own"]
