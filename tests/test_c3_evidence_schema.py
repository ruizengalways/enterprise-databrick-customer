from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def valid_evidence() -> dict:
    return {
        "schema_version": 1,
        "certification_level": "C3",
        "status": "passed",
        "generated_at": "2026-08-31T11:00:00+00:00",
        "customer_sha": "a" * 40,
        "framework_sha": "b" * 40,
        "workflow_run_id": "123",
        "workflow_run_attempt": "1",
        "bundle_target": "c3",
        "verifier_success": True,
        "claim_scope": "real_databricks_runtime_semantics",
        "recovery_certified": False,
        "bundle_summary": {},
        "bundle_run_result": {},
        "databricks_cli": {},
    }


def validator() -> Draft202012Validator:
    schema = json.loads(
        (ROOT / "certification/schemas/c3-evidence.schema.json").read_text(encoding="utf-8")
    )
    return Draft202012Validator(schema)


def test_valid_c3_evidence_shape_is_accepted() -> None:
    validator().validate(valid_evidence())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "not_run"),
        ("verifier_success", False),
        ("recovery_certified", True),
        ("bundle_target", "prod"),
        ("framework_sha", "not-a-sha"),
    ],
)
def test_c3_schema_rejects_overclaims_or_ambiguous_identity(field: str, value: object) -> None:
    evidence = deepcopy(valid_evidence())
    evidence[field] = value
    with pytest.raises(Exception):
        validator().validate(evidence)
