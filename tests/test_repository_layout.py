from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_layout() -> dict:
    return yaml.safe_load((ROOT / "project/layout.yml").read_text(encoding="utf-8"))


def test_top_level_directories_have_explicit_machine_owned_meaning() -> None:
    layout = load_layout()
    for directory in layout["root"]:
        assert (ROOT / directory).is_dir(), directory
    for directory in layout["forbidden_top_level_directories"]:
        assert not (ROOT / directory).exists(), directory


def test_databricks_workload_is_grouped_by_execution_role() -> None:
    layout = load_layout()
    expected = set(layout["required_databricks_subdirectories"])
    actual = {path.name for path in (ROOT / "databricks").iterdir() if path.is_dir()}
    assert expected <= actual
    assert (ROOT / "databricks/pipelines/reference_runtime.py").is_file()
    assert (ROOT / "databricks/tasks/seed_fixtures.py").is_file()
    assert (ROOT / "databricks/tasks/verify_outputs.py").is_file()
    assert (ROOT / "databricks/resources/c3-certification.yml").is_file()


def test_each_certified_pattern_is_self_contained_under_fixtures() -> None:
    layout = load_layout()
    for pattern, relative in layout["pattern_fixture_directories"].items():
        root = ROOT / relative
        assert root.is_dir(), pattern
        assert (root / "input").is_dir(), pattern
        assert (root / "expected").is_dir(), pattern
        if pattern in {"P07", "P10", "P12"}:
            assert (root / "failures").is_dir(), pattern
