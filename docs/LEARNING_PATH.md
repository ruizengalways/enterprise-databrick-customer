# Learning Path

This repository is designed so a new data engineer can learn the framework from concrete data rather than reading abstractions first.

## Lab 0 — Understand the boundaries

Read `docs/PROJECT_CONTEXT.md` and explain why:

- framework code is a package;
- Terraform is not required for normal dataset onboarding;
- this customer repo owns metadata and expected results;
- the cheatsheet owns semantic definitions;
- a green local test is not the same as Databricks runtime certification.

## Lab 1 — P01 full snapshot current state

Files:

- `metadata/table_specs/country.yml`
- `data/reference/country/current.csv`
- `expected/p01_country_current.csv`

Questions:

1. Why can the source omit a reliable primary key and still support snapshot replacement?
2. What fidelity is lost between snapshots?
3. What proves a successful reconciliation?

## Lab 2 — P02 snapshot-derived SCD2

Compare `snapshot_001.csv`, `snapshot_002.csv` and `snapshot_003.csv`.

Identify:

- a changed customer;
- an inserted customer;
- a customer deleted by snapshot absence;
- why intermediate source changes between snapshots can never be reconstructed.

Then compare with `expected/p02_customer_history.csv`.

## Lab 3 — P07 watermark + lookback + soft delete

Study `data/crm/customer/observations.csv`.

Explain why Bronze is raw append even though Silver is current state, why overlap can redeliver data, and why `row_version` plus business key is different from `_ingest_run_id`.

Use `data/failure_injection/crm_bad_email.csv` to discuss quarantine versus hard failure.

## Lab 4 — P10 Debezium/full CDC -> SCD2

Study `data/sales/customer/debezium_normalized.jsonl` and the P10 metadata.

Trace one customer through create/update/delete events. Distinguish:

- Kafka delivery identity;
- source LSN/event ordering;
- business key;
- SCD2 business history.

Then inspect the duplicate/out-of-order failure fixture.

## Lab 5 — P12 business events

Use `data/commerce/order/events.jsonl` to build the canonical event sequence. Explain why a domain event is not the same thing as database CDC.

The failure fixture contains a duplicate event ID and an unknown event type; decide which should be deduplicated and which should be quarantined.

## Lab 6 — Certification thinking

Read `docs/CERTIFICATION_MODEL.md` and `certification/matrix.yml`.

For each of P01/P02/P07/P10/P12, write down what additional evidence is needed to move from C1/C2 to C3 and C4.

## Lab 7 — Recovery

Choose one failure injection and design:

1. detection;
2. containment;
3. repair request;
4. replay/rebuild scope;
5. consistent reconciliation cutoff;
6. proof that processing can resume safely.

## Lab 8 — Onboard a new pattern/source

Use the cheatsheet to classify a new source before writing code. If the semantics match an existing P01-P14 pattern, add customer metadata and a source adapter rather than creating a new core pattern. Only propose a new framework semantic pattern when the existing catalogue truly cannot represent the behavior.
