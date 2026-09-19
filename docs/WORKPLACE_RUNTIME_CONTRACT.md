# Workplace runtime contract (use existing infrastructure patterns)

The user already has workplace patterns for Function Apps and storage. Supply these requirements to those patterns; **do not deploy `infra/personal-lab` at work or replace existing Terraform**. The home lab is a temporary integration test with a different network/caller boundary. Its real tenant settings, state, plans, billing details and evidence do not belong in source transfer.

The source is published at [csGIT34/auditevidencecollector](https://github.com/csGIT34/auditevidencecollector). Commit `83b0711` passed [Linux and macOS offline CI](https://github.com/csGIT34/auditevidencecollector/actions/runs/35452053904): 105 tests each, zero skips, distribution and source-package builds. The later home-lab/RG-scope changes have their own [local preparation record](../infra/personal-lab/VALIDATION.md); the old CI result must not be attributed to an unpushed commit. Neither proves live workplace connectivity.

## Runtime and package

Use an approved Linux x86_64 Python 3.12 Functions v4 environment; Flex Consumption uses `functionAppConfig.runtime`, deployment storage and scale/concurrency properties. macOS is development only. `host.json` chooses ten minutes; synchronous HTTP reports still need measured headroom under the platform HTTP limit. Keep storage, network paths, region, plan capacity, package feeds and cost/logging ownership within approved workplace policy.

Build from `requirements.txt`/`constraints.txt`, the application source and `program_scope.json`. `scripts/package_functions.py` emits a source-only ZIP. `scripts/build_functions_package.py` on Linux x86_64 Python 3.12 adds pinned runtime dependencies for a deployable package; **omit `--with-lab-probe` at work**. Do not deploy a Mac venv, Terraform directory, local settings, source checkout wholesale or personal evidence. ReportLab ships the embedded fonts. Use the plan's supported deployment method with approved Entra/federated identity; no repository token is embedded.

## Identity and storage

Explicitly attach the chosen UAMI, supply its **client ID**, and verify tenant ownership out of band. ARM requests use the managed identity SDK, no workstation login or automatic credential fallback. Collection preflight needs only `Microsoft.Resources/subscriptions/read` on every configured subscription to verify its ID, tenant and Enabled state. Inventory/detail permissions belong at the approved scope. Reader at a selected RG is sufficient for the current lab's metadata reads; custom workplace roles may be narrower. No secret/action/data-plane reads are part of ARM collection.

Keep Functions runtime/coordination and evidence storage in **separate accounts**. Runtime's identity-based `AzureWebJobsStorage` needs host/trigger permissions (Blob Data Owner for the current timer/HTTP-only design), reviewed against the chosen platform. Deployment package access can use that same runtime UAMI/account. Evidence needs existing container read/list/create-write access; the supplied adapter never creates accounts/containers. Avoid delete permissions where policy allows. Application conditional writes prevent overwriting existing keys; write RBAC and Blob alone are not WORM. Retention/legal holds, private endpoints, immutable policy and purge/backup ownership remain workplace decisions. Never apply evidence retention locks to runtime storage.

## Required app configuration

Use `deploy/app-settings.example.json` plus the full [configuration reference](AZURE_FUNCTIONS.md). For Flex, omit `FUNCTIONS_WORKER_RUNTIME` from deployment settings and set runtime in `functionAppConfig`; the local example keeps it for Core Tools. Required operational inputs are tenant UUID, selected UAMI client ID, explicit subscription UUIDs, separate runtime account, evidence URL/container/prefix, identity-based runtime connection, authorized callers and approved UTC cadence. No real values are committed.

`CG_RESOURCE_GROUP` optionally narrows collection to **one** explicit subscription and one portable ASCII RG name. With it, only that RG is listed and hydrated; out-of-scope IDs or changed pagination are rejected. The group is saved in the snapshot inventory and appears in the historical report. Without it, approved subscription-wide discovery remains unchanged. Missing or inaccessible external dependencies remain visible gaps, not reasons to expand permissions silently.

Both operations remain independently disabled by default. Collection produces a unique archived assessment, never an automatic PDF. The protected POST `/api/reports` accepts exactly `{"run_id":"r-<32 lowercase hex>"}` and renders saved facts/conclusions/context into a new report version. No `latest` fallback, recollection or reassessment. Optional `CG_EXECUTION_EXPIRES_AT` (timezone-aware ISO timestamp) rejects new work after a test window; omit it for an intentionally ongoing approved workplace service. It is a cooperative entry guard, not a budget cap or teardown mechanism.

## Caller security and acceptance

Configure approved work-tenant App Service authentication and explicit caller authorization plus inbound network restrictions before enabling reports. Function keys remain in request headers; they are not substitutes for named corporate authorization. The personal lab's operator /32 plus function-key model is deliberately limited to a temporary personal test, not a production recommendation. Do not copy its probe or public-storage network posture into the workplace.

Validate the existing workplace patterns against: successful runtime indexing and host-storage identity; correct UAMI/tenant; expected metadata/data grants and denials; absence of anonymous access; exact-run PDF behavior and archived hashes; conditional conflicts/ambiguous-response handling; audit FAIL versus execution failure; budget/HTTP headroom; overlap/schedule controls; safe logs and recovery. Preserve failed attempts and old binaries. Track actual workload duration/memory before enabling a cadence. The executable rules still cover scoped encryption at rest; 215 proposed checks across 23 services/20 families remain applicability research.
