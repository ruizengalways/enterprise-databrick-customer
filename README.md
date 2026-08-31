# Enterprise Databricks Customer

A deterministic **reference customer, learning lab, and certification repository** for [`enterprise-databrick-framework`](https://github.com/ruizengalways/enterprise-databrick-framework).

This repository behaves like a real consuming data-engineering project. It owns customer-specific metadata, source fixtures, expected outcomes, learning exercises, and certification evidence. It does **not** own reusable framework internals or Databricks platform infrastructure.

## Why this repo exists

It has three equal responsibilities:

1. **Reference customer** — demonstrate how a company/workload repo consumes the reusable framework without copying framework source.
2. **Certification suite** — prove a specific framework Git SHA against deterministic data and explicit expected outcomes. A framework version is never called certified without evidence.
3. **Learning environment** — let a new engineer walk through realistic full snapshot, watermark, CDC, SCD2, soft-delete and business-event scenarios before touching production data.

## Ecosystem

```text
data-engineering-cheetsheet
  semantic/design source of truth (P01-P14)
            |
            v
enterprise-databrick-framework
  reusable installable package
            |
            +-----------------------------+
            |                             |
            v                             v
enterprise-databrick-customer      enterprise-databrick-infra
reference workload + tests         optional platform/IaC baseline
```

The customer repo may use `databricks.yml`/Lakeflow Jobs/Pipelines because a **workload repo owns its own deployable workload**. Terraform, workspaces, catalog topology, OIDC service-principal creation and organisation-wide platform policy remain outside this repo.

## Current certification truth

The initial baseline is intentionally conservative:

- metadata/schema validation against an exact framework SHA: **active**
- deterministic fixture and expected-outcome tests: **active**
- real Databricks runtime execution: **not yet certified**
- failure/recovery certification on Databricks: **not yet certified**
- full P01-P14 runtime coverage: **not yet complete**

See [`certification/matrix.yml`](certification/matrix.yml). Do not interpret a green local CI run as proof that every Databricks runtime path is production-certified.

## Start here

For a new conversation or a new engineer, read in this order:

1. [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) — cross-repository context and non-negotiable decisions.
2. [`docs/CERTIFICATION_MODEL.md`](docs/CERTIFICATION_MODEL.md) — what “certified” means.
3. [`docs/DATASETS.md`](docs/DATASETS.md) — fixture semantics and expected changes.
4. [`docs/LEARNING_PATH.md`](docs/LEARNING_PATH.md) — guided labs.
5. [`certification/framework-lock.yml`](certification/framework-lock.yml) — exact framework version currently under test.

## Local validation

```bash
python -m venv .venv
source .venv/bin/activate
pip install pytest PyYAML
pip install "git+https://github.com/ruizengalways/enterprise-databrick-framework.git@$(awk '/^  ref:/{print $2}' certification/framework-lock.yml)"

edp validate metadata/table_specs
pytest
python scripts/build_certification_evidence.py --output certification-evidence.json
```

GitHub Actions performs the same checks and uploads a machine-readable evidence artifact containing both the customer SHA and the exact framework SHA.

## Repository map

```text
.
├── metadata/table_specs/       customer-owned dataset contracts
├── data/                       deterministic source fixtures
├── expected/                   business-level expected outcomes
├── certification/              framework lock + coverage/certification matrix
├── tests/                      fixture and semantic assertions
├── scripts/                    evidence generation
├── docs/                       context, learning and certification documentation
└── .github/workflows/          consumer-side certification CI
```

The key rule is simple: **the framework supplies reusable behavior; this repo supplies realistic customer evidence.**
