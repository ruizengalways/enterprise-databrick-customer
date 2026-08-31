# Project Context — Enterprise Databricks Ecosystem

Last architecture audit: **2026-08-31**.

Read this file first when starting a new conversation, onboarding a new engineer, or resuming work after a break.

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

`enterprise-databrick-framework` is package-only. It must not own:

- Terraform
- workspaces or cloud networking
- organisation-specific Unity Catalog topology
- GitHub OIDC service-principal creation
- DEV/UAT/PROD environment configuration
- organisation-specific Bundle targets or promotion workflows

It may define runtime requirements and reusable control/recovery semantics, but environment-specific values are injected by the consumer/platform.

### Infra

`enterprise-databrick-infra` is optional. A company with an existing Databricks platform can ignore it entirely. Normal dataset onboarding must not require a data engineer to edit Terraform.

### Customer

`enterprise-databrick-customer` is a workload/reference implementation. It may own customer metadata, source adapters, domain transforms, tests, expected results, and workload deployment definitions. It must consume the framework as a dependency rather than copy `src/edp_framework`.

### Cheatsheet

`data-engineering-cheetsheet` is the semantic/design source of truth. P01-P14 names describe source/change semantics and Bronze behavior; platform-specific implementations may differ while preserving those semantics.

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
10. No framework version is called certified without reproducible evidence tied to an exact Git SHA.

## 4. Current implementation state

At this audit point:

- framework package-only split is merged on `main` at `bd133ad9ed381cb6abf4dc697afd5c0f4d118c81`;
- framework package CI is green for metadata validation, lint, strict typing, tests and wheel build;
- the P01-P14 semantic catalogue exists;
- runtime implementation for initial vertical slices is still being expanded; the branch `feat/phase3-runtime-package` exists and must not be treated as released until merged and certified;
- infra repo contains reusable Terraform modules for Unity Catalog environment resources, workspace bindings and GitHub OIDC service principals plus non-active deployment templates;
- customer repo is the authoritative certification/learning fixture set introduced by this audit;
- no claim of full Databricks runtime certification has yet been made.

Always check current GitHub `main`, open PRs, CI and `certification/framework-lock.yml` before making a newer status claim.

## 5. Certification contract

Certification is performed against an **exact framework commit**. `main` by itself is not an auditable certification identifier.

Evidence levels are defined in `docs/CERTIFICATION_MODEL.md`. The minimum release-quality claim requires real Databricks runtime evidence in addition to local package/fixture validation. Full certification also requires recovery/failure-injection evidence.

## 6. Reference scenarios

The first executable learning/certification verticals are deliberately heterogeneous:

- P01 — authoritative full snapshot/current replacement
- P02 — ordered full snapshots -> SCD2 history
- P07 — watermark + lookback + raw Bronze + source soft delete
- P10 — Debezium/full CDC -> event Bronze -> SCD2
- P12 — business-event stream -> canonical deduplicated events

The certification matrix reserves P03-P06, P08-P09, P11 and P13-P14 so incompleteness remains visible rather than silently implied away.

## 7. How to resume work safely

When a new conversation begins:

1. Read this file.
2. Read the README and current-state/capability document of the repository being changed.
3. Read `certification/framework-lock.yml` and `certification/matrix.yml` when certification is relevant.
4. Inspect current open PRs and GitHub Actions before assuming a branch is merged or a capability is certified.
5. Preserve repository boundaries above unless an explicit ADR changes them.
6. Update this context file whenever an architectural boundary, release/certification rule, or major milestone changes.

This file records architecture context, not private credentials, company secrets or environment-specific IDs.
