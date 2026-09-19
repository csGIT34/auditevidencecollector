# Workplace Azure handoff

Version **0.3.1** implements the previously deferred Azure adapter and a thin Azure Functions host. The full, self-contained deployment/configuration guide is [AZURE_FUNCTIONS.md](AZURE_FUNCTIONS.md). [MACOS_DEVELOPMENT.md](MACOS_DEVELOPMENT.md) covers local setup and source transfer. The published v0.3.0 commit passed [the successful Linux/macOS CI run for commit `83b0711`](https://github.com/csGIT34/auditevidencecollector/actions/runs/35452053904) (105 tests per OS, zero skips); later local preparation has a separate validation record. No hosted/live tenant assessment has run.

Production is an Azure Function App, independent of any person's computer. macOS is only for development/testing. Azure Automation is not this implementation's target. Source is published at [csGIT34/auditevidencecollector](https://github.com/csGIT34/auditevidencecollector), on `main`. The user supplies existing workplace infrastructure patterns: follow the [runtime contract](WORKPLACE_RUNTIME_CONTRACT.md). Terraform in `infra/personal-lab` is home-only.

## Implemented boundaries

- `function_app.py`: timer-capable `CollectEvidence` and a distinct key-protected POST `GenerateReport`. Both default disabled; no guessed schedule, implicit latest run, automatic report generation or anonymous route.
- `hosting.py`: strict settings, explicit subscription/optional single-RG scope, tenant preflight, structured safe invocation outcomes and bounded per-process overlap handling. An archived FAIL/INCOMPLETE finding is a completed job, not a process failure.
- `azure_adapters.py`: explicit user-assigned managed identity in Azure; explicitly opted-in tenant-bound CLI credentials locally; an ARM credential wrapper and a Blob ObjectStore. No default credential chain or cloud provisioning.
- `workflow.py`: deterministic collect-assess-archive orchestration and shared saved-report digest preparation, preserving existing encryption rules.
- `storage.py`: unchanged `put_new(key, bytes)`, `read(key)` and `keys(prefix)` interface plus the local POSIX FileStore.
- `archive.py`: facts, conclusions and frozen context stored separately; hashes/versions, completion manifests last, exact saved-run reads and unique archived PDFs.
- `provenance.py`: an additive versioned execution-context extension; old schema-1.0 runs without it remain readable.
- `pdf_report.py`: in-memory rendering with embedded package fonts, original evidence context and separate PDF-generation provenance. No database, JSON, private Blob URL or separate spreadsheet is needed by the auditor.

Blob creation uses an explicit create-if-absent condition on BlockBlob writes. A random per-attempt marker and exact downloaded bytes reconcile a lost acknowledgement; unrelated collisions remain errors even with equal bytes. Read/list failures cannot become success. Partial committed artifacts are retained, failure markers override final manifests, and incomplete attempts must not be repaired through overwrites. A failure to record a failure marker cannot revoke a manifest already committed during an ambiguous response. Neither Blob nor application no-overwrite behavior is a WORM certification; retention/legal holds remain workplace decisions.

## Inputs and validation still required at work

Supply the approved Function App plan/region and Python runtime; work tenant; existing attached user-assigned identity/client ID; explicit collection subscriptions; separate runtime and evidence storage accounts; existing evidence container/prefix; ARM and Blob permission scopes; private network/DNS path; authenticated report callers; package/source policy; schedule/UTC semantics; invocation budgets/overlap policy; classification, PDF recipients, alert ownership and retention duration. The checked-in settings templates intentionally contain no tenant/account values or keys.

Use identity-based `AzureWebJobsStorage` for production coordination, with permissions reviewed separately from retained evidence. Never place the runtime storage account under evidence retention locks. Before enabling reports, require approved inbound restrictions and work-tenant caller authentication in addition to Functions key authorization. Native Functions local key authorization is disabled, so development must remain local-only.

Run `python -m pip install -r requirements-dev.txt` in a new approved Python 3.12 venv, then `python scripts/validate.py`. It rejects skipped tests and checks the research outline. Build/install the wheel and exercise an offline fixture, exact-run PDF and historical preservation. `scripts/package_functions.py` creates an allowlisted source package; dependencies must be built for Linux, not copied from a Mac venv. The published v0.3.0 Linux/macOS jobs passed; run the gate again for any newly reviewed commit and the actual work environment.

Once separately authorized, validate against existing nonproduction workplace resources: identity/tenant, API availability/RBAC, Blob conditions, all failure stages, denied report callers, timer indexing/coordination, report latency/memory and historical integrity. Collection and PDF work are in-memory with cooperative budgets; the host may terminate a process before archive creation. There is no checkpoint/resume or exactly-once scheduling claim. Review real workload measurements before choosing production limits; no production benchmark is asserted.

The software still evaluates only scoped encryption at rest. `docs/audit/` preserves 215 proposed checks covering the 23-service program and all 20 NIST families; it does not certify operating controls. No runtime AI, database, dashboard, broad new collectors or remediation were added.

Ready-to-use prompts: [workplace configuration/implementation](prompts/AZURE_ADAPTER_IMPLEMENTATION.md) and [independent validation/rollout](prompts/AZURE_ADAPTER_VALIDATION.md). They can guide a reviewer with this repository and do not depend on conversation history or personal machine paths.
