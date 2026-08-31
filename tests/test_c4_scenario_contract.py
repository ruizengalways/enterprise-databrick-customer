from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def test_c4_requires_c3_and_does_not_claim_recovery_before_execution() -> None:
    c4 = load_yaml("certification/c4-recovery.yml")
    state = load_yaml("project/state.yml")

    assert c4["status"] == "not_run"
    assert c4["precondition"]["c3_runtime_must_pass_first"] is True
    assert c4["claims"]["fixture_exists_is_not_recovery_evidence"] is True
    assert c4["claims"]["recovery_pass_requires_real_databricks_workspace"] is True
    assert state["runtime_certification"]["C4_failure_recovery"] == "not_run"


def test_existing_failure_fixtures_are_mapped_to_ready_scenarios() -> None:
    c4 = load_yaml("certification/c4-recovery.yml")
    scenarios = c4["scenarios"]

    ready = {
        name: scenario
        for name, scenario in scenarios.items()
        if scenario["status"] == "ready"
    }
    assert set(ready) == {
        "p07_bad_email_quarantine",
        "p10_redelivery_and_out_of_order",
        "p12_duplicate_and_unknown_event",
    }

    for scenario in ready.values():
        fixture = ROOT / scenario["fixture"]
        assert fixture.is_file(), fixture
        assert scenario["recovery_claim"] in {"none", "convergence_only"}


def test_true_repair_and_checkpoint_scenarios_remain_visible_planned_gaps() -> None:
    scenarios = load_yaml("certification/c4-recovery.yml")["scenarios"]

    assert scenarios["interrupted_runtime_resume"]["status"] == "planned"
    assert scenarios["bronze_replay_repair"]["status"] == "planned"
    assert scenarios["duplicate_snapshot_key_failure"]["status"] == "planned"
    assert "framework_repair_executor_not_released" in scenarios["bronze_replay_repair"]["blocked_by"]
