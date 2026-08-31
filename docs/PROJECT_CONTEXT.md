# Project Context — Enterprise Databricks Ecosystem

This is the **human-readable** project context. Machine-readable context lives under `project/` and certification state lives under `certification/`.

Read this file first when onboarding a new engineer or when you want the architectural story. Automated agents should start from `project/context.yml` instead of parsing this Markdown.

## Project goal

Build a portfolio-quality, production-oriented Databricks data-engineering ecosystem that demonstrates enterprise ingestion, transformation, CDC/SCD, data quality, reconciliation, recovery, observability, and CI/CD practices without coupling reusable data-engineering logic to one company's infrastructure.

The project is intentionally split into four repositories:

| Repository | Human meaning |
|---|---|
| `data-engineering-cheetsheet` | technology-neutral pipeline semantics and the P01-P14 mental model |
| `enterprise-databrick-framework` | reusable installable Python package and runtime/data-engineering behavior |
| `enterprise-databrick-customer` | reference consuming workload, learning environment, deterministic fixtures, and certification authority |
| `enterprise-databrick-infra` | optional Terraform/platform baseline, identities, catalog/workspace boundaries, and deployment reference |

## Repository boundaries

### Framework

`enterprise-databrick-framework` is a reusable package. It must not own company-specific Terraform, workspaces, cloud networking, Unity Catalog topology, GitHub OIDC bootstrap, environment names, or promotion policy.

It may define reusable runtime contracts, semantic patterns, control/recovery behavior, and Databricks runtime registration functions.

### Infra

`enterprise-databrick-infra` is optional. An organisation with an existing Databricks platform can ignore it. Normal dataset onboarding should not require a data engineer to edit Terraform.

### Customer

`enterprise-databrick-customer` behaves like a real workload repository. It owns source fixtures/adapters, dataset metadata, expected outcomes, domain transforms, workload deployment definitions, tests, learning labs, and certification evidence. It consumes the framework as a dependency rather than copying framework source.

### Cheatsheet

`data-engineering-cheetsheet` remains the technology-neutral semantic source of truth. P01-P14 are stable labels for the fourteen design patterns; a Databricks implementation must preserve the source/Bronze/Silver/fidelity semantics rather than redefining them around a product API.

## Core design principles

1. Classify source semantics before choosing capture technology.
2. Capture mechanism and target semantics are independent dimensions.
3. SCD2 is a target/history contract, not an ingestion mode.
4. Source ordering, business identity, source-version identity, event identity, and delivery identity are distinct.
5. Bronze semantics must be explicit: current replica, raw observation append, snapshot history, or event history.
6. Every incremental/change workload declares bootstrap/handoff, delete completeness, idempotency, retention, reconciliation, and recovery.
7. Git owns desired behavior; runtime Delta/control state owns observations.
8. Code rollback and data recovery are separate operations.
9. Reconciliation must compare a consistent source position/snapshot cutoff.
10. A framework version is never called certified without reproducible evidence tied to exact Git SHAs.

## Certification model

Certification is deliberately layered:

- **C0** — contract/metadata validity;
- **C1** — deterministic semantic outcomes;
- **C2** — exact-SHA package integration;
- **C3** — real Databricks runtime execution;
- **C4** — failure/recovery behavior;
- **C5** — release/promotion certification.

A green C0-C2 run is valuable evidence, but it does not imply that Databricks runtime and recovery behavior are certified. See `docs/CERTIFICATION_MODEL.md` for the human explanation and `certification/matrix.yml` for the authoritative machine status.

## Initial reference scenarios

The first reference customer scenarios deliberately cover different semantic classes:

- P01 — authoritative full snapshot/current replacement;
- P02 — ordered full snapshots to SCD2 history;
- P07 — watermark + lookback + raw Bronze + source soft delete;
- P10 — full CDC/Debezium-style events to event Bronze and SCD2;
- P12 — business-event stream to canonical deduplicated events.

The remaining P03-P06, P08-P09, P11, and P13-P14 stay visible as gaps until they receive fixtures, runtime behavior, and certification evidence.

## Human vs machine context

The project intentionally keeps two representations:

```text
Human narrative
  README.md
  docs/**/*.md

Machine context/state
  project/context.yml
  project/state.yml
  project/repository.yml
  certification/**/*.yml
```

The Markdown explains **why**. YAML/JSON records **what is currently true**.

Do not build automation that extracts SHAs or status from prose.

## How to resume work

For a human:

1. read this file;
2. read the target repository README and relevant ADRs/runbooks;
3. read the certification model when evaluating correctness claims.

For an automated agent/new conversation:

1. read `project/context.yml`;
2. read `project/state.yml`;
3. read `certification/framework-lock.yml` and `certification/matrix.yml`;
4. inspect current GitHub `main`, open PRs, and Actions;
5. read human docs only when architectural explanation is needed;
6. web-verify fast-changing Databricks APIs/platform guidance before material runtime/platform changes.

The live repository SHAs and latest evidence pointers are intentionally **not duplicated here**; they belong in machine-readable state.
