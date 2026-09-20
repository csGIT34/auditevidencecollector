# Guest and agent evidence

This supplement evaluates typed measurements from patch assessment, endpoint protection and vulnerability tools against an exact saved Azure inventory. It preserves the source run and its findings. It does not execute guest commands, install software, remediate hosts, authenticate a vendor API, or establish that an operator's normalization is correct.

Use [sample export](../examples/guest-export.json) and [sample criteria](../examples/guest-criteria.json) with synthetic runs. Sample criteria are test expectations, not approved workplace policy.

## Population and normalized input

The exact envelope contains `schema_version: "1.0"`, `kind: "guest_export"`, `mode`, `resource_ids`, and `records`. Mode is `synthetic` for fixture runs or `operator_export` for live source runs. Select one or more lowercase saved VM or VMSS ARM IDs in `resource_ids`.

Individual VMs are expected guests. Uniform VMSS resources expand to the instance IDs retained in the source run's instance-model observation. Missing or partial instance listings keep coverage incomplete even if every supplied record passes. An empty VMSS population remains incomplete. Select Flexible instances by their individual VM ARM IDs; a scale-set parent cannot stand in for an instance.

Each record contains exactly:

- `record_id`, `source`: bounded identifier tokens supplied by the normalizer; these are attribution, not authenticated identity.
- `resource_id`: an exact expected guest ARM ID, including the full Uniform VMSS child ID where applicable.
- `observed_at`: timezone-qualified export observation time.
- `os`: `linux`, `windows` or `unknown`; these measurements do not require an inferred guest OS.
- `patch`: `assessed_at`, `state`, `missing_critical`, `missing_security`, `reboot_pending`.
- `protection`: `reported_at`, `enabled`, `healthy`.
- `vulnerabilities`: `scanned_at`, `state`, `critical`, `high`.

Component timestamps can be null. States are `succeeded`, `failed`, `in_progress` or `unknown`. Counts are nonnegative integers or null; booleans are actual JSON booleans or null. A component timestamp cannot follow `observed_at`. Unknown fields, negative counts, booleans used as counts, duplicate resource/source pairs and resources outside the expected population are rejected before publication.

The importer accepts at most 4 MiB, 1000 selected resources, 1000 source records and 10000 expanded guest IDs. Submit one current measurement record per resource/source. Multiple sources for a guest remain separate; a failure is never replaced by another source's PASS. Missing expected guest records receive explicit UNKNOWN decisions. The project-defined input is already normalized: only its strict fields are retained, including its exact bytes and hash. Do not feed raw vendor exports into this endpoint.

## Ten predicates and criteria

Criteria use `schema_version: "1.0"`, `id`, `version`, `status` (`draft` or `approved`) and `checks`. An approval label is an operator assertion. Missing/draft criteria produce UNKNOWN.

| Check | Criterion | Observation prerequisites |
| --- | --- | --- |
| `patch_age_seconds` | Maximum seconds since assessment | Succeeded assessment and timestamp |
| `missing_critical_patches` | Maximum count | Succeeded assessment within explicit patch age criterion |
| `missing_security_patches` | Maximum count | Same as above |
| `reboot_pending` | Expected boolean | Same as above |
| `protection_age_seconds` | Maximum seconds since report | Report timestamp |
| `protection_enabled` | Expected boolean | Report within explicit protection age criterion |
| `protection_healthy` | Expected boolean | Same as above |
| `scan_age_seconds` | Maximum seconds since scan | Succeeded scan and timestamp |
| `critical_vulnerabilities` | Maximum count | Succeeded scan within explicit scan age criterion |
| `high_vulnerabilities` | Maximum count | Same as above |

Global `max_age_seconds` applies to `observed_at`. Globally stale/future observations produce UNKNOWN. Old component ages can fail their approved recency thresholds, while their associated counts/statuses remain UNKNOWN. Failed/in-progress scans and patch assessments cannot turn zero counts into PASS. Null fields remain UNKNOWN. Selected exported criteria can be satisfied only with complete known populations and no FAIL/UNKNOWN results. Failures and incomplete coverage can coexist.

These support parts of VM-V and VMSS-V. They do not prove scanner coverage, exploitation absence, remediation completion, vendor tamper protection, or full control effectiveness. Vendor severity definitions and count normalization require review before workplace use. Do not translate vendor severity levels or scan states by guesswork.

## Local commands

```sh
python -m azure_at_rest guest-import \
  --store /path/to/archive --run-id r-EXACT_SOURCE_RUN \
  --input examples/guest-export.json --criteria examples/guest-criteria.json \
  --as-of 2026-09-20T02:00:00Z --max-age-seconds 3600
python -m azure_at_rest guest-show --store /path/to/archive --evidence-id g-EXACT_SUPPLEMENT
python -m azure_at_rest guest-pdf --store /path/to/archive --evidence-id g-EXACT_SUPPLEMENT
```

Import success means the supplement was archived, not that the findings passed. Inspect its summary. Reports retain original measurements, criteria, time, source-manifest hash and frozen decisions. Replay checks object hashes and linkage without reassessing history. Publication writes its completion manifest last; interrupted writes are not completed evidence.

## Azure-hosted endpoints

Enable `CG_GUEST_ENABLED=true` to register two Function-key protected POST endpoints:

- `/api/guests/import`: exactly `{run_id, document, criteria, as_of, max_age_seconds}`. `document` is the normalized envelope above, not a string or a raw vendor payload.
- `/api/guests/reports`: exactly `{evidence_id}` for a `g-` supplement.

Both reuse the configured UAMI, evidence Blob account/container, execution expiry, operation locks and bounded budgets. Import/report require storage permissions only; no guest access or ARM transport is constructed. They return safe result IDs and archive metadata, with 201 for completed publication, 503 when disabled, 409 for overlap, and sanitized errors on failure. The deployment package does not depend on a developer machine.

To integrate a workplace agent/vendor, obtain its authenticated schema and export permissions, implement a reviewed native-to-normalized mapping, and feed that typed result to the hosted importer. Retain the approved mapping version and source exports according to workplace handling rules. Native Wiz and guest-tool adapters remain separate acceptance work; the normalized importer is not a claim that those external integrations have been validated.
