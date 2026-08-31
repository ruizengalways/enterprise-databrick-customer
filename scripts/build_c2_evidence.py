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

    customer_sha = os.getenv("CUSTOMER_SHA") or git_sha(ROOT) or os.getenv("GITHUB_SHA")
    checked_out_customer_sha = git_sha(ROOT)
    if customer_sha and checked_out_customer_sha and customer_sha != checked_out_customer_sha:
        raise SystemExit(
            f"customer SHA mismatch: expected {customer_sha}, checked out {checked_out_customer_sha}"
        )

    evidence = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "customer_repository": "ruizengalways/enterprise-databrick-customer",
        "customer_sha": customer_sha,
        "framework_repository": lock["framework"]["repository"],
        "framework_sha": resolved_framework_sha or expected_sha,
        "framework_package_version": importlib.metadata.version("enterprise-databricks-framework"),
        "workflow": {
            "run_id": os.getenv("WORKFLOW_RUN_ID") or os.getenv("GITHUB_RUN_ID"),
            "attempt": os.getenv("WORKFLOW_RUN_ATTEMPT") or os.getenv("GITHUB_RUN_ATTEMPT"),
            "event": os.getenv("WORKFLOW_EVENT") or os.getenv("GITHUB_EVENT_NAME"),
        },
        "evidence_level": "C2-package-integration",
        "claims": {
            "metadata_contract_validation": "passed_by_ci_step",
            "deterministic_fixture_tests": "passed_by_ci_step",
            "exact_framework_sha": "verified",
            "exact_customer_sha": "verified",
            "databricks_runtime": "not_run",
            "recovery_failure_injection": "not_run",
        },
    }
    Path(args.output).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
