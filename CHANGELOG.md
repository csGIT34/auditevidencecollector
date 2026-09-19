# Release notes

## 0.5.0 — expanded configuration assessments

- Add 115 scoped predicates spanning all 23 service entries, configurable typed criteria and exact-resource overrides. Wider audit objectives remain incomplete.
- Add opt-in tenant-verified Graph metadata, diagnostic category pagination, UAMI federation and private endpoint target/approval evidence.
- Persist independent configuration results and overall outcomes; include them and frozen NIST objective references in historical PDFs.
- Write schema 1.1 archives/snapshots/assessments, preserve schema 1.0 reads, and require the new reader for new runs. No in-place archive migration.
- Add an all-service synthetic demonstration and a 215-objective delivery register. Native Wiz, deep workload/operating evidence and workplace validation remain open.

## 0.4.0 — 2026-09-19

- Fix credential cleanup being skipped when Blob client cleanup raises. HTTP error handling now uses `ExecutionError.outcome`; status codes and safe JSON response envelopes are unchanged. Python callers must stop parsing exception text as JSON.
- Add normalized Wiz evidence import, exact Azure/Wiz inventory and finding comparison, and hash-verified historical comparison reads. Provide strict v1 contract/reference schema, synthetic fixtures/demo and negative/preservation tests. Native Wiz API/authentication/export mapping remains workplace-specific work; this release does not claim a live Wiz connector.
- Add subprocess-isolated synthetic scale measurements and a CI scale regression. Local 2,000-resource PDF publication: 14.505 seconds, 389.77 MiB peak RSS; real Azure latency/CPU and work data remain unmeasured.
- Add documentation relative-link checks and isolated Terraform mock CI. Consolidate current status, architecture, local workflows and handoff, and correct stale pre-deployment statements.

Snapshot/assessment/archive v1, rule version 2026.09.19.1 and PDF renderer 1.2 remain unchanged. New imports/comparisons use separate create-only namespaces. Historical Azure runs/PDFs are preserved; the original retained 0.3.1 live archive was verified readable without changing any bytes. Local checks: 143 Python tests, four Terraform mocked plans and 22 packaged-runtime checks. Check the exact commit's CI before transfer.

The personal Azure app remains stopped on 0.3.2. This source release was not redeployed to the cloud. Rollback restores the earlier package or disables operations; it must not delete retained archives. An older release does not expose the new Wiz commands, but its Azure run/PDF namespaces are unchanged.

## Earlier validated baseline

The personal v0.3.2 pipeline completed repeated requests, a second collection, and current/historical PDFs after the Flex concurrency mitigation. See [that live validation record](infra/personal-lab/REPEAT_VALIDATION.md). Earlier dated documents preserve their historical observations. [Current status](docs/STATUS.md) identifies the remaining workplace validation boundaries.
