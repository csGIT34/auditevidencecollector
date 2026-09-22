# Workplace handover: audit evidence collection

Updated 2026-09-22. This guide is the workplace starting point for the feature checkpoint on the 0.27.0 baseline. The home-lab build history is optional reference and does not need to be copied. Earlier release/live records describe their named versions, not this build. The copyable [workplace startup prompt](prompts/AZURE_ADAPTER_IMPLEMENTATION.md) needs no conversation history.

## Code and documentation together: recommended transfer

For a new work repo, use the **source bundle**, not the documentation-only ZIP:

```sh
python3 scripts/export_workplace_source.py --output /tmp/workplace-source.zip
```

This command runs in the prepared lab checkout. It exports current working files, including reviewed uncommitted handover changes; it does not fetch a remote revision. The manifest records the base commit, dirty status, source-file hashes and exported-file hashes. A remote clone of the last committed revision does not contain these new export tools until the cleanup is committed and transferred.

The bundle includes application code and packaged JSON, all existing tests, synthetic JSON fixtures, pinned dependency files, settings templates, packaging/rehearsal tools, catalog validation data and a short workplace README. It carries the six initial guides below plus `CONFIGURATION_ASSESSMENTS.md`, `KUBERNETES_EVIDENCE.md` and `GUEST_EVIDENCE.md`, which existing tests reference. Those additional guides are permission/feature contracts, not exploratory history. `scripts/lab_probe.py` remains solely to support existing safety tests; the normal Functions package excludes it. Never enable `--with-lab-probe` for work deployment.

Extract to a temporary staging directory, verify `WORKPLACE_SOURCE_MANIFEST.json` hashes, then import into a new project directory or merge into the work repo after checking path conflicts. Preserve existing work files and use the workplace's CI/infrastructure conventions. The bundle contains no `.git`, `.github`, `infra/`, research Markdown, historical status/reports, interview material or personal evidence/settings. Git commit ancestry is not required in the destination.

Run `python scripts/validate.py --workplace` in the imported source, followed by the synthetic rehearsal. This mode keeps every test and the zero-skip rule, catalog data/consistency checks, delivery-register checks and retained-document link checks. It omits only checks for lab research prose. Record the actual test count and result; do not reuse last night's passing result. Missing Python dependencies still need to be resolved in the workplace.

## Exactly which documents to copy

Copy only these **six documents**, keeping their relative paths. They are the initial workplace reading set:

| File | Purpose |
| --- | --- |
| `docs/WORKPLACE_AZURE_HANDOFF.md` | Scope, setup, workplace inputs and unfinished work; read first |
| `docs/prompts/AZURE_ADAPTER_IMPLEMENTATION.md` | Copyable prompt for the work session |
| `docs/WORKPLACE_RUNTIME_CONTRACT.md` | Runtime, identity and storage integration contract |
| `docs/AZURE_FUNCTIONS.md` | Detailed settings, packaging and host operations |
| `docs/EVIDENCE_REPORTS.md` | Full and selected report commands and HTTP contract |
| `docs/WIZ_INTEGRATION.md` | Normalized import boundary and native connector requirements |

From the lab checkout, create the documentation-only bundle:

```sh
python3 scripts/export_workplace_docs.py --output /tmp/workplace-docs.zip
```

Use a new output filename on repeat runs. Extract the bundle into a review/staging directory, then copy its `docs/` files into the work repo without overwriting unrelated work. `WORKPLACE_DOCS_MANIFEST.json` records the lab revision, whether the source working tree was dirty, and hashes of the exported documents. No Git ancestry is required in a separate work repo. Exported links to omitted local files become labelled plain-text references; do not fetch more lab documents just to follow those references.

**Leave in the lab:** `HOME_LAB_BUILD_STATUS.md`, `STATUS.md`, `CHANGELOG.md`, `HOME_LAB*`, `LOCAL_*`, historical `VALIDATION_*`, `MACOS_DEVELOPMENT.md`, `AZURE_POLICY_REVIEW.md`, `PROJECT_COMPLETION_PLAN.md`, `DELIVERY_REGISTER.md`, all research Markdown under `docs/audit/`, all `docs/reference/`, all `infra/personal-lab/`, and old prompts other than the startup prompt above. The lab root README is an overview of this larger repository; write the work repo's README around its own setup instead of copying it wholesale.

**Pull only when needed:** `AZURE_POLICY_EVIDENCE.md` for Policy integration; `CONFIGURATION_ASSESSMENTS.md` for criteria/Graph permissions; `CONTROL_REGISTER.md` and `PROGRAM_SCOPE.md` for tailoring; `OPERATIONAL_EVIDENCE.md`, `KUBERNETES_EVIDENCE.md`, or `GUEST_EVIDENCE.md` when enabling that source; `SAVED_RUN_COMPARISON.md` for comparisons; the independent validation prompt when planning rollout. These are task-specific references, not initial reading requirements.

### Source and test files are separate from reading material

