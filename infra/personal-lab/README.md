# Temporary personal Azure lab (Terraform only for home)

**Personal/home lab only.** See [LIVE_VALIDATION.md](LIVE_VALIDATION.md) for the bounded test and stopped infrastructure status. This configuration is exclusively for a personal test. Workplace infrastructure uses the user's existing patterns; see the tool-agnostic [workplace runtime contract](../../docs/WORKPLACE_RUNTIME_CONTRACT.md). Do not deploy this lab's network/access settings as a production default.

Read [COST.md](COST.md) first. A $25 total monthly bill is an acceptance condition, not an unlimited-spend authorization. An empty cost query is not a verified zero bill. Apply requires a separate review of the concrete plan, personal billing headroom, region/quota/policy and teardown arrangements. The user confirmed the $25 limit covers the entire personal bill, this subscription is intended for this project, and project-resource cleanup is authorized after successful workplace handoff. That is conditional future cleanup, not permission for deletion during preparation.

## Proposed topology and access

One new `rg-<lab_name>` in East US; one Python 3.12 Linux FC1 Function App; one explicitly attached UAMI; separate Standard LRS Hot runtime/evidence accounts, with deployment `package` and retained `evidence` containers. Host-created key/lease containers stay in runtime storage. There are no paid test databases, VMs, logging destinations or networking appliances. Sixteen Terraform resource instances are expected in the initial plan.

| Principal | Scope | Grant |
| --- | --- | --- |
| New UAMI | New lab RG only | Built-in Reader: inventory/detail GETs, not secret/action reads. |
| New UAMI | Subscription metadata only | Custom role: exactly `Microsoft.Resources/subscriptions/read`, required by authenticated tenant preflight. No subscription resource-list or whole-subscription Reader. |
| New UAMI | Runtime storage account only | Storage Blob Data Owner for host keys/leases and the package container. No queue/blob triggers or Durable Functions. |
| New UAMI | Evidence container only | Custom container read + blob read/write data actions. No delete/role management/key access. Write RBAC can technically replace a blob; conditional-create application logic additionally enforces no overwrite. No WORM claim. |
| Existing operator user | Evidence container only | Storage Blob Data Reader to inspect/download requested results using Entra login. No new operator identity or consent. |

Two custom role definitions and five role assignments are part of the future apply. The subscription metadata definition/assignment live outside the RG and must be removed through the same Terraform state during teardown. Creation requires an already-authorized operator with appropriate resource and RBAC-management rights. This configuration does not grant the operator general administrative rights.

Collection sets `CG_RESOURCE_GROUP` to the new RG and exactly one subscription. The collector uses `/subscriptions/S/resourceGroups/G/resources`, validates every returned resource's group before hydration and rejects pagination changing the scope. Children remain within that group; outside dependencies remain unresolved rather than being read. A denied/empty listing does not become full-subscription success. Existing subscription-wide behavior remains available when no group is supplied, but is not used in this lab.

The app and SCM endpoint use HTTPS and a **single explicit operator public IPv4 /32**, with unmatched traffic denied. HTTP report/probe routes require Functions keys. Basic SCM publishing credentials are disabled; deployment uses the operator's Entra authentication. The temporary personal test accepts this key plus IP boundary; it does not establish named corporate caller authorization. Workplace production still requires approved Entra/App Service authentication and network controls. Storage uses public service hostnames with Entra-only authorization, no shared keys and no anonymous blobs. The lab does not reproduce workplace private DNS/endpoints/firewalls or validate their behavior. A private-network lab would need a separately costed design.

AzureRM is pinned for RG, UAMI, plan and RBAC. AzAPI is pinned for storage/container/site/config resources because the reviewed AzureRM storage/site read implementations call `listKeys`/publishing-credential APIs; AzAPI metadata reads avoid those calls. Azure creates the SCM basic-publishing policy child with the app. `azapi_update_resource.basic_auth["scm"]` manages its `allow=false` property without trying to create or import that child. Removing the update resource does not re-enable basic authentication; deleting the parent app removes its policy. Provider registration is explicitly disabled. No `local-exec`, remote provisioner, app code deployment, external executable data source, policy change or automatic subscription registration is present.

## Phase 1: local checks and read-only preflight

Use Terraform **1.15.9**, Python 3.12 and an existing approved Azure CLI installation. Providers are pinned to AzureRM **5.6.0** and AzAPI **2.12.0**, with official checksums for Linux amd64 and Mac arm64/amd64. Do not upgrade without rerunning the gate.

From the repository root:

