from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--expected-customer-sha")
    parser.add_argument("--expected-framework-sha")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise TypeError(f"{path}: expected JSON object")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    args = parse_args()
    evidence = load_json(args.evidence)
    schema = load_json(ROOT / "certification/schemas/c3-evidence.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(evidence), key=lambda error: list(error.path))
    if errors:
        messages = [f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}" for error in errors]
        raise ValueError("invalid C3 evidence:\n" + "\n".join(messages))

    with (ROOT / "certification/framework-lock.yml").open(encoding="utf-8") as handle:
        lock = yaml.safe_load(handle)
    locked_framework_sha = lock["framework"]["ref"]
    if evidence["framework_sha"] != locked_framework_sha:
        raise ValueError(
            "C3 evidence framework SHA does not match certification/framework-lock.yml"
        )

    plan_path = ROOT / evidence["reconciliation_plan"]["path"]
    actual_plan_digest = sha256(plan_path)
    if evidence["reconciliation_plan"]["sha256"] != actual_plan_digest:
        raise ValueError("C3 evidence reconciliation plan digest does not match reviewed source")

    if args.expected_framework_sha and evidence["framework_sha"] != args.expected_framework_sha:
        raise ValueError("C3 evidence framework SHA does not match workflow expectation")
    if args.expected_customer_sha and evidence["customer_sha"] != args.expected_customer_sha:
        raise ValueError("C3 evidence customer SHA does not match workflow expectation")

    print(
        "valid C3 evidence: "
        f"customer={evidence['customer_sha']} framework={evidence['framework_sha']} "
        f"reconciliation_plan={evidence['reconciliation_plan']['sha256']}"
    )


if __name__ == "__main__":
    main()
