# Workplace deployment: Azure Functions, managed identity and retained Blob evidence

Version 0.3.2 supplies a Python v2 Functions application and optional Azure adapters. The [Linux/macOS workflow](https://github.com/csGIT34/auditevidencecollector/actions/workflows/offline.yml) validates offline behavior and builds. A [personal lab run](../infra/personal-lab/LIVE_VALIDATION.md) validated UAMI/Blob access, one RG collection and one PDF. v0.3.2 is now deployed, but the [follow-up investigation](../infra/personal-lab/DISPATCH_INVESTIGATION.md) reproduced HTTP 503 with minimal code. The app is stopped; workplace acceptance remains incomplete. macOS is for development/testing. Production runs in an Azure Function App without a workstation, interactive login, or running local terminal. The application never provisions infrastructure. Terraform is home-only; workplace patterns are supplied by the user.

The executable assessment remains scoped encryption at rest. The 215 proposed checks across 23 services and 20 NIST families in `docs/audit/` are applicability research, not newly implemented collectors. Provider-managed keys remain acceptable.

## Two operations

| Operation | Trigger and inputs | Successful outcome |
| --- | --- | --- |
| `CollectEvidence` | Timer, only registered when `CG_COLLECTION_SCHEDULE` is supplied; handler also requires `CG_COLLECTION_ENABLED=true`. Explicit subscriptions and identity required. | Verify subscription tenant metadata, collect, assess, archive a unique run. No automatic PDF. |
| `GenerateReport` | `POST /api/reports`, Functions `FUNCTION` key authorization, `CG_REPORT_ENABLED=true`, JSON body containing exactly `{"run_id":"r-<32 lowercase hex>"}`. | Load that exact completed run and archive a new PDF/report manifest. No ARM reads, recollection, reassessment or `latest` substitution. Response contains report/run IDs and the logical PDF key, not a SAS URL. |

Both operations start disabled. An absent schedule creates no timer binding; an enabled collection with a missing/invalid schedule fails configuration. No frequency or timezone preference has been chosen for the workplace. Numeric six-field NCRONTAB uses UTC; choose the cadence deliberately, including any daylight-saving implications. `run_on_startup=False`, `use_monitor=True`, and no function-level retry decorator. Microsoft's timer documentation describes runtime storage coordination and manual execution behavior: [timer trigger](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-timer).

The report endpoint uses a function key to prevent anonymous invocation. Before enabling it in production, configure the organization's inbound access restrictions/private access and App Service authentication for the approved work-tenant callers. Functions keys alone are shared secrets, not user identity or corporate authorization. Send a key through `x-functions-key`, never a query string, source file or log. Do not paste keys into this project or an LLM prompt. The platform must validate caller authentication; the code does not trust caller-supplied identity headers or decode JWTs. Test missing/wrong-key and unauthorized-user denials after deployment. Core Tools disables key authorization locally: bind development to localhost and never expose its port. [HTTP trigger authorization](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-http-webhook-trigger), [Functions security](https://learn.microsoft.com/en-us/azure/azure-functions/security-concepts).

This is a synchronous on-demand report operation. Measure PDF duration and memory on representative saved inventories before enabling it. HTTP response time is limited to about 230 seconds independently of the host timeout. If the supported workload cannot finish comfortably within that limit, an explicitly scoped asynchronous report design is required; this slice does not add a queue, database or Durable Functions. [Functions hosting limits](https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale).

## Source and configuration boundaries

| File/module | Responsibility |
| --- | --- |
| `function_app.py` | Trigger registration, POST input validation, safe HTTP response. |
| `azure_at_rest/hosting.py` | Strict settings, explicit operation selection, scoped tenant preflight, per-process overlap guard, safe invocation outcomes and dependency construction. |
| `azure_at_rest/azure_adapters.py` | Explicit credential factory, ARM SDK-credential wrapper, budget-aware ARM transport, Blob `ObjectStore`. |
| `azure_at_rest/workflow.py` | Shared assessment/digest logic and deterministic collect-assess-archive operation. |
| `azure_at_rest/archive.py` | Versioned facts, saved conclusions, context, exact historical selection and PDF publication. |
| `azure_at_rest/pdf_report.py` | In-memory PDF rendering; serialized per process to protect shared font state. |
| `host.json` | Functions v4-compatible host configuration; a 10-minute execution timeout. |
| `requirements.txt`, `constraints.txt` | Azure/PDF runtime packages and exact tested dependency versions. |
| `deploy/app-settings.example.json` | Empty workplace settings and disabled operations; not a deployable resource template. |
| `scripts/package_functions.py` | Allowlisted source ZIP, with no credentials, evidence or local virtual environment. Does not deploy. |

Use Python 3.12 on a supported Linux Functions host. Flex Consumption is the initial serverless option to evaluate; the workplace must choose an approved region/plan, networking, capacity and budget. The fixed ten-minute `host.json` limit is an application choice, not a claim that Functions plans all share that limit. Verify current platform constraints and extensions during deployment. [Python Functions reference](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python), [hosting options](https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale).

Use the user's existing infrastructure patterns and the [workplace runtime contract](WORKPLACE_RUNTIME_CONTRACT.md). Home-lab Terraform is not a workplace module.

## Required workplace inputs

Fill these settings in the approved deployment/configuration mechanism, not a committed file. All values in the checked-in example are empty or safe defaults.

| Setting | Meaning |
| --- | --- |
| `CG_TENANT_ID` | Work-tenant UUID, expected for every selected subscription. |
| `CG_MANAGED_IDENTITY_CLIENT_ID` | Client ID of the explicitly selected **user-assigned** managed identity attached to the Function App. Production has no automatic credential chain/system-identity fallback. |
| `CG_SUBSCRIPTION_IDS` | Nonempty comma-separated subscription UUIDs approved for collection. Optionally set `CG_RESOURCE_GROUP` to narrow to one RG in exactly one subscription. Do not enable for a broader scope than approved. |
| `CG_RESOURCE_GROUP` | Optional one-RG scope; requires exactly one subscription. Saved in inventory context; out-of-group resources are never hydrated. |
| `CG_EXECUTION_EXPIRES_AT` | Optional timezone-aware test-window end; rejects new enabled operations after expiry. Not a hard cancellation or cost cap. |
| `CG_EVIDENCE_ACCOUNT_URL` | Exact public-cloud endpoint `https://<account>.blob.core.windows.net`; no path, SAS, key, custom host or sovereign-cloud endpoint. Private DNS may resolve this normal hostname through an approved private endpoint. |
| `CG_EVIDENCE_CONTAINER` | Existing retained-evidence container; never auto-created. |
| `CG_EVIDENCE_PREFIX` | Optional portable key prefix; empty is allowed. No slash at either end. |
| `CG_RUNTIME_STORAGE_ACCOUNT` | Separate existing Functions runtime storage account name. It must differ from the retained-evidence account. |
| `AzureWebJobsStorage__accountName` | Same runtime account name, or use its explicit `__blobServiceUri` and the other service URIs required by your host. Code cross-checks the configured account/Blob URI. |
| `AzureWebJobsStorage__credential`, `AzureWebJobsStorage__clientId` | Runtime storage's identity configuration, separately reviewed from evidence permissions. Example uses `managedidentity` and an explicit client ID. |
| `CG_AUTH_MODE` | `managed_identity` in Azure. Production rejects a connection-string `AzureWebJobsStorage` and requires identity-based account/Blob settings. |
| `CG_COLLECTION_SCHEDULE` | Workplace-chosen six-field numeric UTC NCRONTAB. Empty means no timer. |
| `CG_COLLECTION_ENABLED`, `CG_REPORT_ENABLED` | Exact strings `true` or `false`; default false. Enable independently after their validation gates. |

Production SDK authentication requests tokens using the selected managed identity. `ArmCredential` adapts the SDK's scoped `AccessToken` result to the collector's existing `get_token() -> string` interface; the SDK handles caching and refresh. Before collection, authenticated ARM subscription GETs verify each subscription ID, `tenantId` and Enabled state against configuration. No unverified JWT claims are used. [ARM subscription metadata contract](https://learn.microsoft.com/en-us/rest/api/resources/subscriptions/get?view=rest-resources-2022-12-01). The configured client ID is recorded as configuration provenance, not as an independently measured principal identity. The deployment reviewer must verify the Function App's assigned identity and work tenant. Report generation relies on that deployed identity configuration and Blob authorization; it does not call ARM to revalidate historical data.

ARM collection needs the approved subscription/resource metadata reads described in [COLLECTION.md](COLLECTION.md); Reader is a possible built-in starting point, not a request to grant it automatically. Blob operations separately need read/list/create-write on the evidence container. Evaluate a custom role without deletion; built-in Blob Data Contributor includes delete. Runtime storage needs its own host/trigger permissions and service access, reviewed against the chosen Functions plan. Its coordination records, keys and deployment data must not be subjected to evidence retention locks. The adapter creates neither accounts nor containers and never grants permissions. [Functions connections and host storage](https://learn.microsoft.com/en-us/azure/azure-functions/manage-connections), [Blob Entra authorization](https://learn.microsoft.com/en-us/azure/storage/blobs/authorize-access-azure-active-directory).

The workplace must also supply package/source-intake policy, GitHub destination/visibility, network/DNS/proxy paths and owners, authorized PDF recipients, classification, retention/legal holds, logging/alert ownership, deployment approval and test/cost scope. Retention duration is undefined here; no immutable-storage policy is enabled or locked.

## Budgets, overlap, retry and failures

| Setting | Default / accepted range | Behavior |
| --- | --- | --- |
| `CG_COLLECTION_BUDGET_SECONDS` | 480 / 30–540 | Cooperative deadline checked around ARM calls, retries and pipeline stages. |
| `CG_REPORT_BUDGET_SECONDS` | 180 / 10–180 | Cooperative budget for saved-run reads and publication; checked after rendering. |
| `CG_ARM_RETRIES` | 2 / 0–3 | Retries of throttling/transient ARM failures. |
| `CG_BLOB_RETRIES` | 2 / 0–3 | Adapter retries; SDK automatic retries disabled for explicit reconciliation. |
| `CG_MAX_PAGES` | 1000 / 1–10000 | Per-list limit. Reaching it yields incomplete evidence, never a pass. |
| `CG_LOCK_WAIT_SECONDS` | 0 / 0–30 | Per-process wait for the operation lock; zero rejects overlap immediately. |

These budgets are **not hard cancellation guarantees**. An in-flight SDK call or PDF render can outlast a cooperative deadline. The Functions host enforces its execution timeout and can terminate a process without application cleanup. Collection is sequential, holds the selected inventory in memory, and has no checkpoint/resume; PDF generation loads a full run and builds the document in memory. The 34-resource fixture is not a production scale benchmark. Measure end-to-end latency and peak RSS for the approved scope and require headroom under both host and HTTP limits. Do not silently drop resources to fit.

Runtime timer monitoring coordinates the timer for one correctly configured Function App. The Python locks cover one process only; concurrent workers/apps and repeated HTTP requests can create distinct runs/reports. UUID keys and conditional writes prevent overwrites, not duplicate logical executions. No exactly-once claim or automatic retry of the whole audit is made. Choose one production collector deployment for a scope/schedule unless duplicated runs are intentional. A busy operation records `operation_busy`; HTTP returns 409, and the timer invocation fails visibly without an application retry policy. Increase bounded lock wait only after measuring the workload.

Every handler logs a safe invocation ID and started state; exceptions log a fixed stage/code without raw SDK responses, tokens, input bodies or configuration. Collection that archives FAIL/INCOMPLETE results returns a **completed invocation** with the findings/coverage summary. Configuration, tenant preflight, time-budget, storage and rendering failures remain execution failures. Monitor host failures and missing expected scheduled completions as well as audit findings. A process killed before `save_run` has no archive intent; Functions host logs are the recovery evidence. A completed manifest plus lost client acknowledgement is reconciled/inspected, never rewritten. Cleanup failure can leave a completed archive even though the host invocation reports failure; inspect by invocation ID in saved provenance before retrying.

## Blob preservation and historical reports

`BlobStore` uses BlockBlob upload with `overwrite=False` and `MatchConditions.IfMissing`; SDK wire tests verify `If-None-Match: *` on both a single PUT and multipart final block-list commit. Each put attempt has a random metadata marker and SHA-256. After an ambiguous response, only the same in-flight marker plus identical downloaded bytes can be accepted as successful. An unrelated existing blob remains a conflict even if its bytes match. Retries preserve the logical key and condition. Listing exhausts all pages or fails; denied/partial listings never become an empty successful inventory.

Committed partial attempt objects and failure records remain. The service controls the lifecycle of uncommitted upload blocks; those are not complete archive objects. Final manifests are last; failure markers take precedence. Failed marker writes cannot revoke a completion manifest already committed during an ambiguous response. Hash validation detects inconsistency, not an administrator replacing an entire archive. Blob storage alone does not establish WORM protection. [Blob upload API](https://learn.microsoft.com/python/api/azure-storage-blob/azure.storage.blob.blobclient), [conditional requests](https://learn.microsoft.com/en-us/rest/api/storageservices/specifying-conditional-headers-for-blob-service-operations).

The additive `execution_provenance` extension has its own schema `1.0` inside hashed saved context and PDF-generation metadata. Archive schema `1.0` and snapshot/assessment schemas are unchanged. Old runs without the extension still load and clearly disclose missing provenance. New hosted runs include configured identity, verified collection tenant, invocation ID and storage backend; PDFs retain original context and separately identify the current report-generation environment. Token values, account keys and local machine paths are excluded. PDF renderer version is 1.1; the original archived PDF remains the exact historical binary.

## Portable development and packaging

Follow [MACOS_DEVELOPMENT.md](MACOS_DEVELOPMENT.md). Install approved Python 3.12 and use a new virtual environment. `requirements-dev.txt` plus `constraints.txt` installs the complete test/build set, including JMESPath. `python scripts/validate.py` fails on any skipped test. The published `83b0711` passed [Linux/macOS CI](https://github.com/csGIT34/auditevidencecollector/actions/runs/35452053904), 105 tests each. This does not validate subsequent local commits or live Azure. Review GitHub Actions policy/minutes before enabling its runs.

ReportLab's licensed Vera fonts ship in its installed package and are embedded in PDFs. The application wheel includes `program_scope.json`; neither PDF generation nor Blob archiving needs a persistent local directory. Deploy installed dependencies built for **Linux**, never the Mac `.venv`. Dependency version pins are tested versions, not a claim of identical wheel bytes across operating systems or a vulnerability certification. Review package policy and refresh pins through the full gate.

`python scripts/package_functions.py --output dist/functions-source.zip` writes an allowlisted **source** archive: Functions entry point, host configuration, runtime requirements/constraints and application modules/data. It excludes documentation, examples, tests, local settings, credentials and outputs even if custom exports exist. A clean Linux dependency build is still required. Use your approved Functions remote-build/deployment workflow against the reviewed source package, or extract it on a clean Linux Python 3.12 build runner and install:

```sh
python -m pip install -r requirements.txt --target .python_packages/lib/site-packages
```

The final deployable package needs `host.json` at its root and the Linux dependency directory. Select the deployment method supported by the approved hosting plan; do not assume a ZIP deploy command works identically for every plan. Neither packaging command authenticates to Azure or deploys. Verify function indexing and required package data after the Linux build. The CLI remains available independently through `python -m azure_at_rest` or the installed console command.

## Workplace acceptance sequence

1. Review and transfer only the Git commit to the approved repository. Inspect staged files; ignore rules do not protect forced/manual uploads. Keep live evidence outside the source tree or under ignored `evidence/`/`output/` paths.
2. On the work Mac, run the complete offline gate, package build and fixture smoke test. Review the sample PDF; don't present it as tenant evidence.
3. For a separately authorized developer ARM smoke test, verify Azure public cloud, sign in with `az login --tenant WORK_TENANT_ID`, select the approved subscription with `az account set --subscription SUBSCRIPTION_ID`, inspect `az account show`, then use explicit CLI `--subscription` and a protected local `--store`. No role grants or new resources are implied.
4. Configure an approved existing nonproduction Function App, its explicit UAMI, runtime storage and separate evidence container through workplace change control. Review identity assignments, roles, network/DNS, package versions and endpoint caller restrictions before enabling either operation.
5. Verify hosted runtime indexing, denied caller behavior, one approved collection scope, tenant mismatch failure, conditional-write conflicts/lost responses, manifests, safe failure logging, prior-run preservation and exact-ID report generation. Use synthetic storage tests where practical and preserve test/real evidence separation. Record which results are mocks versus live checks.
6. Measure duration/memory, verify schedules and overlap behavior, assign alert/recovery/retention owners, then approve production rollout. Rollback disables the triggers or restores the previous code; it must never delete or overwrite retained evidence. No compliance certification follows from software test success.
