# Ready-to-use workplace LLM implementation prompt

Copy the prompt below into the workplace coding LLM with this repository available. It contains the settled requirements; the LLM must obtain environment-specific inputs before live use.

---

Implement an Azure Blob Storage adapter for this cloud-governance project. Inspect the current repository and applicable instructions first. Read `docs/WORKPLACE_AZURE_HANDOFF.md`, `docs/LOCAL_ARCHIVE_PDF.md`, `docs/PROGRAM_SCOPE.md`, and `docs/audit/README.md`; then inspect the actual modules and tests named below. Continue the existing implementation rather than replacing its data models or collection/assessment behavior.

The current version 0.2.0 works entirely with local filesystem storage. Its workflow is collect/assess → new archived JSON evidence and manifest → select one exact saved run → generate a single self-contained PDF from saved facts and saved conclusions → archive a new PDF/report manifest. JSON is internal structured evidence for historical reproducibility. **Auditors receive one PDF containing the supporting facts, criteria, methods, findings, errors/gaps, scope/times and internal index/appendices. They must not need a database, JSON files, blob URLs, another spreadsheet or an external index to interpret it.**

The program's authoritative scope is all applicable NIST controls across 23 services: Event Hubs; AKS; App registrations; Event Grid; Storage Accounts; Cosmos DB; Managed Redis; Function Apps; Key Vaults; PostgreSQL Flexible Servers; Azure Container Apps; user-assigned managed identities; private endpoints; Azure Container Registries; backup vaults; App Configuration; Application Insights; Managed Grafana; Managed Prometheus; Log Analytics Workspaces; Virtual Machines; Virtual Machine Scale Sets; Automation accounts. The research catalog distinguishes direct technical, shared, inherited and manual/process evidence and is provisional until RCSA/auditor agreement. Only scoped encryption checks are currently executable. This adapter must not claim to implement the proposed broader checks, approve thresholds or establish full-period control effectiveness. Provider-managed at-rest keys are accepted.

Actual extension seam:

- `azure_at_rest/storage.py` defines `ObjectStore` with `put_new(key: str, data: bytes) -> None`, `read(key: str) -> bytes`, and `keys(prefix: str) -> list[str]`. `parts(key)` validates portable relative keys; `FileStore` is the POSIX local adapter.
- `azure_at_rest/archive.py` exposes `save_run(store, snapshot, report)`, `load_run(store, run_id)`, `list_runs(store)`, and `publish_pdf(store, run_id)`. It writes intent/object/final-manifest records and stores safe failure stages. It validates exact object identity, byte length, SHA-256 and saved snapshot/result consistency.
- `azure_at_rest/pdf_report.py` exposes `render_pdf(saved, generation) -> bytes`. Rendering must remain a pure saved-data consumer with no collection, assessment, credential or Azure dependency. ReportLab is an optional dependency.
- `azure_at_rest/cli.py` currently constructs `FileStore` for `collect --store ROOT`, `runs --store ROOT`, and `pdf --store ROOT --run-id ID [--export FILE]`. Add a small explicit factory/configuration path for choosing local or Azure storage; preserve existing local commands and behavior.
- `azure_at_rest/program_scope.json` is the packaged research outline frozen into each run's `context.json`. `docs/audit/export_program_scope.py --check` validates it against the research source. Existing archived context must never be replaced by current documentation.
- `tests/test_archive.py`, `tests/test_pdf_pipeline.py` and the existing collector/rule/CLI tests define behavior to preserve.

Add a minimal maintainable Azure adapter using optional Azure SDK dependencies. Use standard block blobs in an operator-supplied existing standard general-purpose v2 account/container. Map logical object keys directly to blob names under an optional validated prefix; strip that prefix consistently when listing. Keep archive/PDF code independent of SDK types and authentication. No database, MCP server, dashboard, runtime AI, hosted runner, general plugin framework, new service collectors or unrelated refactor is part of this task.

Storage layout/invariants:

```text
runs/r-<32 hex UUID>/{intent,snapshot,assessment,context,manifest,failure}.json
reports/r-<run UUID>/p-<report UUID>/intent.json
reports/r-<run UUID>/p-<report UUID>/report.pdf
reports/r-<run UUID>/p-<report UUID>/manifest.json
reports/r-<run UUID>/p-<report UUID>/failure.json
```

