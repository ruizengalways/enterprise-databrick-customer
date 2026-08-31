# Project Context — Enterprise Databricks Ecosystem

Last architecture/documentation audit: **2026-08-31**.

Read this file first when starting a new conversation, onboarding a new engineer, or resuming work after a break. Also see `docs/DOCUMENTATION_AUDIT.md` for the audit trail.

## 1. Project goal

Build a portfolio-quality, production-oriented Databricks data-engineering ecosystem that demonstrates enterprise ingestion, transformation, CDC/SCD, data quality, reconciliation, recovery, observability and CI/CD practices without coupling reusable data-engineering logic to one company's infrastructure.

The project is intentionally split into four repositories.

| Repository | Authoritative responsibility |
|---|---|
| `data-engineering-cheetsheet` | technology-neutral pipeline semantics and P01-P14 design knowledge |
| `enterprise-databrick-framework` | reusable installable Python package and runtime/data-engineering semantics |
| `enterprise-databrick-customer` | reference consuming workload, deterministic fixtures, learning labs and certification evidence |
| `enterprise-databrick-infra` | optional Terraform/platform baseline, identities, catalog/workspace boundaries and deployment templates |

## 2. Non-negotiable repository boundaries

### Framework

`enterprise-databrick-framework` is package-only. It must not own Terraform, workspaces/cloud networking, organisation-specific Unity Catalog topology, GitHub OIDC service-principal creation, DEV/UAT/PROD environment configuration, or organisation-specific Bundle targets/promotion workflows.

It may define runtime requirements and reusable control/recovery semantics, but environment-specific values are injected by the consumer/platform.

### Infra

`enterprise-databrick-infra` is optional. A company with an existing Databricks platform can ignore it entirely. Normal dataset onboarding must not require a data engineer to edit Terraform.

### Customer

`enterprise-databrick-customer` is a workload/reference implementation. It may own customer metadata, source adapters, domain transforms, tests, expected results and workload deployment definitions. It must consume the framework as a dependency rather than copy `src/edp_framework`.

### Cheatsheet

`data-engineering-cheetsheet` is the semantic/design source of truth. P01-P14 are stable routing/reference labels for the fourteen catalogue rows; platform-specific implementations may differ while preserving those semantics and fidelity limitations.

## 3. Core data-engineering principles

1. Classify source semantics before choosing capture technology.
2. Capture mechanism and target semantics are independent dimensions.
3. SCD2 is a target/history contract, not an ingestion mode.
4. Source ordering, business identity, source-version identity, event identity and delivery identity are distinct concepts.
5. Bronze semantics must be explicit: current replica, raw observation append, snapshot history, or event history.
6. Every incremental/change workload declares bootstrap/handoff, delete completeness, idempotency, retention, reconciliation and recovery.
7. Git owns desired behavior; runtime Delta/system/control tables own observed state.
8. Code rollback and data recovery are separate operations.
9. Reconciliation uses a consistent source position/snapshot cutoff, not unrelated wall-clock queries.
10. No framework version is called certified without reproducible evidence tied to exact Git SHAs.

## 4. Audited repository state

At completion of the documentation audit:

- cheatsheet `main`: `bbf14c9ea4411e423f33f0c9f17b99daad7a3195`;
- framework `main`: `6be809f7c106b8432494797405e47492354d96d6`;
- infra `main`: `3f00addafa4c433660d18d65b009d0174a38ee57`;
- customer baseline `main` before this certification-hardening change: `59be3df3f278bdfea07f4790886db74474207a6e`.

The customer certification lock is deliberately advanced to framework `6be809f7c106b8432494797405e47492354d96d6` by this change. Do not mark the new lock `passed` until its CI evidence succeeds.

Framework package behavior currently includes the metadata/semantic foundation; executable runtime coverage for initial vertical slices is still being expanded. The branch `feat/phase3-runtime-package` exists but must not be treated as released until merged and independently certified.

## 5. Certification contract

Certification is performed against an **exact framework commit and exact customer source commit**. `main` alone is not an auditable identifier.

Evidence levels are defined in `docs/CERTIFICATION_MODEL.md`:

- C0 contract validation;
- C1 deterministic semantics;
- C2 package integration;
- C3 real Databricks runtime;
- C4 failure/recovery;
- C5 release certification.

A green C0-C2 run is valuable but is not a substitute for C3/C4. Full framework correctness/production certification must remain unclaimed until those levels have evidence.

## 6. Reference scenarios

The first executable learning/certification verticals are deliberately heterogeneous:

- P01 — authoritative full snapshot/current replacement;
- P02 — ordered full snapshots -> SCD2 history;
- P07 — watermark + lookback + raw Bronze + source soft delete;
- P10 — Debezium/full CDC -> event Bronze -> SCD2;
- P12 — business-event stream -> canonical deduplicated events.

The matrix keeps P03-P06, P08-P09, P11 and P13-P14 visible as gaps until their fixtures/runtime/recovery evidence exists.

## 7. How to resume work safely

When a new conversation begins:

1. Read this file and `docs/DOCUMENTATION_AUDIT.md`.
2. Read the README/current-state document of the repository being changed.
3. Read `certification/framework-lock.yml` and `certification/matrix.yml` before any certification claim.
4. Inspect current `main`, open PRs and GitHub Actions before assuming a branch is merged or a capability is certified.
5. Preserve the repository boundaries above unless an explicit ADR changes them.
6. Web-verify fast-changing Databricks platform guidance (Bundles, identity, connectors/runtime APIs) when relevant.
7. Update this context whenever an architectural boundary, release/certification rule or major milestone changes.

This file records architecture context, not credentials, company secrets or environment-specific IDs.
