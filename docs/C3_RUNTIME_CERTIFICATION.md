# C3 real Databricks runtime certification

This document is for people. Automation must use `certification/c3-runtime.yml`, `certification/framework-lock.yml`, `certification/matrix.yml`, and `project/state.yml` instead of parsing this Markdown.

## What C3 proves

C3 proves that the exact framework package pinned by the customer repository can execute the reference semantic patterns in a real Databricks workspace and produce the deterministic expected outcomes in this repository.

C3 currently covers the reference vertical slices P01, P02, P07, P10 and P12. It does not certify failure recovery; that belongs to C4.

A green package test, successful Bundle deployment, or successful pipeline refresh by itself is not C3 evidence. The final verifier task must also match every actual result to the platform-neutral expected fixtures.

## Workspace prerequisites

Use a dedicated GitHub Environment named `databricks-certification`. Configure these GitHub Environment variables:

- `DATABRICKS_HOST`: the workspace URL.
- `DATABRICKS_CLIENT_ID`: the Databricks service principal configured for GitHub OIDC federation.
- `DATABRICKS_CERTIFICATION_CATALOG`: a pre-provisioned Unity Catalog catalog dedicated to certification.

The deployment identity needs enough privilege in that catalog to create the certification schemas and managed Delta tables, plus permission to deploy and run the Bundle job and serverless Lakeflow pipeline. The framework repository does not own these privileges or the catalog lifecycle.

The OIDC federation subject should match the GitHub Environment identity used by this workflow. Do not add a long-lived Databricks PAT merely to make certification convenient.

## Execution chain

The manually dispatched `Certify Databricks runtime C3` workflow runs only from the repository's `main` branch.

It performs the following chain:

1. Checks out the exact customer Git SHA selected by the workflow run.
2. Reads the exact framework SHA from the machine-readable framework lock.
3. Checks out that exact framework commit into `.framework` and verifies its package version.
4. Installs a pinned Databricks CLI and validates the Bundle.
5. Creates a replayable Bundle deployment plan and deploys that reviewed plan.
6. Runs `seed_fixtures` to overwrite the deterministic normalized source fixtures and P02 snapshot-history Bronze.
7. Runs the Lakeflow pipeline with a full refresh.
8. Runs `verify_outputs`, which normalizes Databricks physical SCD columns back into the semantic expected model and compares every reference pattern exactly.
9. Writes a verification record to `<catalog>.certification_control.c3_verification`.
10. Only after the verifier succeeds, emits a C3 evidence JSON artifact tied to the exact framework/customer SHAs.

Diagnostics from validation, planning, deployment and execution are uploaded separately so a failed certification run can be investigated without turning that failure into a certification claim.

## Why P02 is seeded differently

P02 models retained complete snapshots. The workload/capture adapter owns snapshot discovery and retention, while the reusable framework owns snapshot-to-SCD2 semantics. The C3 seed task therefore writes the retained deterministic snapshots to the declared snapshot-history Bronze table. The pipeline supplies a lazy snapshot callback to the framework; the framework does not scan customer fixture files or hard-code fixture versions.

## Why expected outputs stay platform-neutral

The expected CSVs describe semantic outcomes, not Databricks storage implementation details.

For P02 and P10, Databricks AUTO CDC creates `__START_AT` and `__END_AT`. The verifier translates those values into the repository's semantic `start_*`, `end_*`, `is_current`, and `end_reason` fields before comparison. This prevents Databricks-specific physical columns from leaking into the cross-platform meaning of the test cases.

## Interpreting failures

A seed failure normally means the certification identity lacks Unity Catalog privileges or a fixture cannot be materialized safely.

A pipeline failure can indicate dependency installation, Lakeflow API compatibility, schema/type problems, duplicate source sequencing, DQ failure, or a framework runtime defect.

A verifier failure means the pipeline ran but the result was semantically wrong. The verifier prints missing and unexpected canonical rows for each failed pattern and records a failed verification entry before raising.

Do not update `certification/matrix.yml` to `passed` merely because a resource exists in the workspace. C3 status should advance only after evidence from the real workflow has been reviewed and tied to the exact locked SHAs.