```sh
python -m pip install -r requirements-dev.txt
python -m pip install --no-build-isolation --no-deps -e .
python scripts/validate.py
terraform -chdir=infra/personal-lab init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/personal-lab fmt -check
terraform -chdir=infra/personal-lab validate
terraform -chdir=infra/personal-lab test
```

`init` downloads provider packages. `validate` checks configuration/provider schemas. `test` uses **mocked providers and plan-only runs**, with no Azure authentication or resources. Its "tearing down" message refers to mock test state. These checks do not prove Azure service acceptance or capacity.

Create a private directory **outside the checkout**, mode 700; use `umask 077`. Set `LAB_PRIVATE` to its absolute path. Copy `lab.tfvars.example` there as `lab.tfvars` and replace every placeholder. Set an explicit teardown timestamp within seven days of the future apply (prefer 24 hours). Terraform checks the timestamp at plan time; the app and lab probe reject new work after the configured expiry. This is not an automatic teardown, hard cancellation or storage-spend cap.

With the approved personal CLI context already selected, run:

```sh
python scripts/lab_preflight.py --subscription APPROVED_SUBSCRIPTION_UUID \
  --tenant APPROVED_TENANT_UUID --private-output "$LAB_PRIVATE/preflight"
```

The output directory must be new and outside the checkout. The script verifies cloud/tenant/subscription before reading metadata, cost/forecast, policies, Defender defaults, Flex locations and provider registrations. It never prints credentials and performs no mutations. Failed/throttled queries are saved as private errors; do not repeatedly hammer Cost Management. Interpret currency and actual/forecast periods separately. Review the current billing portal for total existing charges and commitments before using the estimate.

Review inherited policy definitions/parameters, including DeployIfNotExists/Modify and parent scopes, rather than just assignment names. Resolve any forced diagnostic export, paid Defender plan, denied region or MFA requirement with the owner; do not change policies to make the lab work. Current provider registration/permissions must be adequate without auto-registration. Microsoft.App may be required by the chosen Flex workflow even though this lab has no VNet; an unregistered provider is a review item, not permission to register it. Check Python 3.12 with `az functionapp list-flexconsumption-runtimes --location eastus --runtime python`. East US availability does not prove available Flex memory quota. Generic App Service VM usage limits are not Flex quota. Use the platform's Flex quota view/support if the subscription-specific quota cannot be read before creation; do not silently assume the documented default.

## Phase 2: private plan and review (still no creation)

Confirm `az group exists --name rg-YOUR_LAB_NAME` is false, the global account/app names are new, and the active account matches the approved tfvars. Never import or reuse unrelated personal resources for this lab.

```sh
terraform -chdir=infra/personal-lab init -input=false -lockfile=readonly \
  -backend-config="path=$LAB_PRIVATE/terraform.tfstate"
terraform -chdir=infra/personal-lab plan -input=false \
  -var-file="$LAB_PRIVATE/lab.tfvars" -out="$LAB_PRIVATE/create.tfplan" \
  > "$LAB_PRIVATE/create-plan.txt"
terraform -chdir=infra/personal-lab show -json "$LAB_PRIVATE/create.tfplan" \
  > "$LAB_PRIVATE/create-plan.json"
```

This real `plan` can read Azure using the selected operator. With the provider registration settings above, no resource creation/registration is intended. No real Azure-connected plan was executed during preparation. Inspect the plan privately: only the 16 declared new lab resources, no replacements/deletions, no unrelated IDs, no access keys, no paid extras, correct /32 and future expiry. Reconcile inherited changes outside Terraform and any unknown calculated fields. State/plan/outputs may contain identifiers and sensitive configuration; do not commit, paste into public issues or upload them. The lock file is the exception: it contains public checksums and is tracked.

**Stop here for the resource, role, network, billing and teardown review.** Creation/deployment/live tests below still need explicit authorization; the preparation request does not authorize them. Project-only cleanup is already authorized once successful workplace handoff, evidence preservation and exact scope checks are satisfied; do not request duplicate generic cleanup consent.

## Phase 3: future authorized creation and deployment

Apply only the reviewed plan, not an unreviewed new plan. Confirm its expiry is still future before applying. Do not use `-auto-approve`.

```sh
terraform -chdir=infra/personal-lab apply "$LAB_PRIVATE/create.tfplan"
terraform -chdir=infra/personal-lab output -json lab > "$LAB_PRIVATE/lab.json"
```

MFA/write-policy or RBAC-propagation failures are possible. Record safe error codes and inspect which resources exist before retrying. Never broaden roles to Owner or disable policies as a workaround. Inspect actual account kind/LRS/Hot, Entra-only access, UAMI attachment, role scopes, denied-by-default app/SCM access, zero always-ready and disabled settings. Stop if policy adds a billable component. No logs/workspace/Defender activation is included.

