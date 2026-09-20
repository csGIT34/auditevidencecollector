# Local saved-evidence and PDF workflow

Version 0.3.0 preserves the complete workflow locally: collect and assess, preserve the facts and conclusions in a new archive run, select one exact saved run, generate one self-contained PDF, and archive that PDF as a new report version. This page describes the local workflow. The optional Azure Functions/Blob path is documented in [AZURE_FUNCTIONS.md](AZURE_FUNCTIONS.md); it does not require a database.

The auditor receives the PDF. The JSON files are internal records for historical reproducibility and future consumers; auditors do not need a database, JSON, Blob URL or separate spreadsheet to understand a finding. The PDF contains an index, scope/times, methods and criteria, actual saved facts, findings, dependencies, collection errors, missing/unknown/manual coverage, verification instructions, sources and provenance. The PDF embeds fonts bundled with ReportLab; characters outside their coverage are preserved as explicit Unicode code points rather than unreadable glyphs. Evidence IDs and internal links connect the findings index to resource details inside the same document.

The [NIST catalog](audit/README.md) covers proposed applicability across all 23 services and 20 families. Version 0.5.0 adds [scoped configuration and identity assessments](CONFIGURATION_ASSESSMENTS.md), including schema 1.1 archives and renderer 1.3. Schema 1.0 historical reads remain supported. Wider operating-evidence claims are not inferred from these predicates.

## Install and run

Python 3.11+; the local secure filesystem adapter currently requires POSIX `dir_fd`, no-follow opens and hard links (Linux/macOS). Collection and archive JSON need only the standard library. PDF generation uses the optional ReportLab dependency:

```sh
python3 -m pip install '.[pdf]'
python3 -m cloud_governance collect \
  --fixture examples/demo-fixture.json \
  --store ./evidence/archive
python3 -m cloud_governance runs --store ./evidence/archive
```

The demo collection deliberately exits **1** because it contains confirmed failures; a complete archive is still created. The output prints its unique `r-...` run ID. Copy that exact ID into the separate operation:

```sh
python3 -m cloud_governance pdf \
  --store ./evidence/archive \
  --run-id r-REPLACE_WITH_THE_EXACT_32_HEX_DIGIT_RUN_ID \
  --export ./output/pdf/auditor-report.pdf
```

The placeholder is deliberately invalid; use the ID printed by `collect` or `runs`. No `latest` shortcut exists. `pdf` loads that run's snapshot, saved assessment and saved explanatory context. It never calls Azure, `collect`, `assess`, or the current rule catalog to change historical findings. A new report ID is generated each time. The optional export also refuses to replace an existing file: choose a new name for another export.

Without `--export`, the archived PDF is already a normal local file beneath the configured root at the key printed by the command. Copy or deliver only that PDF to auditors. `pdf` returns 0 for successful rendering/publication even when the saved assessment contains failures; its success is not a control PASS. Exit 3 identifies invalid/incomplete/corrupt run input, unavailable PDF dependency, publication or export failure. If the archive succeeded but an extra export failed, output explicitly says the archived PDF exists.

Collection retains existing assessment exit codes: 0 scoped supported criteria satisfied, 1 confirmed failures, 2 incomplete coverage without confirmed failure, 3 input/output failure. With `--store`, loose JSON/Markdown exports are produced only when explicitly requested. Without `--store`, the existing default `evidence/audit.json` and `evidence/audit.md` behavior remains. Loose `--json`, `--report` and `--snapshot` outputs can replace their specified paths as before; they are **not** historical archives.

Live collection remains separately authorized and untested against a tenant. This feature does not grant permission to use personal/work credentials, provision resources, buy scans or make cloud changes. Offline fixture runs never authenticate.

## Object layout and completion

Paths below are portable logical keys, relative to the configured storage root:

```text
runs/r-<uuid4 hex>/intent.json
runs/r-<uuid4 hex>/snapshot.json
runs/r-<uuid4 hex>/assessment.json
runs/r-<uuid4 hex>/context.json
runs/r-<uuid4 hex>/manifest.json
runs/r-<uuid4 hex>/failure.json                 # only on recorded failure
reports/r-<run uuid>/p-<report uuid>/intent.json
reports/r-<run uuid>/p-<report uuid>/report.pdf
reports/r-<run uuid>/p-<report uuid>/manifest.json
reports/r-<run uuid>/p-<report uuid>/failure.json # only on recorded failure
```

UUIDs prevent same-timestamp collisions. Given run/report IDs, object keys are deterministic. There is no mutable index or overwritten `latest.pdf`.

