# Workplace handover: audit evidence collection

Updated 2026-09-21. Start with [home-lab build status](HOME_LAB_BUILD_STATUS.md) for the tested source checkpoint on the 0.27.0 baseline. Earlier release/live records describe their named versions, not this build. The copyable [workplace startup prompt](prompts/AZURE_ADAPTER_IMPLEMENTATION.md) needs no conversation history.

## Intended system

Collect audit evidence across all 20 NIST SP 800-53 Rev. 5 families and the 23-service program. Preserve good, bad, unknown, exempt and unassessed states, observations, periods, criteria, source coverage and provenance. A successful collection/report publication is independent of adverse findings. Evidence presence is not control satisfaction.

Use Azure Policy as the primary source of configuration evaluations, with direct ARM/Graph, workload/guest, Wiz and operating records supplying evidence that Policy cannot establish. Keep deterministic archives and reporting; no runtime LLM is required. The current collector still runs direct collection before adding Policy: making execution genuinely Policy-led remains an explicit implementation task.

Collection and reporting are separate. A report can cover the entire collected scope, controls/families, or a reviewed topic such as encryption at rest. Topics use explicit mappings; NIST labels or rule titles alone cannot prove equivalence. See [report commands and HTTP contract](EVIDENCE_REPORTS.md).

## Transfer and first work session

Transfer source, tests, public/synthetic examples and guides through the approved repository process. Exclude `.venv`, personal Azure configuration, evidence, Terraform state, credentials and caches. Preserve the exact source revision and constrained dependencies. Use the revision containing the home-lab checkpoint; cloning the previous baseline alone omits these changes.

1. Confirm source revision, Python 3.12 and approved package access. Install `requirements-dev.txt` and run `python scripts/validate.py`. Required skipped tests fail the gate.
2. Run `python scripts/demo_audit_evidence.py --output ../audit-rehearsal-work` into a new private directory. Inspect `result.json`, the synthetic PDF and unchanged-source assertions. No Azure/Wiz access is needed.
3. Obtain the actual Wiz contract and samples listed below. Implement the native mapper at that boundary, feeding the tested importer. Reuse reporting, custody and reconciliation.
4. Review remaining Policy engineering gaps against workplace scope. The one-subscription lab path is not an estate-wide collector.
5. Prepare the Functions settings/package using actual workplace identity, network and storage inputs. Deploy and validate within the user's actual authorization; this guide does not provide guessed values or approvals.

Production remains Azure Functions with an explicitly selected attached UAMI and separate runtime/evidence Blob storage. Follow existing workplace infrastructure patterns and [runtime contract](WORKPLACE_RUNTIME_CONTRACT.md). `infra/personal-lab` is home-only. The new report uses the existing ObjectStore/host and adds no infrastructure.

Build on Linux x86_64 Python 3.12 with `scripts/build_functions_package.py`; `scripts/package_functions.py` alone includes no runtime dependencies. Test with `scripts/smoke_functions_runtime.py --package PATH --output NEW_PRIVATE_DIRECTORY --operational --workload --guest`. Exclude the lab probe and any Mac virtual environment.

## Workplace inputs

| Input | Needed for |
| --- | --- |
| Tenant, subscriptions/RG boundaries and full Policy assignment IDs, including inherited assignments | Exact population/authorization; one selected subscription/assignment per current Policy run |
| Tailoring, approved criteria/topic mappings, evidence owners and assessment periods | Applicable/missing/inherited evidence without inventing organizational policy |
| Attached UAMI/client ID, Function App plan/runtime, separate runtime/evidence accounts/container/prefix | Binding the host to workplace infrastructure |
| Network/private DNS, ARM/Graph/Blob read scopes, authenticated report callers | Source availability and protected evidence access; enabled Graph collection is tenant-wide |
| Cadence, freshness/skew limits, budgets, alert/recovery owners | Operating the collector and interpreting periods/staleness |
| Retention, classification, recipients and immutable-storage decisions | Custody; application hashes/create-only writes are not WORM certification |

Runtime coordination storage must stay separate from retained evidence storage. Configure work-tenant caller authentication and inbound restrictions in addition to Functions keys. Keep keys/tokens in approved secret mechanisms, not URLs/prompts/source. Local Functions key enforcement differs from the deployed host; use packaged runtime and workplace caller tests.

## Wiz connection: native boundary still required

The local v2 contract accepts safe observations, explicit rule evaluations including PASS/FAIL, issue lifecycle records and scan target/coverage records. It retains v1 imports. See [Wiz guide](WIZ_INTEGRATION.md), [synthetic v2 example](../examples/wiz/observations-export.json) and the authoritative `wiz_observations.py` validator.

At work obtain the documented endpoint/authentication method, granted read scopes, actual query/schema/export revision, project/cloud-account filters, installed CLI version and available scan formats. Obtain approved sanitized samples for inventory, positive/negative evaluations, issues, incomplete/failed scans and pagination/partial errors. Verify Audit History entitlement, retention and supported API/export access. Public product pages do not establish an authenticated GraphQL contract.

Preserve source IDs, actual timestamps, status meanings, target digests/commits and evaluated rule coverage. A resolved/rejected issue is not PASS; no issues is not a population of passing resources. A build scan is evidence about its target/time, not necessarily current deployment. Unavailable positive evidence remains unavailable. Exclude discovered secret values/snippets.

Acceptance: complete pagination; partial GraphQL responses never marked complete; throttling/authentication/denials tested; no name-only joins; exact ARM IDs and typed artifact identities; conflicts retained; source archives unchanged. Test sanitized native fixtures before a narrowly scoped authorized read-only live test.

## Remaining engineering and acceptance boundaries

These are unfinished features, not capabilities silently claimed complete or all blocked by credentials:

- **Policy-led execution and criteria context:** separate inventory/evaluation from optional direct supplements without breaking archives. Freeze evaluated definition/version, assignment/initiative parameters and overrides, exclusions/selectors, exemptions and attestation provenance. Current rows remain provider assertions with explicit missing-context limits.
- **Estate coverage/resilience:** one assignment/subscription and at most 5,000 retained Policy records per current run. Overflow is incomplete. Complete multi-subscription/assignment partitioning and a partial-source archive outcome after Policy denial; current denial fails before publication. Do not remove bounds or suppress failure to make a large run appear complete.
- **Combined supplements:** guest/Kubernetes have dedicated archived reports; merging those rows into the new selected view is unfinished. Generic organizational-objective evidence is not complete; operating records use the established objective contract.
- **Live acceptance:** verify real identity/RBAC, Policy continuation/inherited-assignment access, Blob/network/custody and report time/memory. No checkpoint/resume or exactly-once guarantee exists. Local tests do not establish these properties.

All 215 research objectives remain tracked as open/partial. Use [delivery register](DELIVERY_REGISTER.md) and [completion plan](PROJECT_COMPLETION_PLAN.md) for objective-level work. Do not re-research the entire project merely to connect Wiz; finish a concrete boundary task and its tests first.

## Report operations

`POST /api/evidence/reports` supports full/topic/family/control/resource selections and exact Wiz/operating import IDs. It uses `CG_REPORT_ENABLED`; successful publication returns 201 even with findings. `POST /api/reports` preserves the older exact-run PDF contract. Reads verify source hashes and never recollect Azure. See [request examples](EVIDENCE_REPORTS.md#azure-functions).

After successful handoff, handle personal evidence and lab teardown under the existing [lab guide](../infra/personal-lab/README.md). Nothing in this change started, stopped, deployed or deleted Azure resources.
