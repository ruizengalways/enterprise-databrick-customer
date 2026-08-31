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


def test_ready_patterns_have_customer_metadata() -> None:
    matrix = yaml.safe_load((ROOT / "certification/matrix.yml").read_text(encoding="utf-8"))
    ready = {pattern for pattern, status in matrix["patterns"].items() if status["metadata_contract"] == "ready"}
    metadata_text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "metadata/table_specs").glob("*.yml"))
    for pattern in ready:
        assert f"pattern_id: {pattern}" in metadata_text