| Record | Purpose |
| --- | --- |
| snapshot.json | Sanitized collected observations, original collection period, mode, inventory/child completeness and errors. No evaluation is substituted into these facts. |
| assessment.json | Saved results/reasons/scopes, dependencies, gaps, source references, rule/tool/schema versions, timestamps, summary and snapshot digest. |
| context.json | Frozen explanatory rule criteria/catalog plus program applicability outline, unresolved parameters and research source hashes. Hosted runs add versioned nonsecret execution/backend provenance. Later documentation/rule changes do not rewrite this context. |
| Run manifest | Original collection/assessment timestamps, archive timestamps, scope, versions, assessment conclusion/coverage flags and exact keys/lengths/SHA-256 for all three objects. Written last. |
| PDF manifest | New report ID/generation time, renderer/tool/dependency versions, original run-manifest hash and object descriptors, PDF key/size/hash and archive completion time. Written last. |
| Intent/failure records | A started attempt and, if possible, a sanitized failure stage/time. No credentials or raw exception/API payloads. |

An intent without a final manifest is incomplete. A failure marker makes a run unreportable even if an uncertain final-write acknowledgement left a manifest behind. Do not interpret `state: complete` as successful controls: it means object publication completed. `assessment_conclusion` and `coverage_incomplete` remain separate. `runs` verifies manifests and objects and labels missing/corrupt/failed archives explicitly. A storage failure may prevent writing its failure marker; a missing final manifest still prevents a completed run claim. If the final manifest was committed but its acknowledgement and failure-marker write both failed, publication has an ambiguous client outcome. Inspect the manifest and verify every object before treating that attempt as complete.

JSON archive creation begins after the collector and evaluator return. Collector-reported errors/gaps are saved. A process terminated before archiving begins has no saved run, and cannot produce a historical report. This implementation does not checkpoint an in-progress collection.

Failed/partial attempts are retained for operator inspection. There is no automatic deletion, repair, resumption or overwrite. Retry the operation to create a new run/report ID. Keep the original incomplete attempt until retention/incident handling policy permits cleanup. Do not manually fabricate completion records.

## Safety and historical meaning

`FileStore` validates portable keys, rejects traversal/symlinks/nonregular objects, creates private files/directories and publishes via a same-directory temporary file followed by an atomic no-replace hard link and filesystem sync. Existing objects are never replaced by the adapter. Concurrent writers for one key cannot both succeed. Select a local filesystem supporting those semantics; unusual/network filesystems require their own validation.

The operator must secure the storage root, its ancestors, backups and workstation. Application-level no-overwrite behavior is **not** WORM or tamper-proof storage: the same OS user or administrator can alter/remove files outside the tool. SHA-256 detects inconsistencies relative to the manifest, not an attacker replacing all objects and hashes. Retention duration, legal holds, backup and access policy remain organization-defined. No retention or immutability is configured automatically.

The PDF is a historical point-in-time view. Regeneration preserves saved facts, conclusions, criteria and context, but has a new generation time and renderer version; layout and binary bytes can differ with software versions. Retain the original archived PDF for exact-byte reproduction. A current-state verification command cannot reproduce a historical API response. Manual/process, inherited/common controls and a whole audit period require separate evidence and approved criteria. Current snapshots capture subscription scope; they do not explicitly capture the tenant ID.

The renderer operates in memory on one run; very large inventories may require future streaming/partitioned rendering work. Do not silently drop rows to reduce report size. Native Windows support requires a secure filesystem adapter extension and tests; it is not claimed by the current POSIX implementation.

## Modules and checks

- `cloud_governance/storage.py`: `ObjectStore` protocol and `FileStore` implementation (`put_new`, `read`, `keys`).
- `cloud_governance/archive.py`: context capture, versioned run publication/loading, listing, integrity checks and PDF publication.
- `cloud_governance/pdf_report.py`: saved-data-only ReportLab rendering, internal references and appendices.
- `cloud_governance/cli.py`: `collect --store`, `runs` and `pdf` entry points, preserving existing collect/assess use.
- `cloud_governance/program_scope.json`: packaged research outline copied into each run. Refresh deliberately after catalog changes with `python3 docs/audit/export_program_scope.py`; verify with `--check`.
- `tests/test_archive.py` and `tests/test_pdf_pipeline.py`: no-overwrite/concurrency, invalid paths/symlinks, partial/corrupt runs, historical selection, failure stages, PDF content and optional export semantics.

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate.py
python3 docs/audit/validate_catalog.py
python3 docs/audit/export_program_scope.py --check
```

PDF extraction tests require the optional test dependency `pypdf`; the existing optional JMESPath parser test requires `jmespath`. These are test-only and do not add runtime collection dependencies. Visually render a newly generated sample using Poppler after renderer changes, inspect tables/headers/footers/long IDs and all section transitions, and verify internal evidence links. See the [portable workplace guide](WORKPLACE_AZURE_HANDOFF.md) and [ready-to-use implementation prompt](prompts/AZURE_ADAPTER_IMPLEMENTATION.md) for the implemented Azure adapter and remaining workplace deployment steps.
