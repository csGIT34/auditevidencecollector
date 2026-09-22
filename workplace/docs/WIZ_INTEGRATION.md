# Wiz evidence integration

**Current source implements project-defined v1/v2 imports, inventory/finding comparison, positive/negative observations and selectable reports. Native Wiz authentication, API queries and export-field mapping remain unimplemented/unverified.**

## Full audit evidence and native capability verification

Requirement clarified 2026-09-21: preserve positive/negative evidence, observations, operating records, exceptions and missing coverage. Wiz is more than an open-issue feed. The v1 reader is preserved; v2 adds observed facts, evaluations and scan coverage. History and native mapping still require implementation.

Public capabilities reviewed for the planned integration:

| Path | Contribution to audit evidence | Contract boundary |
| --- | --- | --- |
| Wiz API / native exports | Asset inventory, configuration evidence, vulnerability/configuration findings and Issues | Verify the tenant's schema, permissions, scan coverage and availability of positive evaluations; retrieve the relevant full population and states |
| Wiz Audit History | Configuration changes and historical configuration/finding records where available | Verify entitlement, retention, current feature status and supported API/export access; do not infer API access from UI availability |
| Wiz CLI artifacts from existing pipelines | IaC/container/code scan records, evaluated scope and policy outcomes where emitted | Verify installed version and native output; retain artifact digest/commit, scan identity, timestamps, completion and criteria; do not infer deployment state from build-time scans |

Sources: [Wiz's documented integration exports](https://www.wiz.io/integrations/caveonix), [Audit History announcement](https://www.wiz.io/blog/introducing-audit-history), [CLI JSON/SARIF integration](https://www.wiz.io/integrations/harness). These establish candidate product capabilities, not this project's live connector contract. Detailed tenant documentation and authenticated schema access were not available in this review.

V2 separates inventory, safe observed properties, evaluations and scan coverage. Preserve original outcomes and observation/scan times. Native historical changes and Wiz exceptions need a subsequent reviewed contract; existing attributed operating exceptions can already accompany reports. Missing positive outcomes remain unavailable rather than inferred from absence of findings.

An issue marked resolved, rejected or suppressed is lifecycle/exception evidence, not automatically a currently passing check. A completed scan with no matching detections supports a limited statement about that scan's target, rule set and time; an empty Issues response provides no such coverage proof by itself. Store secret-detection metadata and safe references, not discovered credential values or sensitive snippets.

V2 scan targets accept exact ARM IDs, container digests and repository commits. Native workload identities and relationships to deployed resources still need a reviewed mapping. Preserve conflicts/time skew. Native pagination/completeness and GraphQL partial errors must be tested before claiming a complete source.

Selected reports link exact v1/v2 imports without rewriting them or old Azure runs. Offline tests cover positive/negative outcomes, missing coverage, partial scans, scope mismatch, safe-field exclusion and corruption. Native denial/pagination/history tests remain integration work. See [report usage](EVIDENCE_REPORTS.md).

Wiz's [integration overview](https://www.wiz.io/integrations) links to its [documentation](https://docs.wiz.io). The documentation endpoint returned HTTP 403 from this development session on 2026-09-19. No account/schema was available. Accordingly, the contract below is **defined by this project**, not claimed to be a native Wiz export or GraphQL schema. No API endpoint, token scope, pagination field or native status meaning is guessed.

## Offline demo

With the normal Python development environment, run:

```sh
python scripts/demo_wiz.py --output ../wiz-demo
python scripts/demo_audit_evidence.py --output ../audit-rehearsal
```

Use a new directory outside the checkout. This makes no Azure, Wiz or credential calls. It creates a synthetic Azure run and Wiz import, then a comparison with one matched resource, one Azure-only resource, one Wiz-only resource, and one HIGH/OPEN Wiz finding alongside an unchanged Azure encryption PASS. It verifies source hashes and writes `comparison.md`, `comparison.json`, `result.json` and a reusable private archive. The expected state is `REVIEW_REQUIRED`; differing populations and missing authenticated tenant provenance are visible.

The [example export](../examples/wiz/normalized-export.json) contains synthetic identities. The demo adjusts only its synthetic observation timestamps to match the generated fixture. A workplace mapper must retain actual source observation/scan timestamps, not substitute the time it downloaded the export.

## Import, compare, verify

```sh
python -m cloud_governance wiz-import --input /private/normalized-wiz.json --store /private/archive
# Use the exact w-... printed above and an existing r-... in the same archive.
python -m cloud_governance wiz-reconcile --store /private/archive \
  --run-id r-REPLACE_WITH_EXACT_ID --wiz-import-id w-REPLACE_WITH_EXACT_ID \
  --as-of 2026-09-19T15:00:00Z --max-age-hours 24 --max-skew-hours 1
python -m cloud_governance wiz-show --store /private/archive --comparison-id c-REPLACE_WITH_EXACT_ID
```

The dates/thresholds shown are examples, not organizational policy. Supply an explicit comparison time and approved freshness/time-skew limits. CLI commands use local files; the Python functions take the shared `ObjectStore` interface and can use an existing Blob adapter when a separately configured workplace host supplies it. No Wiz HTTP route, timer or live transport is enabled.

Import and comparison commands return 0 for a successfully completed publication even when the comparison needs review. Read `comparison_state`; command success is not audit success. Invalid input, unreadable/corrupt archives and failed publication return 3 with a sanitized error. `wiz-show` verifies both comparison objects and both source archives before printing the saved Markdown; it never recomputes with new rules or current time.

## Normalized v2 contract

The [complete synthetic example](../examples/wiz/observations-export.json) is copyable; `cloud_governance/wiz_observations.py` is authoritative. This is a project format, not native Wiz JSON/SARIF/GraphQL. Source and inventory/finding fields retain v1 semantics, with `schema_version` and `source.mapping_version` set to `2.0`. Required additions:

| Field | Retained evidence |
| --- | --- |
| `observations[]` | `observation_id`, exact known `resource_id`, `observed_at`, nonempty allowlisted `values` |
| `evaluations[]` | Unique `evaluation_id`, known resource, `rule_id`, source `result`, observation time, safe `observed`/`expected` values, bounded `criterion` and declared `controls` |
| `evaluations_complete` | Exporter assertion about evaluation coverage, separate from inventory/issues |
| `scans[]` | Unique scan ID; typed target (`arm_resource`, `container_image`, `repository_commit`); status; start/end; tool version; policy ID; evaluated rules; result completeness/counts |

Safe values currently cover encryption enabled, logging enabled, key source, public-network access, minimum TLS, identity type, backup status and vulnerability/missing-patch counts. Types/enumerations are strict; unknown properties are rejected. Extend the allowlist only after reviewing actual native fields. Unknown/raw payloads and discovered secrets do not belong here.

Evaluation outcomes are PASS, FAIL, UNKNOWN, NOT_APPLICABLE or EXEMPT. They retain a source assertion, not an independently validated determination. Scan status is complete/partial/failed; `results_complete: true` requires a completed scan and a nonempty evaluated rule set. Image targets require a SHA-256 digest, repository targets a full commit hash. Scans do not establish deployed-resource linkage by themselves.

Use the same `wiz-import` command, then `evidence-report --wiz-import-id w-EXACT`. The new report preserves independent Azure/Wiz results and does not infer a pass from an empty issue list. It explicitly notes missing native-authentication proof and missing approved cross-source freshness criteria. The existing `wiz-reconcile` remains an inventory/issues comparison, not a v2 rule-equivalence engine. History/change records and native exception provenance are not implemented in v2.

## Normalized v1 contract (preserved)

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
