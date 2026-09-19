# Collection, permissions and evidence handling

## Permissions

An existing Azure **Reader** assignment covering the selected subscription resources normally supplies the management-plane `*/read` permissions used by this tool. The operator needs visibility of the selected subscriptions plus reads for resource inventory, supported resources, supported child lists, and TDE settings. Narrow custom roles can grant those read operations instead; test their actual permissions and review denied reads in the report. Cross-resource dependencies must also be visible within the selected inventory to resolve.

The tool does not create assignments or change RBAC. It does not require Key Vault data-plane permissions, Storage account keys/data-plane roles, Kubernetes credentials, SQL query credentials, application configuration listing actions or resource write actions. [Azure Reader role documentation](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/general#reader).

## HTTP operations

All cloud requests use GET against `https://management.azure.com`. There are no PUT/PATCH/POST/DELETE operations. The initial ARM endpoints are:

- `/subscriptions?api-version=2022-12-01` when subscription IDs are omitted.
- `/subscriptions/{id}/resources?api-version=2021-04-01` for each selected/discovered subscription.
- `/{resource-id}?api-version={catalogued-version}` for supported resource details, except justified non-data-store types.
- Supported child lists: SQL servers/managed instances `databases`, Synapse workspaces `sqlPools`, AKS `agentPools`, Event Hubs namespaces `eventhubs`, and App Service `slots`.
- Per-database `/transparentDataEncryption/current` for SQL/MI user databases and Synapse dedicated pools. SQL master is excluded from this mechanism.

The [ARM Resources List API](https://learn.microsoft.com/en-us/rest/api/resources/resources/list?view=rest-resources-2021-04-01) is a subscription inventory endpoint, **not a promise to enumerate every child/data-plane object**. Known child lists are paginated separately. Other children and exports are explicit coverage limits.

Pagination must stay on the exact ARM origin and initial collection path. Redirects, foreign-host links, subscription/path changes, malformed pages, repeated links and page limits produce errors. Successfully collected prior pages are retained. The default page limit is 1,000 per collection, adjustable with `--max-pages`; reaching it means incomplete evidence. Continuation tokens and URLs containing them are not saved.

Requests retry HTTP 429 and selected 5xx responses, plus network timeouts, up to three times. The per-attempt timeout is 30 seconds; waits are bounded. Reads are sequential to keep the initial implementation simple. A denied/missing resource remains an ERROR. A failed subscription list still produces a report with incomplete coverage. The collector never treats an authentication error as an empty successful subscription.

## Safe evidence

Only exact resource identity, selected kind/SKU/location, required encryption states, supported storage IDs, sanitized volume/node-pool metadata, timestamps and fixed error codes are persisted. Arbitrary tags, app settings, environment variables, passwords, connection strings, access keys, secret values, client secrets, tokens, provider error bodies, SAS URLs and full ARM responses are excluded.

The collector never calls `listKeys`, `listSecrets`, application-settings listing, Key Vault secret APIs, Kubernetes APIs or database/blob data APIs. Normal ARM resource GETs may themselves return incidental sensitive fields; those responses exist transiently in process memory and are projected before persistence. This is why storage mappings embedded in secret connection strings remain gaps rather than being extracted. Debugging should not add raw-response logging.

JSON, Markdown and optional snapshot files are written atomically with owner-only file permissions (`0600`). Outputs contain infrastructure identifiers and should be handled under your evidence retention/access policy. The default `evidence/` directory and credential-like files are ignored by Git. The committed fixture/report are synthetic.

## Interpretation of encryption evidence

A missing optional CMK field is not a failure and is never itself proof of encryption. For service-enforced rules, proof consists of a successful, matching resource GET identity plus a reviewed Microsoft guarantee for the exact type and assessed scope. Configurable mechanisms require explicit returned states. Unknown values and contradictory encryption flags do not become passes.

SQL TDE protector metadata on a server does not prove that its databases have TDE enabled. Each discovered user database is checked separately. SQL restore/copy history can preserve unencrypted states, so creation defaults are not used as proof. Kusto backing-storage encryption alone does not establish encryption of VM cache disks. ACR's CMK `disabled` field and managed disks' guest-ADE flags do not disable the underlying default service encryption.

Application and compute metadata can establish individual component observations while leaving workload storage unknown. AKS node-resource-group disk evidence and a host-encryption flag cannot establish PV/CSI/hostPath/emptyDir protection. Functions and Container Apps retain gaps for mounts, host/content storage, revisions and external stores. No attempt is made to fetch secret-bearing settings to close those gaps.

The assessment checks encryption confidentiality mechanisms, not the full SC-28 integrity requirement, organization-defined information coverage, algorithms/module certification in operation, key custody, access control, recovery ability or sustained operating effectiveness. SP 800-53A examination/test/interview procedures must be scoped and completed by the control owner.

## Verification boundary and no-charge constraint

Automated tests and the demo use local JSON fixtures only. They validate control flow, rules, source/scoping output, redaction, dependency gaps, pagination, CLI/report behavior and replay. They do not validate a real tenant's service responses, RBAC, API availability or inventory completeness.

A future authorized smoke test can run the CLI on the operator's local machine against existing subscription resources using metadata reads only. It requires no new Azure resource, hosted compute, diagnostic activation, service activation or application-data operation. Do not create sample resources for testing under the user's no-new-charges requirement. No personal credentials or live Azure tests were used in this implementation.

## Independent verification fields

Reports add `verification_guidance` at run level and `verification_commands` / `verification_notes` on each resource result. Commands are descriptions, not executed jobs. Each command has `kind`, `resource_id`, `relation` (self or dependency), `method`, `url`, `api_version`, `query`, `argv`, `command`, `shell`, `synthetic`, `verifies`, `expected_fields`, `interpretation`, `sources` and `paginated`.

SQL and MI TDE commands select `properties.state`; Synapse dedicated-pool TDE commands select `properties.status`. Other commands use selected catalogued fields. Current successful reads must be interpreted together with the original scope and any unresolved dependencies, not as automatic overrides of previous findings. Missing/invalid collected API metadata does not cause a guessed service endpoint. Resource IDs, API versions and request paths are validated before command construction; POSIX quoting is applied to every argument, with argv also retained.

The synthetic example and automated tests do not execute Azure commands. Offline command tests use a temporary fake `az` program to check shell argument boundaries. An optional local JMESPath test can run with an installed Azure CLI Python runtime to validate projection syntax/results without importing the Azure CLI, obtaining tokens or accessing Azure. Standard-library-only environments skip that optional parser check; all other tests remain dependency-free.