Build on Linux x86_64 Python 3.12, independent of a personal Mac virtual environment:

```sh
python scripts/build_functions_package.py --output "$LAB_PRIVATE/functions-lab.zip" --with-lab-probe
```

On an Apple Silicon Mac, use an approved x64 Linux build runner or a container explicitly configured with `--platform linux/amd64`; an ARM Linux container is rejected because its native wheels do not match the managed Functions x64 runtime. The builder combines the source allowlist with pinned Linux dependencies and a temporary lab probe. It never deploys. `--wheelhouse PATH` uses an approved local package cache with `--no-index`. The normal production source packager excludes all lab code/Terraform. Deploy a complete package through the supported Flex CLI path, using the private output's RG/app name and the existing Entra CLI session:

```sh
az functionapp deployment source config-zip --resource-group LAB_RG --name LAB_APP \
  --src "$LAB_PRIVATE/functions-lab.zip" --build-remote false --only-show-errors -o none
```

Current CLI should use Entra when basic publishing auth is disabled. If it attempts publishing-profile credentials or fails access restrictions, stop and diagnose the approved Entra/SCM route; do not enable basic auth. Do not directly upload the ZIP to Blob and call that a deployment. Do not set deprecated Flex settings such as `WEBSITE_RUN_FROM_PACKAGE`, `FUNCTIONS_WORKER_RUNTIME` or `SCM_DO_BUILD_DURING_DEPLOYMENT`. The pinned lab infrastructure uses `functionAppConfig` instead. [Flex deployment](https://learn.microsoft.com/en-us/azure/azure-functions/deployment-zip-push), [Flex settings](https://learn.microsoft.com/en-us/azure/azure-functions/functions-app-settings#flex-consumption-plan-deprecations).

Verify runtime indexing returns `GenerateReport` and `LabProbe`; no timer is expected with an empty schedule. Confirm actual host startup/storage access (SDK binding tests alone do not prove this). A successful deployment or SDK binding check alone is not proof of sustained runtime availability.

## Phase 4: bounded live acceptance

Record start/end UTC, invocation/run/report IDs, actual durations and private results. Limit the initial session to **two probes, two collections and three PDFs**, with no automatic retry of whole operations. Stop immediately on unexpected scope, leaked diagnostics, unknown billable extras or repeated failures. Keep test settings and outputs private. Set only the named lab app settings; never list/export arbitrary unrelated app secrets. App settings changes restart the host.

1. From the allowed /32, call the probe without a key (`scripts/lab_request.py --operation no-key`) and require rejection before handler work. Verify an outside-/32 request is denied without changing the allowlist (use an authorized alternate network only). A public request being rejected does not grant permission to expose a new public endpoint. Obtain the newly created lab function key through the approved operator channel only when live testing is authorized; do not read unrelated secrets, use query-string keys or print them. `lab_request.py` prompts with hidden input and puts the key only in a header, refuses redirects, makes one request and writes its response outside the checkout.
2. Temporarily set `CG_LAB_PROBE_ENABLED=true` on the lab app; leave collection/report disabled. Run one probe:

   ```sh
   python scripts/lab_request.py --url https://LAB_APP.azurewebsites.net \
     --operation probe --private-output "$LAB_PRIVATE/probe-1.json"
   ```

   Require HTTP 201 and all three pass fields. The host's selected UAMI obtains an ARM token, verifies authenticated subscription/tenant metadata, then creates one uniquely named **synthetic** blob, verifies a same-key second create conflicts, and checks original bytes/read/paged-list. It prints no token and never overwrites/deletes the probe or historical evidence. This proves successful UAMI use for these operations, not every possible denial. Inspect role metadata for no-delete/no-subscription-inventory grants; do not issue destructive delete probes. Disable the probe after at most two calls. The code also rejects an expired lab window.
3. Choose one explicit UTC calendar time **outside the short manual test session** (e.g. a day/month/hour within the seven-day window, never `* * * * * *`). Set that six-field `CG_COLLECTION_SCHEDULE` and `CG_COLLECTION_ENABLED=true`, leaving the expiry and `CG_RESOURCE_GROUP` unchanged. Verify `CollectEvidence` indexes. If ARM still lists stale trigger metadata after the app-settings restart, use the supported `POST .../sites/LAB_APP/syncfunctiontriggers?api-version=2024-04-01` action once for this exact lab app, then reread the function list; do not invoke an unindexed target. Manually trigger it once using `lab_request.py --operation collect` and the lab master key; this administrative key must stay in hidden input and is not used for normal reports. [Manual timer invocation](https://learn.microsoft.com/en-us/azure/azure-functions/functions-manually-run-non-http). Disable collection and clear the schedule immediately after completion; don't leave the future calendar trigger active. If any acknowledgement is lost, inspect manifests/invocation provenance before retrying.
4. Using the operator's container-scoped Data Reader and `az storage blob ... --auth-mode login`, list only the `lab/runs/` prefix, download that exact new run privately, verify completion and inspect every resource ID. They must all belong to the lab RG; no personal Key Vault contents or unrelated resource groups may appear. Preserve partial/error data if collection fails. Supported Storage rows may pass, while the app's workload coverage and unsupported resource types can remain UNKNOWN/UNSUPPORTED; an audit finding is not a host failure. Do not claim broad NIST coverage.
5. Set only `CG_REPORT_ENABLED=true`. Call `lab_request.py --operation report --run-id EXACT_R_ID` twice, with new private output filenames. Require distinct `p-...` IDs, the same exact saved run and unchanged original run-object hashes. Download each returned logical `pdf_key` using the evidence prefix from private `lab.json`; validate the manifest's SHA-256, open/render the PDF and confirm its RG scope, timestamp, findings and separate saved/generation provenance. Requesting `latest` or extra fields must fail; missing/wrong keys must fail. Never overwrite prior exports.
6. Optionally make the second allowed collection after recording the first run's hashes, then request the **older** run as the third allowed PDF. Confirm it retains older facts without recollection/reassessment. For tenant failure testing, an explicitly reviewed temporary wrong `CG_TENANT_ID` should fail preflight before archive writes; restore it immediately. For a permission-denial test, a reviewed nonexistent RG name may return 403/404 and must not fall back to subscription inventory; 404 alone is not proof of RBAC denial. Offline tests already prove scope-change rejection. Never grant subscription Reader merely to remove an expected denial.
7. Restore `CG_COLLECTION_ENABLED=false`, `CG_REPORT_ENABLED=false`, `CG_LAB_PROBE_ENABLED=false`, and `CG_COLLECTION_SCHEDULE=''`. Synchronize trigger metadata after clearing the schedule and verify no future timer binding remains. Check actual cost/usage and unexpected resources. Save results with exact code commit/provider versions and distinguish live observations from mocks. No long-running polling/scheduling is required.

`CG_EXECUTION_EXPIRES_AT` prevents new enabled collection/report work after the window, including manual admin calls; it does not kill an in-flight request. Probe expiry is separate. Host/HTTP/runtime storage costs can still exist after this application guard, so complete teardown.

## Phase 5: authorized project-only cleanup after successful workplace handoff

Once the workplace handoff has succeeded, disable all personal operations. Preserve the Git source/history and the selected test evidence first. With the user's artifact selection, use Entra read access to retain the selected run JSON/manifests and PDFs outside the repository, record hashes and verify the copies. Do not remove evidence merely because the test was successful; destroying both accounts permanently removes their contents. The lab has no legal hold or WORM policy.

Using **this lab's original private state**, produce and review a destroy plan. Never use subscription-wide deletes, a different workspace/state, broad wildcard resource commands, or import unrelated resources.

```sh
terraform -chdir=infra/personal-lab plan -destroy -input=false \
  -var-file="$LAB_PRIVATE/lab.tfvars" -out="$LAB_PRIVATE/destroy.tfplan" \
  > "$LAB_PRIVATE/destroy-plan.txt"
# After successful workplace handoff, verified evidence copies and exact project-only scope:
terraform -chdir=infra/personal-lab apply "$LAB_PRIVATE/destroy.tfplan"
```

Require the plan to contain only the 16 lab resources, including the **subscription-scoped metadata role definition and assignment**. Policy/MFA delete blocks must be resolved normally; don't disable security controls. Verify the RG/app/plan/both accounts/UAMI, five assignments and two role definitions are gone; compare existing-resource inventory to the private baseline. Confirm no diagnostic destination or other policy-created orphan remains. Recheck billing after metering delay and at the billing-period close. A missing RG is not proof of a zero outstanding bill.

Existing resources not created by this Terraform state (including any earlier Key Vault/UAMI) require an ownership/dependency assessment before eventual inclusion in project cleanup. Do not silently import/delete them or use a whole-subscription delete. The user's dedicated-subscription statement does not prove dependencies are absent. If handoff is not complete by the proposed seven-day deadline, disable the lab and review ongoing storage cost/lifetime; do not interpret expiry alone as permission to delete before the handoff condition.

The expiry tag is ownership metadata, not a scheduler. No budget alerts, outbound messages or automated delete jobs are created. Keep the lab disabled and do not extend its lifetime without a fresh cost and cleanup review.
