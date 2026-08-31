# Documentation Audit — 2026-08-31

This audit exists so future conversations can reconstruct the project from Git rather than relying on chat memory.

## Final audited repository heads

| Repository | Main SHA | Role |
|---|---|---|
| `data-engineering-cheetsheet` | `bbf14c9ea4411e423f33f0c9f17b99daad7a3195` | semantic/design source of truth |
| `enterprise-databrick-framework` | `950f0e3752705ae82ea5e7114ae688f26179ff9f` | reusable package |
| `enterprise-databrick-infra` | `3f00addafa4c433660d18d65b009d0174a38ee57` | optional platform/IaC reference |
| `enterprise-databrick-customer` | `1ab491c1fd1e072146115fc26319835c3a8ba4ef` immediately before this final-lock change | reference workload / learning / certification |

## Audit findings and corrections

### Cheatsheet

The core taxonomy, walkthrough and production-operability checklist were semantically consistent. No semantic rewrite was required. Added:

- root `PROJECT_CONTEXT.md`;
- stable catalogue-row -> P01-P14 mapping;
- `docs/databricks-reference-implementation.md` explaining implementation/certification boundaries.

### Framework

The package-only README/integration boundary was correct, but monorepo-era documentation remained. Corrected:

1. `docs/architecture/platform-foundation.md` — removed fixed DEV/CI/UAT/PROD/platform ownership from the package;
2. `docs/architecture/repository-strategy.md` — replaced obsolete single-platform-repo strategy with the four-repo architecture;
3. `docs/runbooks/configure-github-oidc.md` — moved platform identity ownership to infra;
4. `docs/adr/005-databricks-resource-ownership.md` — marked superseded by ADR-010 while retaining the one-authoritative-owner principle;
5. `docs/REPOSITORY_MAP.md` — routes independent certification to the customer repo.

Added/updated `docs/PROJECT_CONTEXT.md`, blueprint and capability language so package CI is never mistaken for Databricks runtime certification. Every framework documentation PR in this audit passed the complete package CI before merge.

### Infra

Existing framework/infra ownership ADRs were correct. Added:

- authoritative `docs/PROJECT_CONTEXT.md`;
- optional reference `docs/PLATFORM_FOUNDATION.md`;
- GitHub workload-identity-federation/OIDC runbook;
- current Declarative Automation Bundles/direct-engine guidance;
- links to the customer certification repo.

Terraform validation CI passed before merge.

### Customer

Established this repository as the independent reference consumer with:

- exact framework SHA lock;
- P01/P02/P07/P10/P12 deterministic fixtures;
- independent expected outcomes;
- failure-injection data;
- customer-owned metadata specs;
- new-engineer learning path;
- C0-C5 certification model;
- P01-P14 certification matrix;
- exact customer/framework SHA verification and evidence artifact generation.

The initial and hardened C0-C2 runs passed. The final framework lock is advanced by this change to `950f0e3752705ae82ea5e7114ae688f26179ff9f`; status is promoted to `passed` only after this exact lock succeeds in CI.

## Truth hierarchy

When documents disagree, resolve them in this order:

1. current Git/ADR decisions for repository ownership;
2. `data-engineering-cheetsheet` for technology-neutral semantic definitions;
3. framework metadata/contracts for executable package behavior;
4. customer certification lock/matrix/evidence for what has actually been certified;
5. infra docs for optional reference platform implementation.

Runtime Databricks state is evidence/observation, not a replacement for desired-state Git contracts.

## Fast-changing Databricks facts

These were re-checked against current Databricks documentation during the audit and should be web-verified again before future material changes:

- Declarative Automation Bundles: https://docs.databricks.com/aws/en/dev-tools/bundles/
- Bundle deployment modes/direct engine: https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes
- Unity Catalog workspace bindings: https://docs.databricks.com/aws/en/catalogs/binding
- GitHub workload identity federation: https://docs.databricks.com/aws/en/dev-tools/auth/provider-github
- AUTO CDC / snapshot CDC APIs: https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-apply-changes

Do not freeze time-sensitive product behavior into the technology-neutral cheatsheet.

## New-conversation recovery rule

For any future conversation about this ecosystem:

1. read this file or `docs/PROJECT_CONTEXT.md` in customer;
2. inspect current main SHAs and open PRs;
3. read `certification/framework-lock.yml` and `certification/matrix.yml` before certification claims;
4. read the target repo's README/PROJECT_CONTEXT;
5. web-verify fast-changing Databricks product guidance when relevant.

This is the durable handoff contract for the project.
