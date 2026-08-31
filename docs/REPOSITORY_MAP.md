# Repository Map

This document explains the repository to a human reader. The enforceable machine layout is `project/layout.yml`.

## Top-level rule

A top-level directory must answer a clear question:

- `certification/` — what can we claim, against which exact SHAs, and what evidence exists?
- `databricks/` — what workload code is actually deployed to Databricks?
- `fixtures/` — what deterministic customer scenario proves a semantic pattern?
- `metadata/` — what customer dataset contract is supplied to the reusable framework?
- `project/` — what is the current machine-readable ecosystem context/state/layout?
- `scripts/` — what CI/evidence utilities run outside the deployed workload?
- `tests/` — what can be proven without a live Databricks workspace?
- `docs/` — what explanatory material is for people?

Generic roots such as `src/`, `data/`, `expected/`, and `resources/` are intentionally forbidden in this repository because their ownership is ambiguous here.

## Pattern fixtures

Each certified pattern is self-contained:

```text
fixtures/p10_full_cdc/
├── input/
│   └── debezium_normalized.jsonl
├── expected/
│   └── customer_history.csv
└── failures/
    └── duplicate_out_of_order.jsonl
```

This arrangement is designed for onboarding: one folder tells the complete story of a pattern without cross-referencing unrelated roots.

P01/P02 currently have no baseline failure fixture, so they contain `input/` and `expected/`. P07/P10/P12 additionally contain `failures/` used by C4 scenarios.

## Databricks workload

```text
databricks/
├── pipelines/
│   └── reference_runtime.py
├── tasks/
│   ├── seed_fixtures.py
│   └── verify_outputs.py
└── resources/
    └── c3-certification.yml
```

`pipelines/` defines Lakeflow dataset registration. `tasks/` contains job-executed Python entrypoints. `resources/` contains Bundle resource declarations. The root `databricks.yml` remains the conventional Bundle entrypoint.

## Why the reusable framework is not here

The `.framework/` checkout is an ephemeral exact-SHA build input created by CI. Framework source is never copied into this repository. The deployed workload imports the built wheel just as a real company workload would consume an internal package.
