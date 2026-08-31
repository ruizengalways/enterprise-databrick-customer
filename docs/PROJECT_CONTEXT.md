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
`enterprise-databrick-framework` is package-only. It must not own Terraform, workspaces/cloud networking, organisation-specific Unity Catalog topology, GitHub OIDC service-principal creation, DEV/UAT/PROD environment configuration, or organisation-specific Bundle targets/promotion workflows. Environment-specific values are injected by the consumer/platform.

### Infra
`enterprise-databrick-infra` is optional. A company with an existing Databricks platform can ignore it entirely. Normal dataset onboarding must not require a data engineer to edit Terraform.

### Customer
`enterprise-databrick-customer` is a workload/reference implementation. It owns customer metadata, source fixtures/adapters, domain transforms, expected results, tests, learning labs and certification evidence. It consumes the framework as a dependency rather than copying framework source.

### Cheatsheet
`data-engineering-cheetsheet` is the semantic/design source of truth. P01-P14 are stable routing/reference labels for the fourteen catalogue rows; platform implementations must preserve their semantics and fidelity limitations.

## 3. Core principles

1. Classify source semantics before choosing capture technology.
2. Capture mechanism and target semantics are independent dimensions.
3. SCD2 is a target/history contract, not an ingestion mode.
4. Source ordering, business identity, source-version identity, event identity and delivery identity are distinct.
5. Bronze meaning is explicit: current replica, raw observation append, snapshot history or event history.
6. Incremental/change workloads declare bootstrap/handoff, delete completeness, idempotency, retention, reconciliation and recovery.
7. Git owns desired behavior; Delta/system/control tables own observed runtime state.
8. Code rollback and data recovery are separate.
9. Reconciliation uses a consistent source position/snapshot cutoff.
10. Certification claims require reproducible evidence tied to exact framework and customer SHAs.

## 4. Audited repository state

Final audited documentation heads on 2026-08-31:

- cheatsheet `main`: `bbf14c9ea4411e423f33f0c9f17b99daad7a3195`;
- framework `main`: `950f0e3752705ae82ea5e7114ae688f26179ff9f`;
- infra `main`: `3f00addafa4c433660d18d65b009d0174a38ee57`;
- customer `main` immediately before this final lock update: `1ab491c1fd1e072146115fc26319835c3a8ba4ef`.

The certification lock in this change pins framework `950f0e3752705ae82ea5e7114ae688f26179ff9f`. Its C0-C2 status must be marked `passed` only after CI for this lock succeeds.

Framework runtime coverage is still being expanded. The branch `feat/phase3-runtime-package` exists but is not released or certified until merged and independently exercised here.

## 5. Certification contract

Certification is against an **exact framework commit and exact customer source commit**.

- C0 — contract validation
- C1 — deterministic semantics
- C2 — package integration
- C3 — real Databricks runtime
- C4 — failure/recovery
- C5 — release certification

C0-C2 success does not imply C3/C4. Full framework production certification remains unclaimed until real Databricks runtime and recovery evidence exists.

## 6. Reference scenarios

Current learning/certification fixtures cover:

- P01 — authoritative full snapshot/current replacement;
- P02 — ordered full snapshots -> SCD2 history;
- P07 — watermark + lookback + raw Bronze + source soft delete;
- P10 — Debezium/full CDC -> event Bronze -> SCD2;
- P12 — business-event stream -> canonical deduplicated events.

P03-P06, P08-P09, P11 and P13-P14 remain visible gaps until their fixtures/runtime/recovery evidence exists.

## 7. New-conversation recovery

1. Read this file and `docs/DOCUMENTATION_AUDIT.md`.
2. Read the target repo README/PROJECT_CONTEXT.
3. Read `certification/framework-lock.yml` and `certification/matrix.yml` before any certification claim.
4. Inspect current main SHAs, open PRs and Actions; do not infer status from old chat history.
5. Preserve repository boundaries unless an explicit ADR changes them.
6. Web-verify fast-changing Databricks guidance when relevant.
7. Update these context files whenever architecture, certification rules or major milestones change.

This file contains architecture context only, not credentials or environment secrets.
