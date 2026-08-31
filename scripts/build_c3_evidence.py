from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework-sha", required=True)
    parser.add_argument("--customer-sha", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--workflow-run-attempt", required=True)
    parser.add_argument("--bundle-summary", type=Path, required=True)
    parser.add_argument("--bundle-run", type=Path, required=True)
    parser.add_argument("--cli-version", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def require_sha(value: str, label: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError(f"{label} must be an exact Git SHA")
    return value


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    args = parse_args()
    evidence = {
        "schema_version": 1,
        "certification_level": "C3",
        "status": "passed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "customer_sha": require_sha(args.customer_sha, "customer_sha"),
        "framework_sha": require_sha(args.framework_sha, "framework_sha"),
        "workflow_run_id": str(args.workflow_run_id),
        "workflow_run_attempt": str(args.workflow_run_attempt),
        "bundle_target": "c3",
        "verifier_success": True,
        "claim_scope": "real_databricks_runtime_semantics",
        "recovery_certified": False,
        "bundle_summary": load_json(args.bundle_summary),
        "bundle_run_result": load_json(args.bundle_run),
        "databricks_cli": load_json(args.cli_version),
    }
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote C3 evidence to {args.output}")


if __name__ == "__main__":
    main()
