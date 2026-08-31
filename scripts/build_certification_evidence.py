#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def git_sha(path: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="certification-evidence.json")
    args = parser.parse_args()

    lock = yaml.safe_load((ROOT / "certification/framework-lock.yml").read_text(encoding="utf-8"))
    framework_checkout = ROOT / ".framework"
    resolved_framework_sha = git_sha(framework_checkout) or os.getenv("FRAMEWORK_SHA")
    expected_sha = lock["framework"]["ref"]
    if resolved_framework_sha and resolved_framework_sha != expected_sha:
        raise SystemExit(f"framework SHA mismatch: expected {expected_sha}, got {resolved_framework_sha}")

    evidence = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "customer_repository": "ruizengalways/enterprise-databrick-customer",
        "customer_sha": os.getenv("GITHUB_SHA") or git_sha(ROOT),
        "framework_repository": lock["framework"]["repository"],
        "framework_sha": resolved_framework_sha or expected_sha,
        "framework_package_version": importlib.metadata.version("enterprise-databricks-framework"),
        "evidence_level": "C2-package-integration",
        "claims": {
            "metadata_contract_validation": "passed_by_ci_step",
            "deterministic_fixture_tests": "passed_by_ci_step",
            "databricks_runtime": "not_run",
            "recovery_failure_injection": "not_run",
        },
    }
    Path(args.output).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
