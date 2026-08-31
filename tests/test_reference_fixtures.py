from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: str) -> list[dict[str, object]]:
    with (ROOT / path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def test_p01_country_snapshot_matches_expected_current_state() -> None:
    actual = sorted(read_csv("data/reference/country/current.csv"), key=lambda row: row["country_code"])
    expected = read_csv("expected/p01_country_current.csv")
    assert actual == expected
    assert len({row["country_code"] for row in actual}) == len(actual)


def test_p02_snapshot_story_matches_expected_history_contract() -> None:
    s1 = {row["customer_id"]: row for row in read_csv("data/legacy/customer/snapshot_001.csv")}
    s2 = {row["customer_id"]: row for row in read_csv("data/legacy/customer/snapshot_002.csv")}
    s3 = {row["customer_id"]: row for row in read_csv("data/legacy/customer/snapshot_003.csv")}
    assert s1["C001"] != s2["C001"]
    assert "C003" not in s1 and "C003" in s2
    assert "C002" in s2 and "C002" not in s3
    assert s2["C003"] != s3["C003"]
    history = read_csv("expected/p02_customer_history.csv")
    assert sum(row["is_current"] == "true" for row in history) == 2
    assert any(row["customer_id"] == "C002" and row["end_reason"] == "absent_delete" for row in history)


def test_p07_latest_source_version_produces_expected_current_state() -> None:
    observations = read_csv("data/crm/customer/observations.csv")
    latest: dict[str, dict[str, str]] = {}
    for row in observations:
        key = row["customer_id"]
        if key not in latest or int(row["row_version"]) > int(latest[key]["row_version"]):
            latest[key] = row
    actual = [
        {
            "customer_id": row["customer_id"],
            "email": row["email"],
            "status": row["status"],
            "is_deleted": row["is_deleted"],
            "row_version": row["row_version"],
        }
        for row in sorted(latest.values(), key=lambda item: item["customer_id"])
    ]
    assert actual == read_csv("expected/p07_customer_current.csv")
    duplicates = [row for row in observations if row["customer_id"] == "C001" and row["row_version"] == "1001"]
    assert len(duplicates) == 2  # intentional lookback/redelivery


def test_p10_baseline_delivery_identity_is_unique_and_delete_is_explicit() -> None:
    rows = read_jsonl("data/sales/customer/debezium_normalized.jsonl")
    identities = {(row["_kafka_topic"], row["_kafka_partition"], row["_kafka_offset"]) for row in rows}
    assert len(identities) == len(rows)
    assert [row["source_lsn"] for row in rows] == sorted(row["source_lsn"] for row in rows)
    assert any(row["_operation"] == "d" and row["customer_id"] == "S002" for row in rows)
    expected = read_csv("expected/p10_customer_history.csv")
    assert any(row["end_reason"] == "cdc_delete" for row in expected)


def test_p12_baseline_event_identity_is_unique() -> None:
    rows = read_jsonl("data/commerce/order/events.jsonl")
    assert len({row["event_id"] for row in rows}) == len(rows)
    assert {row["event_type"] for row in rows} <= {
        "ORDER_CREATED",
        "ORDER_PAID",
        "ORDER_CANCELLED",
        "ORDER_SHIPPED",
    }
    assert len(rows) == len(read_csv("expected/p12_order_events.csv"))


def test_failure_injection_is_separate_and_intentional() -> None:
    bad_email = read_csv("data/failure_injection/crm_bad_email.csv")
    assert "@" not in bad_email[0]["email"]
    cdc = read_jsonl("data/failure_injection/debezium_duplicate_out_of_order.jsonl")
    assert cdc[0]["_kafka_offset"] == 13  # duplicate delivery identity from baseline
    assert cdc[1]["source_lsn"] < cdc[0]["source_lsn"]  # out-of-order source version delivery
    events = read_jsonl("data/failure_injection/order_duplicate_unknown.jsonl")
    assert events[0]["event_id"] == "E002"  # duplicate business-event identity
    assert events[1]["event_type"] == "ORDER_TELEPORTED"  # quarantinable unknown event type
