# Architecture and extension guide

See [current status](STATUS.md) for what is implemented and validated. Collection, assessment, archives and reporting run without an AI/model dependency.

```text
ARM or fixture -> collector -> sanitized snapshot -> assessment
                                                   |
                                        create-only ObjectStore
                                        snapshot + result + context
                                                   |
                                       exact saved-run PDF renderer

Normalized Wiz file -> strict validation -> create-only Wiz source archive
                                                   |
Exact Azure run + exact Wiz import -> deterministic comparison
                                   -> new JSON/Markdown archive + hashes
                                   -> verified historical replay
```

## Ownership

| Module | Responsibility |
| --- | --- |
| `collector`, `safety`, `snapshot` | Explicit identities/scopes, bounded GETs/pagination, safe projection and replay validation. |
| `catalog`, `assessment`, `verification` | Exact-type rules, saved findings, source basis and independent read instructions. |
| `storage`, `azure_adapters` | Common `ObjectStore` protocol; local and Blob create-only writes, reads and listing. Azure credentials and SDK behavior stay at this boundary. |
| `archive`, `provenance`, `pdf_report` | Frozen run context, hashes, manifest-last completion and a separate PDF publication with its own identity. Historical rendering does not collect or reassess. |
| `hosting`, `function_app` | Strict configuration, cooperative budgets, per-process overlap locks, dependency cleanup and safe invocation/HTTP outcomes. `ExecutionError.outcome` carries the safe error envelope; no exception-message JSON protocol. |
| `wiz`, `reconciliation` | Validate/import normalized Wiz records; correlate exact resource IDs while retaining source meaning, time, completeness and identity. Shared storage, separate artifact kinds; Azure conclusions are not changed. |
| `cli`, `scripts` | Operator entry points, packaging, offline demonstrations and checks. Functions does not expose a Wiz upload endpoint. |

## Contracts and invariants

- Snapshot, assessment and archive contracts remain version 1.0. Rule version and PDF renderer version are unchanged by 0.4.0. Wiz evidence and comparison contracts are separate version 1.0 records.
- Run/report/import/comparison IDs select exact objects. There is no implicit latest source, overwrite or historical rewrite. Intent first, completion manifest last; a failure marker makes an attempt unreportable.
- Hashes detect mismatches relative to retained manifests. They are not signatures, proof against privileged replacement, or a WORM/retention guarantee.
- `ExecutionError` remains a `RuntimeError` subclass, but Python consumers must use its `outcome` property. Public HTTP status codes and JSON bodies are unchanged. Internal exception text contains only the fixed safe code.
- Cleanup always attempts both Blob client and credential closure. Cleanup can fail after archive completion; recover by invocation ID/source manifests before retrying work.
- Application locks protect a single process; they do not provide distributed exactly-once execution. Deadlines are cooperative; neither rendering nor an in-flight SDK call is forcibly interrupted by the application.
- A Wiz comparison is not an assessment: `COMPARISON_COMPLETE` means correlation checks completed without identified comparison gaps, not that any control passed. Missing findings never establish a pass.

## Adding behavior

Add an exact service rule with reviewed API/fields, sources, scope and normal/missing/denied/partial fixtures. Reuse the common snapshot and report path; do not collect a provider's entire response. Keep unsupported services visible. Tenant/Graph objects need an explicit identity/plane contract instead of pretending to be ARM resources.

For Wiz native transport/mapping, implement the [workplace acceptance contract](WIZ_INTEGRATION.md#native-wiz-mapping-and-api-handoff). Existing normalized imports/comparisons can be replayed unchanged. Do not add assumed API fields or authentication endpoints from unverified examples.

Run the focused tests, then `python scripts/validate.py`. Packaging and Terraform regression checks are described in the development guide. Evidence schema changes require explicit compatibility and historical replay proof before release.
