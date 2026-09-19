# Workplace Azure handoff

Version **0.5.0** implements the Azure adapter and a thin Azure Functions host. Use [AZURE_FUNCTIONS.md](AZURE_FUNCTIONS.md), [MACOS_DEVELOPMENT.md](MACOS_DEVELOPMENT.md) and the [live validation record](../infra/personal-lab/LIVE_VALIDATION.md). The [Linux/macOS workflow](https://github.com/csGIT34/auditevidencecollector/actions/workflows/offline.yml) validates offline behavior and packaging. The [follow-up personal validation](../infra/personal-lab/REPEAT_VALIDATION.md) resolved the observed HTTP 503s, passed repeated-request and key-rejection checks, and completed a second scoped live collection plus current/historical PDFs without changing the original evidence. The app is stopped and temporary diagnostics were removed. The personal app remains on v0.3.2; the later source changes are locally validated separately; see current status for the exact release evidence. Workplace acceptance remains outstanding. See [current status](STATUS.md).

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

Run `python -m pip install -r requirements-dev.txt` in a new approved Python 3.12 venv, then `python scripts/validate.py`. It rejects skipped tests and checks the research outline. Build/install the wheel and exercise an offline fixture, exact-run PDF and historical preservation. `scripts/package_functions.py` creates an allowlisted source package; dependencies must be built for Linux, not copied from a Mac venv. Linux/macOS CI includes the full offline gate, and Linux also smoke-tests the packaged application in a pinned Microsoft Functions container. Check the exact commit being cloned and run the gate in the actual work environment.

Once separately authorized, validate against existing nonproduction workplace resources: identity/tenant, API availability/RBAC, Blob conditions, all failure stages, denied report callers, timer indexing/coordination, report latency/memory and historical integrity. Collection and PDF work are in-memory with cooperative budgets; the host may terminate a process before archive creation. There is no checkpoint/resume or exactly-once scheduling claim. Review real workload measurements before choosing production limits; no production benchmark is asserted.

The software now evaluates scoped encryption and [configuration/identity criteria](CONFIGURATION_ASSESSMENTS.md). `docs/audit/` preserves 215 proposed checks covering the 23-service program and all 20 NIST families; it does not certify operating controls. No runtime AI, database, dashboard or remediation is introduced. Broad objective coverage remains incomplete even though scoped predicates span the 23 services.

Ready-to-use prompts: [workplace configuration/implementation](prompts/AZURE_ADAPTER_IMPLEMENTATION.md) and [independent validation/rollout](prompts/AZURE_ADAPTER_VALIDATION.md). They can guide a reviewer with this repository and do not depend on conversation history or personal machine paths.

## Local work completed before transfer

Review [current status](STATUS.md), [architecture](ARCHITECTURE.md), [scale validation](LOCAL_SCALE_VALIDATION.md), and [Wiz integration](WIZ_INTEGRATION.md). Run `python scripts/demo_wiz.py --output ../wiz-demo` for the synthetic source/import/comparison/replay path. Native Wiz schema, endpoint, identity/read scopes and safe field mapping still need workplace verification. No personal evidence or credentials are part of the source package.

## Expanded assessment configuration

Supply approved criteria through `CG_ASSESSMENT_CRITERIA_JSON`. Missing/draft criteria retain observations as UNKNOWN. Enable `CG_GRAPH_ENABLED=true` only for intended tenant-wide metadata collection with separately authorized Graph read permissions. Graph is not limited by `CG_RESOURCE_GROUP`. New archives require the 0.5.0 reader; older runs remain readable without modification. Run the [all-service synthetic example](CONFIGURATION_ASSESSMENTS.md) locally before workplace acceptance.
