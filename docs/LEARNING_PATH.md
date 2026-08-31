# Learning Path

This repository lets a new data engineer learn the framework from concrete, self-contained scenarios before reading implementation internals.

## Lab 0 — boundaries and directory map

Read `docs/PROJECT_CONTEXT.md` and `docs/REPOSITORY_MAP.md`. Explain why the package, workload, platform Terraform, and semantic cheatsheet live in separate repositories.

## Lab 1 — P01 full snapshot

Open `fixtures/p01_full_snapshot/` and `metadata/table_specs/country.yml`.

Compare `input/country_current.csv` with `expected/country_current.csv`. Ask what fidelity is lost between snapshots and what reconciliation can prove.

## Lab 2 — P02 snapshot-derived SCD2

Open `fixtures/p02_snapshot_history/`.

Compare the three input snapshots, find an insert/change/delete-by-absence, then explain every row in `expected/customer_history.csv`. Identify why changes between snapshots are unrecoverable.

## Lab 3 — P07 watermark + lookback + soft delete

Open `fixtures/p07_watermark_soft_delete/`.

Explain why Bronze is raw append, why C001 is redelivered, why `row_version` differs from `_ingest_run_id`, and why a soft-delete row remains meaningful current state. Then inspect `failures/bad_email.csv` and decide quarantine versus hard fail.

## Lab 4 — P10 full CDC → SCD2

Open `fixtures/p10_full_cdc/` and the P10 metadata.

Distinguish business key, Kafka delivery identity, source LSN/order, and SCD2 history. Then use `failures/duplicate_out_of_order.jsonl` to reason about idempotent convergence and tombstone retention.

## Lab 5 — P12 business events

Open `fixtures/p12_business_events/`.

Explain why domain events are not database CDC. Use `failures/duplicate_unknown.jsonl` to decide which record is deduplicated and which is quarantined.

## Lab 6 — follow the real Databricks workload

Read, in order:

1. `databricks.yml`
2. `databricks/resources/c3-certification.yml`
3. `databricks/tasks/seed_fixtures.py`
4. `databricks/pipelines/reference_runtime.py`
5. `databricks/tasks/verify_outputs.py`

Trace the certification chain `seed → full refresh → exact verifier` and identify where reusable framework behavior ends and customer-owned adapter/transform behavior begins.

## Lab 7 — certification thinking

Read `docs/CERTIFICATION_MODEL.md`, `certification/matrix.yml`, `certification/c3-runtime.yml`, and `certification/c4-recovery.yml`. Explain what extra evidence is necessary for C3 and C4 and why fixture existence is not recovery evidence.

## Lab 8 — recovery design

Choose one ready C4 failure scenario and design detection, containment, repair/replay scope, consistent reconciliation cutoff, and proof of safe resume. Compare your design with the `planned` checkpoint/repair gaps in `certification/c4-recovery.yml`.

## Lab 9 — onboard a new source

Classify the source against P01-P14 first. If it matches an existing pattern, add a new pattern-scoped fixture story, metadata contract, source adapter, and expected oracle. Only propose a new core semantic pattern when the catalogue truly cannot represent the behavior.
