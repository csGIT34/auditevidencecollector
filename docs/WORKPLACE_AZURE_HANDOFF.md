# Workplace handoff: replace local object storage with Azure Blob Storage

This guide is self-contained and describes the actual version 0.2.0 implementation. Azure connectivity is **not implemented or tested here**. The current pipeline works against a configurable local filesystem root. The workplace implementation should add one adapter and its configuration/tests while preserving collection, evaluation and saved-data PDF semantics.

Use the [implementation prompt](prompts/AZURE_ADAPTER_IMPLEMENTATION.md) to start the work with an LLM that can read this repository. Use the [validation/deployment prompt](prompts/AZURE_ADAPTER_VALIDATION.md) after the adapter exists. Neither prompt depends on this conversation, a personal machine path, a preselected tenant or credentials.

## Accepted product and audit requirements

The audit program covers all applicable NIST controls across the 23 services in `docs/PROGRAM_SCOPE.md`. `docs/audit/` contains 215 proposed evidence checks and all-family applicability research. The executable assessment currently covers scoped encryption at rest only. Keep applicability, obtainable evidence, implemented checks and tenant findings distinct. Technical metadata does not prove access reviews, log review, restoration, incident handling or full-period control effectiveness.

The accepted workflow is:

1. Collect and deterministically assess existing authorized resources.
2. Archive a unique run containing observed facts, saved conclusions and the exact explanatory context/versions, with collection and assessment timestamps, scope, missing evidence and errors.
3. Select one exact saved run and produce **one self-contained PDF** from its saved facts/conclusions. No recollection, reassessment or implicit latest selection. Auditors need no database, JSON, blob links or external spreadsheet/index to interpret it.
4. Archive each generated PDF as a new report version associated with its run, with generation time/version and a completion manifest. Retain prior versions unchanged.

JSON is the internal structured record, not a required human deliverable. No database is needed. Collection, assessment, storage and PDF output must have no runtime AI/model-call dependency. MCP, dashboards, database/query infrastructure, broad new service collectors and automatic remediation are outside this adapter slice. Provider-managed at-rest keys are accepted; CMK is not a blanket requirement.

## Current interfaces and entry points

| Module | Actual responsibility |
| --- | --- |
| `storage.py` | `ObjectStore.put_new(key: str, data: bytes) -> None`, `read(key: str) -> bytes`, `keys(prefix: str) -> list[str]`; `FileStore` is the current adapter. `parts(key)` validates portable keys. |
| `archive.py` | `save_run(store, snapshot, report)`, `load_run(store, run_id)`, `list_runs(store)`, `publish_pdf(store, run_id)`. `encode`, `digest`, `snapshot_digest`, `identity` support the versioned contract. |
| `pdf_report.py` | `render_pdf(saved, generation) -> bytes`; uses only loaded run/context plus explicit new generation metadata. `renderer_dependencies()` checks the optional ReportLab dependency. |
| `cli.py` | `collect --store ROOT`, `runs --store ROOT`, `pdf --store ROOT --run-id r-... [--export FILE]`; currently instantiates `FileStore` directly. Add a small explicit storage factory/configuration seam here; do not silently change local defaults. |
| `collector.py` / `assessment.py` | Existing sanitized ARM/fixture collection and deterministic encryption rules. The storage adapter must not change their behavior. |
| `program_scope.json` | Packaged applicability outline saved into each run's `context.json`; its source catalog/hash and unresolved parameters preserve historical meaning. |

`archive.py` uses archive schema `1.0`, collection/assessment schema `1.0` and PDF renderer version `1.0`. Preserve version fields and add explicit migrations/dispatch only if a schema changes. `load_run` does not use current executable rules to reassess history. The [local workflow document](LOCAL_ARCHIVE_PDF.md) defines the layout and completion behavior in full.

Map logical keys directly to blob names below an optional operator-selected prefix. Use standard block blobs in an existing standard general-purpose v2 storage account. Do not translate a run key into a local absolute path or a mutable `latest` object. Existing keys include:

```text
runs/r-<32 hex UUID>/snapshot.json
runs/r-<32 hex UUID>/assessment.json
runs/r-<32 hex UUID>/context.json
runs/r-<32 hex UUID>/intent.json
runs/r-<32 hex UUID>/manifest.json
runs/r-<32 hex UUID>/failure.json
reports/r-<run UUID>/p-<report UUID>/intent.json
reports/r-<run UUID>/p-<report UUID>/report.pdf
reports/r-<run UUID>/p-<report UUID>/manifest.json
reports/r-<run UUID>/p-<report UUID>/failure.json
```

The `put_new` contract is atomic create-if-absent, never replacement. Existing-key conflict maps to `FileExistsError`; not found maps to `FileNotFoundError`; forbidden access should become a sanitized permission/I/O error. No archive/PDF layer may need SDK types, authentication objects or Azure paths. The adapter must not create the account/container, grant rights, modify access/retention or expose secrets in exception text.

`read` returns exactly the addressed object. `keys` returns all matching logical keys with paging completed and configured prefixes removed consistently. Do not assume a blob directory exists. A 403, incomplete listing or throttling exhaustion is an error, not an empty successful inventory. Validate keys before sending requests and reject unexpected external URLs/prefix escapes.

## Conditional writes, retries and completion

Use the SDK's create-only behavior for block blobs and verify that the underlying request enforces absence (for example `If-None-Match: *` where applicable). Do **not** copy documentation samples that set `overwrite=True`. A check-then-upload sequence without a server-side condition is race-prone. Test concurrent writers and large/block-upload paths, not only tiny JSON. [Microsoft conditional request semantics](https://learn.microsoft.com/en-us/rest/api/storageservices/specifying-conditional-headers-for-blob-service-operations), [Python upload guidance](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-upload-python).

