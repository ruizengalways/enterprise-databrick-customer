# Enterprise Databricks Customer

A deterministic **reference customer, learning lab, and certification repository** for [`enterprise-databrick-framework`](https://github.com/ruizengalways/enterprise-databrick-framework).

This repository behaves like a real consuming data-engineering project. It owns customer metadata, deterministic fixtures, expected outcomes, workload deployment definitions, learning material, and certification evidence. It does **not** own reusable framework internals or platform Terraform.

## Start here

Humans should read:

1. [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md)
2. [`docs/REPOSITORY_MAP.md`](docs/REPOSITORY_MAP.md)
3. [`docs/CERTIFICATION_MODEL.md`](docs/CERTIFICATION_MODEL.md)
4. [`docs/DATASETS.md`](docs/DATASETS.md)
5. [`docs/LEARNING_PATH.md`](docs/LEARNING_PATH.md)

Automation/new conversations should read structured state only:

1. [`project/context.yml`](project/context.yml)
2. [`project/state.yml`](project/state.yml)
3. [`certification/framework-lock.yml`](certification/framework-lock.yml)
4. [`certification/matrix.yml`](certification/matrix.yml)
5. [`project/repository.yml`](project/repository.yml)
6. [`project/layout.yml`](project/layout.yml)

Automation must not parse Markdown for Git SHAs, certification state, ownership, or current project status.

## Repository map

```text
.
├── certification/              machine certification contracts/evidence/schemas
├── databricks/                  deployable reference workload
│   ├── pipelines/               Lakeflow pipeline registration
│   ├── tasks/                   seed + verification job tasks
│   └── resources/               Bundle pipeline/job resource definitions
├── fixtures/                    self-contained deterministic pattern scenarios
│   ├── p01_full_snapshot/
│   ├── p02_snapshot_history/
│   ├── p07_watermark_soft_delete/
│   ├── p10_full_cdc/
│   └── p12_business_events/
├── metadata/table_specs/        customer-owned framework metadata
├── project/                     machine ecosystem/context/layout state
├── scripts/                     CI/evidence utilities
├── tests/                       local contract + semantic certification tests
├── docs/                        human-readable Markdown only
├── .github/workflows/           local C2 + real Databricks C3 automation
└── databricks.yml               Bundle entrypoint for this workload repo
```

Each pattern fixture directory keeps its normal input, independent expected output, and optional failure cases together. A new engineer should not need to search separate `data/`, `expected/`, and `failure_injection/` roots to understand one scenario.

## Ecosystem boundary

```text
data-engineering-cheetsheet
        semantic truth P01-P14
                 ↓
enterprise-databrick-framework
        reusable Python package
                 ↓
enterprise-databrick-customer
        workload + evidence + learning

enterprise-databrick-infra
        optional platform/IaC reference
```

The customer repo may own `databricks.yml`, Jobs, Pipelines, source adapters, and domain transforms because those are workload concerns. Workspace/network/catalog provisioning, organisation OIDC bootstrap, and Terraform stay in the infra/platform boundary.

## Certification meaning

C0-C2 prove contracts, deterministic semantics, and exact-SHA package integration. C3 requires a real Databricks workspace plus exact actual-vs-expected verification. C4 adds failure/recovery evidence. The authoritative live status is always [`certification/matrix.yml`](certification/matrix.yml).

## Local validation

```bash
python -m venv .venv
source .venv/bin/activate
pip install pytest PyYAML jsonschema ruff

# Install the exact framework SHA from certification/framework-lock.yml.
FRAMEWORK_SHA=$(python - <<'PY'
import yaml
print(yaml.safe_load(open('certification/framework-lock.yml'))['framework']['ref'])
PY
)
pip install "git+https://github.com/ruizengalways/enterprise-databrick-framework.git@$FRAMEWORK_SHA"

edp validate metadata/table_specs
ruff check databricks scripts tests
pytest -q
python scripts/build_c2_evidence.py --output certification-evidence.json
```

The durable layout contract is machine-readable in `project/layout.yml` and enforced by tests. The key rule remains: **the framework supplies reusable behavior; this repo supplies realistic customer evidence.**
