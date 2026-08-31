from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def test_certification_workflows_use_machine_pinned_action_shas() -> None:
    contract = load_yaml("certification/c3-runtime.yml")
    pins = contract["workflow_supply_chain"]
    c3 = (ROOT / ".github/workflows/certify-databricks.yml").read_text(encoding="utf-8")
    local = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")

    checkout = f"actions/checkout@{pins['actions_checkout_sha']}"
    setup_python = f"actions/setup-python@{pins['actions_setup_python_sha']}"
    upload = f"actions/upload-artifact@{pins['actions_upload_artifact_sha']}"
    setup_cli = f"databricks/setup-cli@{pins['databricks_setup_cli_sha']}"

    for workflow in (c3, local):
        assert checkout in workflow
        assert setup_python in workflow
        assert upload in workflow
        assert "actions/checkout@v" not in workflow
        assert "actions/setup-python@v" not in workflow
        assert "actions/upload-artifact@v" not in workflow

    assert setup_cli in c3
    assert "databricks/setup-cli@main" not in c3
    assert "databricks/setup-cli@v" not in c3


def test_real_c3_workflow_is_manual_main_only_and_oidc_only() -> None:
    c3 = (ROOT / ".github/workflows/certify-databricks.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch:" in c3
    assert "if: github.ref == 'refs/heads/main'" in c3
    assert "id-token: write" in c3
    assert "DATABRICKS_AUTH_TYPE: github-oidc" in c3
    assert "DATABRICKS_TOKEN" not in c3
    assert "bundle plan -t c3 -o json" in c3
    assert "bundle deploy -t c3 --plan" in c3