Completion manifests remain last. A run consists of snapshot, assessment and context objects with lengths/hashes recorded in its manifest; PDF completion requires the generated PDF and its manifest. Intent-only or failure-marked publication is incomplete/unreportable. Failed/partial objects are retained. A failure marker overrides even a manifest left by an uncertain final-write acknowledgement. Do not replace evidence to repair a failed run or overwrite its failure marker. A new operation uses a new ID.

For transient failures, bounded retries must preserve the exact logical key and conditional-write protection. An ambiguous response after commit needs a deliberate rule: within that same in-flight operation, compare the stored object's exact bytes/hash to the attempted payload before deciding whether the request succeeded; unrelated existing objects always remain conflicts. Do not swallow authorization, integrity or schema failures, and do not retry forever. A missing completion manifest always leaves an incomplete archive. If a completion manifest was committed but its acknowledgement and the failure-marker write both fail, the client outcome is ambiguous; reconcile the final manifest and all referenced objects before reporting success. Do not promise that a failed marker write can revoke an already committed manifest. Add tests for timeout-before-write, commit-with-lost-acknowledgement, manifest failure and matching/nonmatching preexisting objects.

Archive completion is not a security outcome. Preserve saved `assessment_conclusion`, `coverage_incomplete`, original observation/assessment times, generator time, renderer/dependency version and source hashes. Regeneration can change PDF bytes/layout as renderer versions change, but never source facts or conclusions. Retain the original PDF for exact-byte reproduction.

## Identity, permissions and deployment inputs

Prefer Microsoft Entra authentication. For an Azure-hosted production runner, use the operator-selected managed identity explicitly. A development credential chain may use an already authorized work sign-in, but constrain/document tenant/cloud and credential precedence so it cannot silently use a personal or unintended identity. Never embed account keys, SAS tokens, client secrets or credentials in files, command output, PDFs, source or tests. Keep Azure SDK dependencies optional so local/offline use stays available. [Microsoft Entra authorization guidance](https://learn.microsoft.com/en-us/azure/storage/blobs/authorize-access-azure-active-directory).

Data access is separate from ARM Reader. The adapter needs read/list and create/write for its approved objects. Container-scoped Storage Blob Data Contributor is a documented built-in starting point but includes delete rights; prefer a reviewed custom role/conditions omitting deletion and unrelated capabilities if the workplace permits it. Separate report readers/writers or evidence/report containers only if the organization requires them; do not force a new architecture. RBAC alone is not a create-only guarantee; retain conditional writes and approved immutable-storage controls.

Obtain these organization-specific inputs before live integration:

- Azure cloud/authority, tenant, existing storage account endpoint, account type, container(s), optional prefix and approved nonproduction test scope.
- Execution location and explicit identity/authentication method, data roles/scope and work-tenant collection scope. Resource collection and blob storage may use distinct rights.
- Network/firewall/private endpoint/DNS/proxy path and owning network team's validation, including allowed outbound destinations.
- Data classification, resource/PII handling, authorized PDF recipients, access logging, evidence ownership, retention duration, legal holds and encryption requirements.
- Approved reliability/retry limits, capacity/cost budget, recovery/backup needs, operational alerting and incomplete-object handling.
- Package/runtime policy, deployment/change approval and live validation authorization.

None of these values is supplied or assumed by this repository. Do not create resources, grant consent/roles, enable paid services or upload organizational data without workplace authorization.

## Retention and immutability

Azure retention/immutability can strengthen production evidence preservation, but retention duration is organization-defined. Account/container/version-level policy and legal-hold choices require the storage/security/legal owners. Ensure the object workflow is compatible with chosen policies; versioning is additional protection, not permission to overwrite logical keys. Never automatically enable or lock a retention policy during development or tests. Review public guidance for the selected policy and account features before implementation. [Microsoft immutable storage overview](https://learn.microsoft.com/en-us/azure/storage/blobs/immutable-storage-overview).

## Required tests and rollout gates

1. Run the existing offline collection, archive, catalog and PDF tests first. Retain their invariants and add a reusable adapter contract covering exact bytes, create-only writes, prefix listing/pagination, not-found, denied, timeout/throttling, concurrent collisions and logical-key validation.
2. Use SDK fakes or an approved emulator to verify request conditions and all failure stages. No emulator/cloud infrastructure is installed by this local phase. Test multi-block upload and response-loss cases explicitly.
3. Exercise collect/assess → archive → select exact historical run → PDF archive through the adapter with sanitized fixtures. Block collection/assessment methods during report generation. Compare source JSON bytes and hashes before/after regeneration and ensure prior PDFs remain unchanged.
4. Extract PDF text and render all pages for visual inspection. Check every result/fact/dependency/error and service/family gap appears, long IDs fit, source/criteria are readable and evidence links stay internal. Auditors must receive one PDF, with no private external evidence dependency.
5. Only after authorization, test against the specified existing nonproduction account/container and work identity, with synthetic data and a bounded cost scope. Verify real identity, endpoint/network, permissions, no-overwrite conditions, failures and final manifests. Do not lock retention or test deletes on protected production evidence.
6. Review privileges, failure alerts, retention decision, operator documentation and package deployment. Roll out through change control. Roll back by selecting the local adapter or previous application version; do not mutate/delete archived evidence. Report precisely which checks used mocks/emulation versus live Azure and which remain unverified.

Success is a small tested adapter/configuration seam, preserved deterministic semantics, complete self-contained PDFs and an honest validation record. It is not a new database, service collector suite or compliance certification.
