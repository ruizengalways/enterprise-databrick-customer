# Documentation Audit — 2026-08-31

This is the **human-readable** audit narrative. The machine-readable audited heads and current evidence pointers live in `project/state.yml`; certification truth lives in `certification/`.

## Repositories audited

The audit covered all four repositories:

- `data-engineering-cheetsheet` — semantic/design source of truth;
- `enterprise-databrick-framework` — reusable package;
- `enterprise-databrick-customer` — reference workload, learning, and certification;
- `enterprise-databrick-infra` — optional platform/IaC reference.

## Findings and corrections

### Cheatsheet

The core taxonomy, walkthrough, and production-operability checklist were internally consistent. No semantic rewrite was required. The audit added stable P01-P14 labels and explicit mapping into the Databricks reference ecosystem without making the cheatsheet Databricks-specific.

### Framework

The package/infra split was correct, but a few monorepo-era documents still described environment topology, Terraform, Bundle deployment, and GitHub OIDC as though they belonged to the framework repository. Those were corrected. Historical resource-ownership guidance was marked superseded where appropriate, while preserving the useful one-owner-per-resource principle.

The framework now clearly owns reusable Python/runtime behavior and semantic contracts, not company platform topology.

### Infra

The infra repository remains optional and is the authoritative reference for platform provisioning concerns: Terraform, workspace/catalog binding, identities, workload-identity federation, and platform deployment templates. Environment names and catalog names are reference defaults, not framework requirements.

### Customer

The customer repository was turned into an independent reference consumer with:

- exact framework SHA locking;
- deterministic P01/P02/P07/P10/P12 fixtures;
- independent expected outcomes;
- failure-injection data;
- customer-owned metadata specs;
- guided learning material;
- C0-C5 certification semantics;
- a P01-P14 coverage matrix;
- GitHub Actions evidence generation;
- persisted certification evidence records.

C0-C2 evidence exists for the initial reference scenarios. Higher runtime/recovery levels remain intentionally separate and must be earned in a real Databricks environment.

## Human vs machine documentation boundary

The audit originally placed some dynamic state in Markdown. That has now been corrected.

```text
Human narrative / rationale
  README.md
  docs/**/*.md

Machine context / current state
  project/**/*.yml

Machine certification truth
  certification/**/*.{yml,json}
```

Markdown may describe what a concept means, but automation must never parse Markdown to discover current Git SHAs, certification status, dependency locks, or repository ownership.

## Truth hierarchy

When information conflicts, resolve it in this order:

1. current ADRs plus `project/repository.yml` for repository ownership;
2. `data-engineering-cheetsheet` for technology-neutral semantic definitions;
3. framework contracts/code for executable reusable behavior;
4. customer `certification/` files for what has actually been certified;
5. infra docs/code for the optional reference platform implementation.

Runtime state in Databricks is operational evidence, not a replacement for Git-owned desired-state contracts.

## Fast-changing Databricks facts

Product details such as Declarative Automation Bundles, workload identity federation, Lakeflow APIs, AUTO CDC APIs, workspace bindings, and runtime/serverless capabilities change over time. They must be re-verified against current Databricks documentation before material implementation changes.

Do not freeze those product details into the technology-neutral cheatsheet semantic model.

## Resume rule

A human should read `docs/PROJECT_CONTEXT.md` and the target repository's documentation.

An automated agent should read `project/context.yml`, `project/state.yml`, the certification lock/matrix, and current GitHub state first. This separation is the durable handoff contract for future conversations.
