# Enterprise Databricks Customer

A deterministic **reference customer, learning lab, and certification repository** for [`enterprise-databrick-framework`](https://github.com/ruizengalways/enterprise-databrick-framework).

This repository behaves like a real consuming data-engineering project. It owns customer-specific metadata, source fixtures, expected outcomes, learning exercises, workload deployment definitions, and certification evidence. It does **not** own reusable framework internals or Databricks platform infrastructure.

## Why this repo exists

It has three equal responsibilities:

1. **Reference customer** — demonstrate how a company/workload repo consumes the reusable framework without copying framework source.
2. **Certification suite** — prove a specific framework Git SHA against deterministic data and explicit expected outcomes.
3. **Learning environment** — let a new engineer walk through realistic full snapshot, watermark, CDC, SCD2, soft-delete, business-event, quality, reconciliation, and recovery scenarios before touching production data.

## Human documentation vs machine contracts

These are deliberately separate.

### Human-readable

Humans read Markdown only:

- [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) — architecture narrative and repository boundaries.
- [`docs/CERTIFICATION_MODEL.md`](docs/CERTIFICATION_MODEL.md) — what C0-C5 mean.
- [`docs/DATASETS.md`](docs/DATASETS.md) — fixture stories and expected business changes.
- [`docs/LEARNING_PATH.md`](docs/LEARNING_PATH.md) — guided learning path.
- [`docs/DOCUMENTATION_AUDIT.md`](docs/DOCUMENTATION_AUDIT.md) — audit history and rationale.

### Machine-readable

Automation and future context recovery use structured files only:

- [`project/context.yml`](project/context.yml) — canonical four-repository architecture and truth hierarchy.
- [`project/state.yml`](project/state.yml) — dynamic audited heads, current milestone, and latest verified evidence pointer.
- [`project/repository.yml`](project/repository.yml) — this repository's ownership contract.
- [`certification/framework-lock.yml`](certification/framework-lock.yml) — exact framework SHA under test.
- [`certification/matrix.yml`](certification/matrix.yml) — machine-readable coverage/certification state.
- [`certification/evidence/`](certification/evidence/) — persisted certification evidence records.

**Automation must not parse Markdown to discover Git SHAs, certification status, repository ownership, or current project state.**

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

The customer repo may own `databricks.yml`, Lakeflow Jobs, and Pipelines because a **workload repo owns its deployable workload**. Terraform, workspaces, catalog topology, OIDC service-principal creation, and organisation-wide platform policy remain outside this repo.

## Current certification meaning

C0-C2 local/package evidence exists for the first reference scenarios. Real Databricks runtime execution and failure/recovery certification remain separate higher levels. The authoritative status is always [`certification/matrix.yml`](certification/matrix.yml), not prose in this README.

## Start here

For a human engineer:

1. read [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md);
2. read [`docs/CERTIFICATION_MODEL.md`](docs/CERTIFICATION_MODEL.md);
3. read [`docs/DATASETS.md`](docs/DATASETS.md);
4. follow [`docs/LEARNING_PATH.md`](docs/LEARNING_PATH.md).

For an automated agent or a new ChatGPT conversation:

1. read [`project/context.yml`](project/context.yml);
2. read [`project/state.yml`](project/state.yml);
3. read [`certification/framework-lock.yml`](certification/framework-lock.yml);
4. read [`certification/matrix.yml`](certification/matrix.yml);
5. inspect current GitHub `main`, open PRs, and Actions before making a newer status claim.

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

GitHub Actions performs the same checks and uploads machine-readable evidence containing the exact customer source SHA and exact framework SHA.

## Repository map

```text
.
├── project/                    machine-readable ecosystem/repository context
├── metadata/table_specs/       customer-owned dataset contracts
├── data/                       deterministic source fixtures
├── expected/                   independent business-level expected outcomes
├── certification/              framework lock + matrix + evidence
├── tests/                      fixture, contract, and semantic assertions
├── scripts/                    evidence generation
├── docs/                       human-readable documentation only
└── .github/workflows/          consumer-side certification CI
```

The key rule is simple: **the framework supplies reusable behavior; this repo supplies realistic customer evidence.**
