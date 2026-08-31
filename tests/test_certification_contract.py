from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_framework_lock_is_exact_sha() -> None:
    lock = yaml.safe_load((ROOT / "certification/framework-lock.yml").read_text(encoding="utf-8"))
    ref = lock["framework"]["ref"]
    assert len(ref) == 40
    assert all(char in "0123456789abcdef" for char in ref)


def test_matrix_keeps_all_patterns_visible() -> None:
    matrix = yaml.safe_load((ROOT / "certification/matrix.yml").read_text(encoding="utf-8"))
    assert set(matrix["patterns"]) == {f"P{i:02d}" for i in range(1, 15)}
    assert all("databricks_runtime" in status for status in matrix["patterns"].values())
    assert all("recovery" in status for status in matrix["patterns"].values())


def test_ready_or_passed_contract_patterns_have_customer_metadata() -> None:
    matrix = yaml.safe_load((ROOT / "certification/matrix.yml").read_text(encoding="utf-8"))
    represented = {
        pattern
        for pattern, status in matrix["patterns"].items()
        if status["metadata_contract"] in {"ready", "passed"}
    }
    metadata_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "metadata/table_specs").glob("*.yml")
    )
    for pattern in represented:
        assert f"pattern_id: {pattern}" in metadata_text


def test_passed_c2_matrix_points_to_matching_evidence_record() -> None:
    matrix = yaml.safe_load((ROOT / "certification/matrix.yml").read_text(encoding="utf-8"))
    latest = matrix["latest_local_evidence"]
    evidence = yaml.safe_load((ROOT / latest["record"]).read_text(encoding="utf-8"))

    assert evidence["status"] == "passed"
    assert evidence["evidence_level"] == "C2-package-integration"
    assert evidence["framework"]["sha"] == latest["framework_sha"]
    assert evidence["customer"]["sha"] == latest["customer_sha"]
    assert evidence["workflow"]["run_id"] == latest["workflow_run_id"]

    passed = {
        pattern
        for pattern, status in matrix["patterns"].items()
        if status.get("package_integration") == "passed"
    }
    assert passed == set(evidence["scope"]["passed_patterns"])
    assert all(matrix["patterns"][pattern]["databricks_runtime"] == "not_run" for pattern in passed)
    assert all(matrix["patterns"][pattern]["recovery"] == "not_run" for pattern in passed)
