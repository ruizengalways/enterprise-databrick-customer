# Reference Datasets

All fixtures are synthetic, deterministic, safe to commit publicly, and deliberately small enough to inspect by eye.

Each semantic pattern has one self-contained folder under `fixtures/` containing normal input, independent expected output, and optional failure cases.

| Pattern | Fixture directory | Source shape | Main lesson |
|---|---|---|---|
| P01 | `fixtures/p01_full_snapshot/` | complete snapshot | current replacement, snapshot fidelity |
| P02 | `fixtures/p02_snapshot_history/` | ordered complete snapshots | snapshot-derived SCD2 + absence delete |
| P07 | `fixtures/p07_watermark_soft_delete/` | watermark observations | lookback/redelivery + raw Bronze + soft delete |
| P10 | `fixtures/p10_full_cdc/` | normalized full CDC | delivery identity vs source order + SCD2 |
| P12 | `fixtures/p12_business_events/` | domain events | event identity, canonical events, quarantine |

## P01 — full snapshot

`input/country_current.csv` is authoritative in full. Re-running the same snapshot must not create duplicate current-state rows. `expected/country_current.csv` is an independent oracle even though the initial values intentionally match the source snapshot.

## P02 — snapshot history

`input/snapshot_001.csv` through `snapshot_003.csv` encode inserts, changes, and deletion by absence. `expected/customer_history.csv` expresses logical snapshot intervals. Physical Databricks AUTO CDC `__START_AT`/`__END_AT` values are translated by the verifier before comparison.

## P07 — watermark/lookback + soft delete

`input/observations.csv` deliberately redelivers C001. Latest authoritative `row_version` wins; `_ingest_run_id` is delivery identity, not source version. `failures/bad_email.csv` is reserved for quarantine certification.

## P10 — full CDC

`input/debezium_normalized.jsonl` contains normalized create/read/update/delete records with Kafka coordinates and authoritative source ordering. `failures/duplicate_out_of_order.jsonl` tests redelivery plus late older source versions independently from the baseline.

## P12 — business events

`input/events.jsonl` contains unique baseline event identities. `failures/duplicate_unknown.jsonl` combines a duplicate event ID and an unknown event type to test deduplication and quarantine.

## Scale testing

These fixtures prove semantics, not throughput. Performance/load suites should generate larger data separately while preserving the same invariants; they should never replace these inspectable certification stories.
