# Wiz evidence integration

**0.4.0 implements an offline normalized-export importer, Azure inventory/finding comparison, immutable archives and verified historical reads. It does not implement or validate native Wiz authentication, API queries or export-field mapping.** See [current status](STATUS.md).

Wiz's [integration overview](https://www.wiz.io/integrations) links to its [documentation](https://docs.wiz.io). The documentation endpoint returned HTTP 403 from this development session on 2026-09-19. No account/schema was available. Accordingly, the contract below is **defined by this project**, not claimed to be a native Wiz export or GraphQL schema. No API endpoint, token scope, pagination field or native status meaning is guessed.

## Offline demo

With the normal Python development environment, run:

```sh
python scripts/demo_wiz.py --output ../wiz-demo
```

Use a new directory outside the checkout. This makes no Azure, Wiz or credential calls. It creates a synthetic Azure run and Wiz import, then a comparison with one matched resource, one Azure-only resource, one Wiz-only resource, and one HIGH/OPEN Wiz finding alongside an unchanged Azure encryption PASS. It verifies source hashes and writes `comparison.md`, `comparison.json`, `result.json` and a reusable private archive. The expected state is `REVIEW_REQUIRED`; differing populations and missing authenticated tenant provenance are visible.

The [example export](../examples/wiz/normalized-export.json) contains synthetic identities. The demo adjusts only its synthetic observation timestamps to match the generated fixture. A workplace mapper must retain actual source observation/scan timestamps, not substitute the time it downloaded the export.

## Import, compare, verify

```sh
python -m azure_at_rest wiz-import --input /private/normalized-wiz.json --store /private/archive
# Use the exact w-... printed above and an existing r-... in the same archive.
python -m azure_at_rest wiz-reconcile --store /private/archive \
  --run-id r-REPLACE_WITH_EXACT_ID --wiz-import-id w-REPLACE_WITH_EXACT_ID \
  --as-of 2026-09-19T15:00:00Z --max-age-hours 24 --max-skew-hours 1
python -m azure_at_rest wiz-show --store /private/archive --comparison-id c-REPLACE_WITH_EXACT_ID
```

The dates/thresholds shown are examples, not organizational policy. Supply an explicit comparison time and approved freshness/time-skew limits. CLI commands use local files; the Python functions take the shared `ObjectStore` interface and can use an existing Blob adapter when a separately configured workplace host supplies it. No Wiz HTTP route, timer or live transport is enabled.

Import and comparison commands return 0 for a successfully completed publication even when the comparison needs review. Read `comparison_state`; command success is not audit success. Invalid input, unreadable/corrupt archives and failed publication return 3 with a sanitized error. `wiz-show` verifies both comparison objects and both source archives before printing the saved Markdown; it never recomputes with new rules or current time.

## Normalized v1 contract

See the [JSON Schema reference](schemas/wiz-evidence-v1.schema.json). The Python validator is authoritative for identity, cross-record and chronology checks.

| Field | Meaning / validation |
| --- | --- |
| `schema_version`, `kind` | Exactly `1.0`, `wiz_evidence`. |
| `source.system`, `source.mode` | `wiz`; either `synthetic` or `operator_export`. Export source mode must agree with the Azure run's synthetic/live boundary. |
| `source.export_id`, `mapping_version` | Stable opaque source-export ID; project mapping contract `1.0`. Keep upstream query/export and actual mapper revision in the work integration's review record. |
| `source.exported_at`, `tenant_id` | Timezone-aware export timestamp and canonical lowercase Azure tenant UUID. The importer validates syntax; it does not authenticate this claim. |
| `source.scope` | Explicit unique subscription UUIDs and `resource_group` (null for subscription scope, otherwise one RG/one subscription). Must exactly match the saved Azure scope for comparison. |
| `inventory_complete`, `findings_complete` | Separate exporter assertions. Partial sources remain usable but require review. A filtered or partial export must not assert exhaustive coverage. |
| `resources` | Unique `wiz_id`, valid scoped ARM `resource_id`, actual `observed_at`. ARM IDs match case-insensitively. No display-name joins. |
| `findings` | Unique `finding_id`, scoped `resource_id` present in resources, `rule_id`, `severity`, `status`, `observed_at`. Rule IDs retain source meaning; no control equivalence is inferred. |
| Normalized severity | CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL, UNKNOWN. |
| Normalized status | OPEN, IN_PROGRESS, RESOLVED, REJECTED, UNKNOWN. These are project-contract values; a native mapper must document its translation. |

Unknown fields, malformed/duplicate JSON members, nonfinite numbers, duplicate resource/finding identities, out-of-scope/orphan findings, unknown enums, naive timestamps and observations later than export time are rejected. Input is limited to 20 MiB and 100,000 resource/finding records per list. Unknown upstream status values need an explicit mapping decision; they must not silently become RESOLVED. Do not supply titles, descriptions, raw properties, tokens, secrets or unfiltered API payloads.

## Comparison and evidence semantics

The output retains BOTH / AZURE_ONLY / WIZ_ONLY presence, original Azure rule/result/time, Wiz resource identity/time, every finding ID/rule/status/severity/time, stale observations/findings and time-skew gaps. It includes both source-manifest hashes, exact accepted input hash, declared scope/tenant/completeness, comparison parameters and tool version.

A recorded Azure tenant that differs from the export causes rejection. Missing Azure tenant provenance remains an explicit gap. Future observations relative to `--as-of` are rejected. Incomplete inventories/findings, stale records, time skew, unmatched resources or an empty population require review. The absence of a finding is never PASS; an OPEN Wiz issue does not automatically negate an unrelated encryption PASS. No matching by names, automatic rule/NIST equivalence, remediation, deduplication of distinct issues or recomputation of the saved Azure assessment occurs.

`external/wiz/w-.../` retains exact accepted file bytes with intent and final manifest. `comparisons/c-.../` retains JSON, human-readable Markdown, intent and final manifest. Each publication gets a new ID. Existing run/PDF/import/comparison objects are never replaced; partial attempts remain with a safe failure record where storage permits. Historical `wiz-show` also rejects a changed or missing source archive. The comparison is a separate supplemental report; it does not retrofit Wiz findings into an existing Azure PDF.

## Native Wiz mapping and API handoff

Finish these work-specific steps using real documentation and approved sample data:

1. Identify the actual product/entity/query/export versions, tenant/project filters, read-only scopes, endpoint and token flow. Record which data-plane fields are actually needed; keep secrets in the approved workplace secret/identity mechanism.
2. Supply a reviewed native-to-normalized field map with safe projections, source hash/revision, identity semantics, original timestamps and status translations. Include a redacted sample of every required record type. Do not manufacture observation times, cloud identities or completeness from export time or an empty response.
3. For API collection, implement bounded pagination/retries, terminal-page verification, partial/GraphQL-error handling and sanitized errors. Do not publish a complete source after a missing/denied/throttled page; fixtures must exercise these paths using the actual schema.
4. Add contract tests for those real samples and a strictly scoped live check. Verify tenant/resource mappings, freshness, source completeness, denied access, changed/unknown upstream fields and permission boundaries.
5. Feed the resulting normalized document into the existing importer. The validated archive/reconciliation/replay path remains unchanged. Measure work data size, define retention/access, and then configure hosting/cadence if wanted.

Until those steps pass, describe this accurately as **locally tested normalized Wiz evidence integration**, not a live Wiz connector.