Failure records exist only on failure. Run/report IDs define reproducible logical keys and are unique even in the same timestamp. Every collection produces a new run; every PDF generation produces a new report version. Never overwrite old evidence, results, context, PDFs or manifests. `put_new` must enforce create-if-absent on the server, not check-then-write. Verify SDK behavior corresponds to a no-overwrite condition such as `If-None-Match: *`; do not use `overwrite=True`. Test both simple and multipart/block upload. Map existing-object conflicts to `FileExistsError`, absent objects to `FileNotFoundError`, and denied/network failures to sanitized exceptions. Do not log raw SDK payloads, credentials or signed URLs.

Read exactly the requested key. Fully paginate `keys`; scope it to the configured container/prefix. Denied/incomplete listings must fail rather than appear empty. Validate keys before requests; no traversal/prefix escape or arbitrary remote URL redirection. Choose bounded retries for transient failures without relaxing create-only conditions. An ambiguous acknowledgement after commit may be resolved only within that same in-flight operation by verifying the exact attempted bytes/hash; do not adopt unrelated existing objects or retry by overwriting them.

Publish the completion manifest last, after all required objects are successfully stored. Intents without completion and any failure-marked run remain unreportable; a failure marker takes precedence over a manifest left by an uncertain final-write acknowledgement. Never mark a partial run/report complete. Archive completion means publication success, not audit PASS. Preserve original collection/assessment times, scope, failures/gaps, collector/rule/schema versions and saved conclusions. Preserve distinct PDF generation time, renderer/dependency version, source run-manifest hash/object descriptors, PDF size/hash and report association. No `latest` substitution; report generation must not call the collector/evaluator or pull current rule/scope context. Retain original PDFs for exact-byte reproduction; regenerated layout may vary with renderer versions while evidence meaning remains unchanged.

Authentication/inputs:

Use Microsoft Entra token authentication; prefer an explicitly selected managed identity for an Azure-hosted production runner. For authorized local work testing, use a bounded documented work credential chain with explicit tenant/cloud expectations. Do not store/embed account keys, SAS tokens, client secrets, personal credentials or organization data in source, prompts, tests, command output or PDFs. Blob data permissions are separate from ARM Reader. Scope read/list/create-write rights to the approved container/prefix; evaluate a custom role without delete/unneeded capabilities. Built-in Storage Blob Data Contributor includes delete and is only a starting point, not a default minimum. No account/container creation, role/consent grants or network/retention modifications in the adapter.

Before live integration, obtain the organization's cloud/tenant/authority, existing account endpoint, container/prefix, runner/identity, approved data-role scopes, network/private endpoint/DNS path, test-data/cost authorization, data classification/recipients, retention/legal-hold policy, package/runtime rules and deployment approvals. Do not invent these settings or use a personal tenant. They are not required to implement and test the adapter offline. Retention duration is organization-defined; do not automatically enable or lock immutable retention during development. Versioning/immutability are production policy decisions and do not replace unique keys and conditional writes.

Validation required before completion:

1. Run existing tests/catalog checks before and after the change. Add adapter contract tests for exact bytes, read/not-found, existing-key conflict, invalid keys/prefixes, full paginated listing, denial, throttling/timeouts, concurrent collisions and multipart uploads.
2. Use mocks or an explicitly permitted emulator first. Test each run/report failure stage, failed failure-marker writes and lost acknowledgements. No partial publication may appear complete.
3. Run a sanitized fixture through the full adapter pipeline. Create multiple runs and PDF versions, select the first exact run, patch collector/evaluator/current-context access to fail during rendering, and prove old object bytes/hashes remain unchanged.
4. Verify PDF content includes all saved resource facts/statuses/dependencies/errors and broader unassessed/manual/shared scope. Render and visually inspect all pages, long fields, tables, footers, internal links and section transitions. Deliver a sample self-contained PDF without requiring private external evidence links.
5. Do not run live Azure tests or deployment without the stated workplace authorization/inputs. If authorized, use existing nonproduction resources, explicit work identity, synthetic data and a bounded cost scope. Record which results are offline/mocked/emulated versus live. Never lock retention as part of a test.

Finish the concrete code, documentation and tests rather than stopping at a proposal. Resolve routine implementation details from the repository. Explain any actual blockers and missing environment decisions precisely. Summarize changed modules, executed checks, limitations, sample PDF, configuration requirements and remaining deployment actions. Do not claim full NIST coverage or live Azure validation without evidence. Preserve local adapter fallback and all archived historical records.
