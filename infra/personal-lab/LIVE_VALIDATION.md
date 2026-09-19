# Bounded personal Azure validation — 2026-09-19

**Partial live validation; repeated-request availability remains unresolved.** The personal Function App is stopped, collection/report/probe settings are false, the schedule is empty, and refreshed function metadata contains no timer. Evidence/storage and the 16 Terraform-managed instances remain for the authorized post-workplace-handoff cleanup. Personal identifiers, state, plans, billing responses and evidence are outside this public repository.

See the [follow-up dispatch investigation](DISPATCH_INVESTIGATION.md) for the minimal reproduction, temporary logging and packaging-permission fix. The original results below are historical.

## Exact versions and proof boundaries

- Original live-run deployment baseline: `1922cb78d47c3eca6594e9b391dfde98672f7670`, application v0.3.1 and PDF renderer 1.1. [Linux/macOS CI](https://github.com/csGIT34/auditevidencecollector/actions/runs/35454459202) passed 117 tests per OS, zero skips, plus builds.
- The deployed Linux x64 ZIP is 16,189,936 bytes, SHA-256 `44b023e1a909d15a6a6c094cbd1b8d8b2f95b6da6c41d25ae326df5032409bef`. Application bytes were compared with that commit before deployment. No corrected v0.3.2 package was deployed during that initial session; the follow-up investigation records its later deployment.
- Local corrected source: application v0.3.2, PDF renderer 1.2, unchanged assessment rule version. **120 tests passed, zero skips**, including RG verification scope and preservation of historical commands/bytes. [Publication CI](https://github.com/csGIT34/auditevidencecollector/actions/runs/35458109446) subsequently passed 120 tests per OS on Linux/macOS, zero skips, plus builds; that does not establish hosted availability.
- Terraform remains home-only. The SCM policy/casing fix passed schema/format validation and all four mocked plan tests. The reviewed live reconciliation changed only the existing SCM policy's `allow` property to false. Workplace infrastructure uses the user's existing patterns and the [runtime contract](../../docs/WORKPLACE_RUNTIME_CONTRACT.md).

## Observed live results

| Check | Observation |
| --- | --- |
| Deployment/host | Supported Flex ZIP deployment with remote build disabled completed. Python 3.12 host indexed the report/probe; the timer indexed after explicit trigger synchronization. No provider registration or quota increase was required. |
| Caller key | Missing and wrong function keys returned HTTP 401. |
| UAMI/Blob probe | One HTTP 201 probe validated authenticated ARM subscription/tenant metadata; synthetic Blob create/read/list succeeded; duplicate conditional create conflicted. |
| Collection | One manually invoked collection completed. All five resources were inside the selected new RG; inventory complete, zero collection errors. Results: PASS 2, NOT_APPLICABLE 1, UNKNOWN 1, UNSUPPORTED 1, overall INCOMPLETE. These are scoped encryption findings, not whole-control compliance. |
| Exact saved-run PDF | One HTTP 201 report created a separate completed publication from the exact saved run. PDF and source-object hashes were verified; original run bytes remained unchanged. The 20-page PDF was rendered and visually reviewed. |
| Repeat requests | A second report request returned plain HTTP 503 after about 60 seconds. No second report intent/publication appeared. A malformed `latest` request also received HTTP 503 before the expected application validation response. |
| Bounded recovery | One normal restart with operations disabled was followed by an expected HTTP 400 for `latest`; the next extra-fields request again returned plain HTTP 503 after about 60 seconds. No further work invocations were attempted. |
| Independent client control | With all operations disabled, a normal start, ARM Running readback and 15-second startup allowance were followed by two identical invalid `run_id=latest` requests through curl. The first returned HTTP 400 in 2.203 seconds; the second returned plain HTTP 503 in 60.097 seconds. The sequence ended immediately and the app was stopped in `finally`, with Stopped readback verified. No collection or report generation was invoked. |
| Final state | All flags false, empty schedule, no indexed timer, app Stopped, unchanged operator /32/default-deny app+SCM rules, SCM basic auth false, zero always-ready and max one instance per function group. Original pre-existing resources remain; no active subscription diagnostic setting or unexpected top-level lab resource was found. |

The HTTP 503 root cause is **not established**. Reproduction through curl shows the failure is not specific to the original urllib helper; the invalid-input control does not invoke evidence collection or PDF generation. An earlier control attempt reached the site before start propagation completed and returned a stopped-site HTTP 403; that attempt was inconclusive and is not authentication or network-denial evidence. A read-only host-status request returned Running, while available diagnostics lacked useful execution/heartbeat data and did not establish Python dispatch health. No speculative code, worker-count, quota, scale, networking or paid-logging change was made. A later, appropriately costed diagnostic session can be reviewed. Failed request status, timing and plain response body are preserved privately; response headers/correlation IDs were not captured by the initial request harness. The later curl control also preserved response headers privately.

## Defects found and fixed locally

1. Azure auto-creates the SCM basic-auth policy child. Creating it again caused the initial Terraform apply to stop. `azapi_update_resource` now manages that existing child on fresh deployments. A case-only service-plan ARM ID difference is normalized. An intermediate malformed ID was rejected by Azure; a regression now checks the complete planned ID and prevents doubled separators. The final corrected plan was independently reviewed before successful apply.
2. The original PDF's inventory verification suggestions for UAMI/plan used subscription-wide inventory URLs even though collection was RG-scoped. New assessments now generate RG-scoped inventory commands and identity-neutral scope limitations; subscription-wide collection behavior remains available. Historical runs/PDFs are deliberately not rewritten. The preserved original PDF retains this limitation: its two wider inventory suggestions should not be used with the lab's RG-only permission.
3. Two narrow PDF column headings are shortened to Ref/Code to avoid awkward wrapping. This is renderer 1.2; it does not change saved assessment criteria.

## Still unproven

Sustained/repeated HTTP handler availability; a second live collection and historical PDF after a newer run; successful rejection of extra report fields in this hosted session; an actual outside-/32 denial (external fetch produced no usable status); numeric subscription-specific Flex quota; workplace caller authentication/private DNS/network/retention and the actual work Mac. Offline tests cover several of these code paths but do not replace the missing hosted observations.

Storage capacity/transactions and any retained service can still incur charges. Capacity metrics had no populated measurements at the final check; known uploaded package size and preserved evidence bytes are recorded privately. The final Cost Management query was throttled, so no measured final bill is asserted. Earlier private billing evidence supported the bounded test; the [public cost model](COST.md) remains an estimate, not a hard cap. Do not treat empty or unavailable cost rows as zero. No budget alert or recurring automation was created.

The app stays stopped while the availability issue is unresolved. Preserve selected evidence/source, then use the original private state for project-only cleanup after successful workplace handoff. Existing Key Vault/UAMI ownership/dependencies require separate review before including them. Never use a subscription-wide delete.