The documentation ZIP is not runnable source or a deployment package. Transfer the implementation (`cloud_governance/`, `function_app.py`, `host.json`), dependency/build files, reviewed settings templates, tests, synthetic examples and relevant development/package scripts separately. Keep all packaged JSON files in `cloud_governance/`. Tests also consume `docs/schemas/wiz-evidence-v1.schema.json` and machine-readable catalogs under `docs/audit/`; those are test/build data, not exploratory reading.

The default lab gate reads research prose including `SERVICE_MATRIX.md`. The source bundle provides `python scripts/validate.py --workplace`: it uses `validate_catalog.py --data-only` to omit research-prose checks while retaining all catalog-data assertions and all tests. Document links are checked against the files actually retained. Use this explicit mode in the work repo; do not copy research prose to satisfy the default lab mode or silently skip failures. The original CI includes personal Terraform checks and is excluded; configure workplace CI around the workplace gate and approved infrastructure.

## Intended system

Collect audit evidence across all 20 NIST SP 800-53 Rev. 5 families and the 23-service program. Preserve good, bad, unknown, exempt and unassessed states, observations, periods, criteria, source coverage and provenance. A successful collection/report publication is independent of adverse findings. Evidence presence is not control satisfaction.

Use Azure Policy as the primary source of configuration evaluations, with direct ARM/Graph, workload/guest, Wiz and operating records supplying evidence that Policy cannot establish. Keep deterministic archives and reporting; no runtime LLM is required. The current collector still runs direct collection before adding Policy: making execution genuinely Policy-led remains an explicit implementation task.

Collection and reporting are separate. A report can cover the entire collected scope, controls/families, or a reviewed topic such as encryption at rest. Topics use explicit mappings; NIST labels or rule titles alone cannot prove equivalence. See [report commands and HTTP contract](EVIDENCE_REPORTS.md).

## Transfer and first work session

Transfer source, tests, public/synthetic examples and guides through the approved repository process. Exclude `.venv`, personal Azure configuration, evidence, Terraform state, credentials and caches. Preserve the exact source revision and constrained dependencies. Feature checkpoint: `519f8cadd666cc3ed4a0f09155bc7e222208e3b3`, committed 2026-09-21 at 23:30 EDT. The next commit, `d855930`, added interview notes only. Transfer a revision containing that feature checkpoint and this cleanup, and record `git rev-parse HEAD` at both ends. Cloning `c316078` alone omits the new features. Commit the reviewed cleanup before transferring with Git; uncommitted edits are not included in a clone or `git archive`.

1. Confirm source revision, Python 3.12 and approved package access. Use the setup commands below in the full source checkout; for a reduced work repo, first adapt the gate as described above. Required skipped tests fail the gate.
2. Run `python scripts/demo_audit_evidence.py --output ../audit-rehearsal-work` into a new private directory. Inspect `result.json`, the synthetic PDF and unchanged-source assertions. No Azure/Wiz access is needed.
3. Obtain the actual Wiz contract and samples listed below. Implement the native mapper at that boundary, feeding the tested importer. Reuse reporting, custody and reconciliation.
4. Review remaining Policy engineering gaps against workplace scope. The one-subscription lab path is not an estate-wide collector.
5. Prepare the Functions settings/package using actual workplace identity, network and storage inputs. Deploy and validate within the user's actual authorization; this guide does not provide guessed values or approvals.

### Fresh-machine setup

Run from the repository root in macOS, Linux or WSL with a POSIX filesystem. On Windows, prefer a checkout and private evidence directory in the WSL Linux filesystem; native Windows archive semantics are not supported. Use an approved Python 3.12 installation with pip/venv support and the approved package index. Do not relax `constraints.txt` to get installation to pass.

```sh
git status --short
git rev-parse HEAD
# Only for a clone retaining the lab Git history:
git merge-base --is-ancestor 519f8cadd666cc3ed4a0f09155bc7e222208e3b3 HEAD
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/validate.py --workplace
# This must be a NEW private directory outside the checkout.
python scripts/demo_audit_evidence.py --output ../audit-rehearsal-work
```

If pip/venv or pinned packages are unavailable, resolve the workstation/package-source prerequisite and record the gate as blocked. A source ZIP is not a dependency-complete deployment ZIP. Transfer tracked project files through the approved repository process, not a whole-directory copy. `.gitignore` is not a credential scanner. Personal lab records are historical reference; the [interview questions](reference/kubernetes-engineer-screening-questions.md) are unrelated reference material.

### Preparation check on 2026-09-22

The starting checkout was clean at `d855930`. On this WSL machine, Python 3.12.3 is available, but pip, ensurepip/venv support and ReportLab are missing. The full gate stopped at the dependency import; the rehearsal and packaged runtime were not rerun here. The 427-test/47-runtime-check results in the home checkpoint belong to the previous machine. Rerun acceptance in the work environment before relying on it. Local cleanup checks passed: 46 Markdown files with no missing relative-link targets, a 50-file allowlisted Functions source ZIP, and `git diff --check`. These do not replace the full gate or Linux runtime smoke test.

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
