# Documentation Audit — 2026-08-31

This audit exists so future conversations can reconstruct the project from Git rather than relying on chat memory.

## Repositories audited

| Repository | Main SHA at audit completion | Role |
|---|---|---|
| `data-engineering-cheetsheet` | `bbf14c9ea4411e423f33f0c9f17b99daad7a3195` | semantic/design source of truth |
| `enterprise-databrick-framework` | `6be809f7c106b8432494797405e47492354d96d6` | reusable package |
| `enterprise-databrick-customer` | `59be3df3f278bdfea07f4790886db74474207a6e` before this hardening change | reference workload / learning / certification |
| `enterprise-databrick-infra` | `3f00addafa4c433660d18d65b009d0174a38ee57` | optional platform/IaC reference |

## Audit findings and corrections

### Cheatsheet

The core taxonomy, walkthrough and production-operability checklist were consistent. No semantic rewrite was required. The audit added:

- `PROJECT_CONTEXT.md` at the repo root;
- stable mapping of catalogue rows 1-14 to P01-P14;
- `docs/databricks-reference-implementation.md` explaining implementation/certification boundaries.

### Framework

The package-only README and integration boundary were already correct, but three monorepo-era documentation areas were stale:

1. `docs/architecture/platform-foundation.md` still described fixed DEV/CI/UAT/PROD catalogs, Terraform and Bundle deployment as framework-owned;
2. `docs/architecture/repository-strategy.md` still described one Databricks platform repository;
3. `docs/runbooks/configure-github-oidc.md` still described framework-repository environment/OIDC setup.

Those files were corrected. `docs/PROJECT_CONTEXT.md`, capability/blueprint certification wording and four-repo links were added/updated. Package CI passed before merge.

### Infra

Existing framework/infra ownership ADRs were correct. The audit added the authoritative platform context, platform-foundation guidance and GitHub workload-identity-federation runbook, and linked the customer certification repo. Terraform validation CI passed before merge.

### Customer

This repo was created as the independent reference consumer and now contains:

- exact framework SHA lock;
- P01/P02/P07/P10/P12 deterministic fixtures;
- independent expected outcomes;
- failure-injection data;
- customer-owned metadata specs;
- new-engineer learning path;
- C0-C5 certification model;
- P01-P14 certification matrix;
- GitHub Actions evidence generation.

The initial merged `main` validation run (`33380097491`) passed and produced a C2 evidence artifact for customer SHA `59be3df3f278bdfea07f4790886db74474207a6e` against framework SHA `bd133ad9ed381cb6abf4dc697afd5c0f4d118c81`. This hardening change deliberately advances the framework lock to the current audited framework `main` SHA and re-runs certification.

## Truth hierarchy

When documents disagree, resolve them in this order:

1. current Git/ADR decisions for repository ownership;
2. `data-engineering-cheetsheet` for technology-neutral semantic definitions;
3. framework metadata/contracts for executable package behavior;
4. customer certification lock/matrix/evidence for what has actually been certified;
5. infra docs for optional reference platform implementation.

Runtime state in Databricks is evidence/observation, not a replacement for desired-state Git contracts.

## Fast-changing Databricks facts

The following were re-checked against current Databricks documentation during this audit and should be web-verified again before future material changes:

- Declarative Automation Bundles (formerly Databricks Asset Bundles): https://docs.databricks.com/aws/en/dev-tools/bundles/
- Bundle direct deployment engine: https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes
- Unity Catalog workspace bindings: https://docs.databricks.com/aws/en/catalogs/binding
- workload identity federation: https://docs.databricks.com/aws/en/dev-tools/auth/provider-github
- AUTO CDC / snapshot CDC APIs: https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-apply-changes

Do not freeze time-sensitive platform behavior into the cheatsheet semantic model.

## New-conversation recovery rule

For any future conversation about this ecosystem:

1. read this file or `docs/PROJECT_CONTEXT.md` in customer;
2. inspect current `main` SHAs and open PRs;
3. read `certification/framework-lock.yml` and `certification/matrix.yml` before making certification claims;
4. read the target repo's `PROJECT_CONTEXT.md`/README;
5. web-verify fast-changing Databricks product guidance when relevant.

This is the durable handoff contract for the project.
