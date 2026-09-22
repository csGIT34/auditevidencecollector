# Operational evidence supplements

Version 0.8.0 accepts attributed operating records linked to one exact archived run. This supports restore exercises, access reviews, change/incident/remediation records, vulnerability and patch reports, workload reviews, provider attestations and exceptions. It does not independently execute those activities or certify their assertions.

The runnable synthetic input is [operational-evidence.json](../examples/operational-evidence.json). Use `synthetic` only with fixture runs; use `operator_supplied` with real collected runs. Every record supplies an owner, reviewer, objective IDs, observation time, evidence period and assertion (`SATISFIED`, `NOT_SATISFIED`, or `NOT_ASSESSED`). Resource-scoped records must name exact lower-case resource IDs present in the source run. Run-scoped records use an empty resource list and cover only that saved scope.

```sh
python -m cloud_governance operational-import --store /absolute/archive --run-id r_EXACT_ID --input records.json --as-of 2026-09-19T21:00:00Z --max-age-hours 24
python -m cloud_governance operational-show --store /absolute/archive --evidence-id o_EXACT_ID
python -m cloud_governance operational-pdf --store /absolute/archive --evidence-id o_EXACT_ID
```

Replace example IDs with returned IDs (actual IDs use a hyphen, followed by 32 hexadecimal characters). Import returns an `evidence_id`; PDF publication returns the immutable PDF key and digest. Original run files and automated results remain unchanged. Publications write intent first and completion manifests last; incomplete publications cannot be loaded. Readers verify stored object hashes and the source manifest before replaying the saved review, without recomputing historical freshness.

`CURRENT` means the observation lies within the chosen age window. Future observations, stale records and expired exceptions remain visible. Exceptions never suppress findings. Owner/reviewer identities, assertions and `reference_sha256` are importer declarations: referenced documents are not fetched, authenticated or hash-verified. Supply no credentials or confidential payloads in free text.

## Required evidence

Optional `requirements` declares up to 1,000 expected records using `requirement_id`, `evidence_type`, `objective_id`, `scope_kind`, `resource_ids`, `period_start` and `period_end`. Each required resource is assessed separately. A matching record must cover the entire required period and exact evidence type/objective/scope. Run-scoped assertions cannot satisfy resource-specific requirements.

The frozen review reports `MISSING`, `NO_CURRENT_EVIDENCE`, `CONFLICTING_ASSERTIONS`, `ASSERTED_NOT_SATISFIED`, `ASSERTED_SATISFIED` or `NOT_ASSESSED`. Matching current positive and negative assertions produce a conflict; none is silently selected as authoritative. These outcomes describe supplied statements, not independently verified control conclusions. An empty records array is accepted when requirements are provided, so an entirely missing evidence population can be reported. Without requirements, the importer makes no completeness claim.

## Azure Functions

Set `CG_OPERATIONAL_ENABLED=true` to register both optional POST routes. Leave it absent/false to register neither. Existing managed-identity, separate evidence storage, expiry and bounded execution settings apply; these operations require evidence Blob access, with no additional ARM or Graph API calls.

- `POST /api/operational/import`: JSON envelope with exactly `run_id`, `document` (the input object), `as_of`, and `max_age_hours`.
- `POST /api/operational/reports`: JSON with exactly `evidence_id`.

Both require a Function key through `x-functions-key`. They return 201 on completion, 400 for malformed envelopes, 409 for an operation already running in the process, and sanitized 500 errors for failed execution. Validation of record contents occurs before publication and may return an execution failure. Input documents are limited to 1 MiB and 1,000 records. Archive paths and all reports remain in the configured evidence store. Local smoke tests verify function registration and missing/wrong-key rejection; they do not establish live Azure permissions or data correctness.
