# Configuration and identity assessments

Source 0.17.0 includes **177 scoped predicates spanning all 23 program service entries**, alongside the existing encryption assessment. The predicates provide partial support for broader research objectives. They do not complete the 215-objective audit program. The [delivery register](audit/delivery-register.json) accounts for every objective and preserves its remaining acceptance boundary.

## Run the complete synthetic example

With the project's development dependencies installed:

```sh
python scripts/demo_controls.py --output /tmp/cloud-governance-control-demo
```

Use a new directory outside the checkout. The command collects synthetic ARM and Graph responses through the real adapters, evaluates explicit fictional criteria, archives the run and renders a self-contained PDF plus JSON/Markdown. It makes no Azure or Graph calls. The supplied case exercises every predicate: 168 expected PASS and one expected expired-credential FAIL. These are software test expectations, not a recommended security baseline or workplace approval.

The [example inputs](../examples/control-suite/) are reproducible HTTP fixtures and fictional criteria. They deliberately include secret canaries to verify projection; no real tenant IDs or credentials are present.

## Criteria

Pass `--criteria criteria.json` to `collect` or `assess`. Collection retains observations without criteria; absent or draft criteria leave results UNKNOWN. No default public-access, retention, authorization or recovery policy is invented.

```json
{
  "schema_version": "1.0",
  "id": "example-draft",
  "version": "1",
  "status": "draft",
  "checks": {
    "ST-https": {"operator": "equals", "value": true},
    "ST-tls": {"operator": "one_of", "value": ["TLS1_2"]},
    "LA-retention": {"operator": "at_least", "value": 90}
  }
}
```

This example is a draft, not an organizational requirement. `approved` records an operator assertion; the application does not independently authenticate approval. Criteria identity/version and the exact per-result criterion are frozen with each run. Accepted operations are typed `equals`, `one_of`, integer `at_least`, and `contains_all` for supported sets. TLS strings use explicit acceptable values, never lexicographic ordering. Diagnostic `category:` and `group:` tokens are distinct; the evaluator does not infer group membership or ingestion health.

Optional `overrides` maps **lowercase exact resource IDs** (or normalized `graph://tenant/collection/object` identities) to check criteria. A resource override wins over the shared check criterion; no wildcard or implicit exception is accepted. This supports different approved endpoint targets or application settings without applying one resource's criterion to another. Unknown check IDs, invalid types, duplicate JSON members and nonfinite numbers are rejected. Criteria input is bounded to 1 MiB.

## Azure Functions

Existing collection/report entry points now include configuration results. Set `CG_ASSESSMENT_CRITERIA_JSON` to the criteria JSON. `CG_GRAPH_ENABLED` defaults to `false`; set it to `true` only when tenant-wide Graph metadata collection is intended and its read permissions exist. The existing explicit tenant/UAMI and ARM subscription preflight remain required. Graph uses the same configured SDK identity with the Graph audience; no new identity or grants are created.

ARM reads include the registered exact-type root GETs, selected Web configuration/authentication/basic-publishing metadata, Blob service recovery metadata, diagnostic settings and UAMI federation metadata. No app-settings, connection-string, publishing-profile, listKeys, credential-value or workload execution endpoint is called. Resource-group scoping remains in force for ARM; **Graph scope is the configured tenant**, independent of that group.

Graph verifies `/organization?$select=id` against the configured tenant before listing applications/service principals. It retains separate object/app IDs, owner IDs, application credential key IDs/start/end dates and granted application role principal/resource/role IDs. Password values, certificate key material, names/email addresses and raw provider error bodies are excluded. Delegated consent grants include client/resource/principal IDs, consent type and scope claims. PIM, group expansion and effective access remain separate. Credential metadata requests can be throttled; partial pages and denials remain visible.

Review the minimum permissions for the actual authentication mode. For application authentication, application/owner/role metadata endpoints document `Application.Read.All`; tenant verification documents `Organization.Read.All`. The delegated-consent endpoint documents `Directory.Read.All`, which is broader and must already be authorized; a denial remains incomplete evidence. No read-write grants are required or created. These are separate from Azure ARM Reader and require workplace authorization/consent. Sources: [applications](https://learn.microsoft.com/en-us/graph/api/application-list?view=graph-rest-1.0), [owners](https://learn.microsoft.com/en-us/graph/api/application-list-owners?view=graph-rest-1.0), [service principals](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list?view=graph-rest-1.0), [application role grants](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-approleassignments?view=graph-rest-1.0), [organization](https://learn.microsoft.com/en-us/graph/api/organization-list?view=graph-rest-1.0). API definitions were reviewed on 2026-09-19; these new paths remain unverified against a live tenant in this release's local evidence.

Local live Graph opt-in is `collect --graph --tenant-id TENANT_UUID ...`; it requires the Azure SDK extra and a tenant-authorized Azure CLI sign-in. ARM tenant mismatch aborts before saving a combined run. Offline Graph uses `--fixture arm.json --graph-fixture graph.json --tenant-id TENANT_UUID`; live and fixture sources cannot be mixed.

## Results and compatibility

Encryption and configuration summaries are separate. The overall outcome includes both: configuration failures cannot be hidden by an encryption PASS. UNKNOWN, partial enumeration, missing criteria and failed reads cannot produce a positive configuration result. Archive completion means persistence succeeded, not that controls passed.

New snapshots, assessments and run archives use schema **1.1**; the new reader retains schema 1.0 historical support. Renderer **1.3** includes configuration findings, exact criteria, supporting objective/NIST references and safe Graph metadata. Historical generation reads frozen facts/results/context and does not apply current predicates. Old software rejects new-version archives instead of generating an encryption-only view that omits new findings.

Rollback: disable the new collector and restore the earlier deployment if needed; retain all archives. Use a 0.5.0-or-later reader to inspect 1.1 runs. No historical files are rewritten or migrated in place.

## Remaining control work

Coverage is scoped: Event Grid currently means custom topics, Managed Redis currently has a root TLS predicate, VMSS fields are model-level, and diagnostic settings are configuration rather than event-delivery proof. Container/guest operating evidence, effective privileges, additional service variants/children, backup populations and restore records, manual/inherited evidence workflows, native Wiz integration and workplace acceptance remain open. A candidate objective can require several of these facts together. Refer to the [full completion plan](PROJECT_COMPLETION_PLAN.md), [service backlog](audit/IMPLEMENTATION_BACKLOG.md) and delivery register rather than interpreting predicate count as objective completion.

## Executable predicate register

Each source links the exact API/property definition. Full scope appears in the saved report.

| Predicate | Research objective | Observed field / scope | API source |
| --- | --- | --- | --- |
| ST-public-network | ST-N | Account public network access configuration: `publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/2023-05-01/storageaccounts) |
| ST-anonymous-blob | ST-N | Account permission for anonymous blob access; container state is separate: `allowBlobPublicAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/2023-05-01/storageaccounts) |
| ST-shared-key | ST-I | Shared-key authorization configuration: `allowSharedKeyAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/2023-05-01/storageaccounts) |
| ST-https | ST-T | Secure transfer requirement: `supportsHttpsTrafficOnly` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/2023-05-01/storageaccounts) |
| ST-tls | ST-T | Minimum configured TLS version: `minimumTlsVersion` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/2023-05-01/storageaccounts) |
| ST-network-default | ST-N | Network ACL default action; exceptions require separate review: `networkAcls.defaultAction` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/2023-05-01/storageaccounts) |
| FUNC-https | FUNC-T | HTTPS-only configuration: `httpsOnly` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites) |
| FUNC-public-network | FUNC-N | Public network access configuration: `publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites) |
| FUNC-https-slot | FUNC-T | HTTPS-only configuration: `httpsOnly` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/slots) |
| FUNC-public-network-slot | FUNC-N | Public network access configuration: `publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/slots) |
| KV-rbac | KV-I | RBAC authorization model; actual assignments remain separate: `enableRbacAuthorization` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.keyvault/2023-07-01/vaults) |
| KV-public-network | KV-N | Public network access configuration: `publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.keyvault/2023-07-01/vaults) |
| KV-network-default | KV-N | Network ACL default action: `networkAcls.defaultAction` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.keyvault/2023-07-01/vaults) |
| KV-purge-protection | KV-B | Purge protection configuration: `enablePurgeProtection` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.keyvault/2023-07-01/vaults) |
| KV-soft-delete | KV-B | Soft delete configuration: `enableSoftDelete` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.keyvault/2023-07-01/vaults) |
| EH-local-auth | EH-I | Local authentication disabled setting: `disableLocalAuth` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.eventhub/2024-01-01/namespaces) |
| EH-public-network | EH-N | Public network access configuration: `publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.eventhub/2024-01-01/namespaces) |
| EH-tls | EH-T | Minimum configured TLS version: `minimumTlsVersion` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.eventhub/2024-01-01/namespaces) |
| COS-local-auth | COS-I | Key-based authentication disabled setting: `disableLocalAuth` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.documentdb/2024-05-15/databaseaccounts) |
| COS-public-network | COS-N | Public network access configuration: `publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.documentdb/2024-05-15/databaseaccounts) |
| COS-tls | COS-T | Minimum configured TLS version: `minimalTlsVersion` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.documentdb/2024-05-15/databaseaccounts) |
| ACR-admin-user | ACR-I | Registry admin account enabled setting: `adminUserEnabled` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.containerregistry/2023-07-01/registries) |
| ACR-public-network | ACR-N | Public network access configuration: `publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.containerregistry/2023-07-01/registries) |
| APPC-local-auth | APPC-I | Local authentication disabled setting: `disableLocalAuth` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.appconfiguration/2023-03-01/configurationstores) |
| APPC-public-network | APPC-N | Public network access configuration: `publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.appconfiguration/2023-03-01/configurationstores) |
| APPC-purge-protection | APPC-B | Purge protection configuration: `enablePurgeProtection` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.appconfiguration/2023-03-01/configurationstores) |
| LA-local-auth | LA-I | Local authentication disabled setting: `features.disableLocalAuth` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.operationalinsights/2023-09-01/workspaces) |
| LA-public-ingestion | LA-N | Public ingestion configuration: `publicNetworkAccessForIngestion` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.operationalinsights/2023-09-01/workspaces) |
| LA-public-query | LA-N | Public query configuration: `publicNetworkAccessForQuery` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.operationalinsights/2023-09-01/workspaces) |
| LA-retention | LA-L | Workspace default retention days; table overrides remain separate: `retentionInDays` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.operationalinsights/2023-09-01/workspaces) |
| AI-local-auth | AI-I | Local authentication disabled setting: `DisableLocalAuth` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.insights/2020-02-02/components) |
| AI-public-ingestion | AI-N | Public ingestion configuration: `publicNetworkAccessForIngestion` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.insights/2020-02-02/components) |
| AI-public-query | AI-N | Public query configuration: `publicNetworkAccessForQuery` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.insights/2020-02-02/components) |
| AKS-local-accounts | AKS-I | Local Kubernetes accounts disabled setting: `disableLocalAccounts` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.containerservice/2024-05-01/managedclusters) |
| AKS-rbac | AKS-I | Kubernetes RBAC enabled setting; bindings remain separate: `enableRBAC` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.containerservice/2024-05-01/managedclusters) |
| AKS-azure-rbac | AKS-I | Azure RBAC integration setting: `aadProfile.enableAzureRBAC` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.containerservice/2024-05-01/managedclusters) |
| AKS-private-api | AKS-N | Private control-plane configuration: `apiServerAccessProfile.enablePrivateCluster` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.containerservice/2024-05-01/managedclusters) |
| ACA-insecure-ingress | ACA-T | Insecure ingress allowed setting: `configuration.ingress.allowInsecure` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.app/2024-03-01/containerapps) |
| ACA-external-ingress | ACA-N | External ingress configuration; missing ingress is unassessed: `configuration.ingress.external` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.app/2024-03-01/containerapps) |
| PG-password-auth | PG-I | Password authentication configuration: `authConfig.passwordAuth` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.dbforpostgresql/2024-08-01/flexibleservers) |
| PG-entra-auth | PG-I | Entra authentication configuration: `authConfig.activeDirectoryAuth` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.dbforpostgresql/2024-08-01/flexibleservers) |
| PG-public-network | PG-N | Public network access configuration: `network.publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.dbforpostgresql/2024-08-01/flexibleservers) |
| PG-backup-retention | PG-B | Configured backup retention days; restore success remains separate: `backup.backupRetentionDays` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.dbforpostgresql/2024-08-01/flexibleservers) |
| REDIS-tls | REDIS-T | Minimum configured TLS version; database protocol remains separate: `minimumTlsVersion` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.cache/2024-02-01/redisenterprise) |
| AUTO-local-auth | AUTO-I | Local authentication disabled setting: `disableLocalAuth` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.automation/2023-11-01/automationaccounts) |
| AUTO-public-network | AUTO-N | Public network access configuration: `publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.automation/2023-11-01/automationaccounts) |
| GRAF-public-network | GRAF-N | Public network access configuration: `publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.dashboard/2023-09-01/grafana) |
| GRAF-zone-redundancy | GRAF-B | Zone redundancy configuration; availability testing remains separate: `zoneRedundancy` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.dashboard/2023-09-01/grafana) |
| PROM-public-network | PROM-N | Workspace public network configuration; collection endpoints remain separate: `publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.monitor/2023-04-03/accounts) |
| EG-local-auth | EG-I | Custom topic local authentication disabled setting: `disableLocalAuth` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.eventgrid/2022-06-15/topics) |
| EG-public-network | EG-N | Custom topic public network access configuration: `publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.eventgrid/2022-06-15/topics) |
| BV-backup-immutability | BV-B | Backup vault immutability configuration: `securitySettings.immutabilitySettings.state` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.dataprotection/2023-01-01/backupvaults) |
| BV-backup-soft-delete | BV-B | Backup vault soft delete configuration: `securitySettings.softDeleteSettings.state` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.dataprotection/2023-01-01/backupvaults) |
| BV-recovery-immutability | BV-B | Recovery Services vault immutability configuration: `securitySettings.immutabilitySettings.state` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.recoveryservices/2023-01-01/vaults) |
| BV-recovery-public-network | BV-N | Recovery Services vault public network configuration: `publicNetworkAccess` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.recoveryservices/2023-01-01/vaults) |
| FUNC-tls | FUNC-T | Minimum site TLS configuration: `minTlsVersion` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/config) |
| FUNC-scm-tls | FUNC-T | Minimum SCM TLS configuration: `scmMinTlsVersion` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/config) |
| FUNC-ftp | FUNC-T | FTP transport configuration: `ftpsState` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/config) |
| FUNC-remote-debugging | FUNC-C | Remote debugging enabled setting: `remoteDebuggingEnabled` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/config) |
| FUNC-auth-platform | FUNC-I | App Service authentication platform enabled setting: `platform.enabled` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/config) |
| FUNC-auth-required | FUNC-I | App Service authentication required setting; excluded paths and app authorization remain separate: `globalValidation.requireAuthentication` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/config) |
| FUNC-scm-basic-auth | FUNC-I | SCM basic publishing authentication allowed setting: `allow` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/basicpublishingcredentialspolicies) |
| FUNC-ftp-basic-auth | FUNC-I | FTP basic publishing authentication allowed setting: `allow` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/basicpublishingcredentialspolicies) |
| FUNC-tls-slot | FUNC-T | Minimum site TLS configuration: `minTlsVersion` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/slots/config) |
| FUNC-scm-tls-slot | FUNC-T | Minimum SCM TLS configuration: `scmMinTlsVersion` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/slots/config) |
| FUNC-ftp-slot | FUNC-T | FTP transport configuration: `ftpsState` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/slots/config) |
| FUNC-remote-debugging-slot | FUNC-C | Remote debugging enabled setting: `remoteDebuggingEnabled` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/slots/config) |
| FUNC-auth-platform-slot | FUNC-I | App Service authentication platform enabled setting: `platform.enabled` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/slots/config) |
| FUNC-auth-required-slot | FUNC-I | App Service authentication required setting; excluded paths and app authorization remain separate: `globalValidation.requireAuthentication` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/slots/config) |
| FUNC-scm-basic-auth-slot | FUNC-I | SCM basic publishing authentication allowed setting: `allow` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/slots/basicpublishingcredentialspolicies) |
| FUNC-ftp-basic-auth-slot | FUNC-I | FTP basic publishing authentication allowed setting: `allow` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/2023-12-01/sites/slots/basicpublishingcredentialspolicies) |
| ST-blob-soft-delete | ST-B | Blob soft delete configuration: `deleteRetentionPolicy.enabled` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/2023-05-01/storageaccounts/blobservices) |
| ST-container-soft-delete | ST-B | Container soft delete configuration: `containerDeleteRetentionPolicy.enabled` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/2023-05-01/storageaccounts/blobservices) |
| ST-blob-versioning | ST-B | Blob versioning configuration; capability depends on account kind: `isVersioningEnabled` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/2023-05-01/storageaccounts/blobservices) |
| ST-blob-restore | ST-B | Blob point-in-time restore configuration; restore test remains separate: `restorePolicy.enabled` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.storage/2023-05-01/storageaccounts/blobservices) |
| VM-linux-password-auth | VM-I | Linux password authentication disabled configuration; missing/other OS unassessed: `osProfile.linuxConfiguration.disablePasswordAuthentication` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.compute/2024-03-01/virtualmachines) |
| VM-secure-boot | VM-C | Secure Boot configuration; unsupported security types unassessed: `securityProfile.uefiSettings.secureBootEnabled` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.compute/2024-03-01/virtualmachines) |
| VM-vtpm | VM-C | Virtual TPM configuration; workload attestation remains separate: `securityProfile.uefiSettings.vTpmEnabled` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.compute/2024-03-01/virtualmachines) |
| VMSS-linux-password-auth | VMSS-I | Linux password authentication disabled configuration; missing/other OS unassessed: `virtualMachineProfile.osProfile.linuxConfiguration.disablePasswordAuthentication` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.compute/2024-03-01/virtualmachinescalesets) |
| VMSS-secure-boot | VMSS-C | Secure Boot configuration; unsupported security types unassessed: `virtualMachineProfile.securityProfile.uefiSettings.secureBootEnabled` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.compute/2024-03-01/virtualmachinescalesets) |
| VMSS-vtpm | VMSS-C | Virtual TPM configuration; workload attestation remains separate: `virtualMachineProfile.securityProfile.uefiSettings.vTpmEnabled` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.compute/2024-03-01/virtualmachinescalesets) |
| ACA-diagnostic-logs | ACA-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| APPC-diagnostic-logs | APPC-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| AUTO-diagnostic-logs | AUTO-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| REDIS-diagnostic-logs | REDIS-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| VM-diagnostic-logs | VM-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| VMSS-diagnostic-logs | VMSS-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| ACR-diagnostic-logs | ACR-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| AKS-diagnostic-logs | AKS-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| GRAF-diagnostic-logs | GRAF-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| BV-diagnostic-logs | BV-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| PG-diagnostic-logs | PG-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| COS-diagnostic-logs | COS-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| EG-diagnostic-logs | EG-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| EH-diagnostic-logs | EH-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| AI-diagnostic-logs | AI-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| KV-diagnostic-logs | KV-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| PROM-diagnostic-logs | PROM-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| LA-diagnostic-logs | LA-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| BV-diagnostic-logs-recovery | BV-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| ST-diagnostic-logs | ST-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| FUNC-diagnostic-logs | FUNC-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| FUNC-diagnostic-logs-slot | FUNC-L | Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence: `logs[].category/categoryGroup` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| PE-targets | PE-N | Declared private endpoint target IDs; reachability and public target restrictions remain separate: `privateLinkServiceConnections/manualPrivateLinkServiceConnections.privateLinkServiceId` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.network/2023-11-01/privateendpoints) |
| PE-approval | PE-N | Returned private endpoint connection approval states: `privateLinkServiceConnections/manualPrivateLinkServiceConnections.privateLinkServiceConnectionState.status` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.network/2023-11-01/privateendpoints) |
| PE-subresources | PE-N | Declared private endpoint subresource group IDs: `privateLinkServiceConnections/manualPrivateLinkServiceConnections.groupIds` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.network/2023-11-01/privateendpoints) |
| UAMI-federation-trust | UAMI-I | Exact federated issuer, subject and audience tuples compared with supplied approved trust configuration: `federatedIdentityCredentials[].issuer/subject/audiences` | [Definition](https://learn.microsoft.com/en-us/azure/templates/microsoft.managedidentity/2023-01-31/userassignedidentities/federatedidentitycredentials) |
| APPREG-audience | APPREG-I | Application sign-in audience configuration; actual consent and access remain separate: `signInAudience` | [Definition](https://learn.microsoft.com/en-us/graph/api/resources/application?view=graph-rest-1.0) |
| APPREG-owner-count | APPREG-I | Number of explicitly enumerated application owners; accountability review remains separate: `owners.count` | [Definition](https://learn.microsoft.com/en-us/graph/api/application-list-owners?view=graph-rest-1.0) |
| APPREG-expired-credentials | APPREG-K | Expired application password/key credential metadata count; no credential values are collected: `credentials.expiredCount` | [Definition](https://learn.microsoft.com/en-us/graph/api/resources/application?view=graph-rest-1.0) |
| APPREG-sp-enabled | APPREG-I | Related service-principal enabled configuration: `accountEnabled` | [Definition](https://learn.microsoft.com/en-us/graph/api/resources/serviceprincipal?view=graph-rest-1.0) |
| APPREG-role-grants | APPREG-I | Application role grant count; roles and target resource IDs remain preserved for owner review: `appRoleAssignments.count` | [Definition](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-approleassignments?view=graph-rest-1.0) |
| APPREG-approved-owners | APPREG-I | Exact application owner ID set compared with supplied approved owners: `owners[].id` | [Definition](https://learn.microsoft.com/en-us/graph/api/application-list-owners?view=graph-rest-1.0) |
| APPREG-approved-role-grants | APPREG-I | Exact granted application role tuples compared with supplied approved grants; delegated consent and effective user access remain separate: `appRoleAssignments[].principalId/resourceId/appRoleId` | [Definition](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-approleassignments?view=graph-rest-1.0) |
| APPREG-federation-trust | APPREG-I | Exact application federated trust tuples compared with supplied approved trust configuration: `federatedIdentityCredentials[].issuer/subject/audiences` | [Definition](https://learn.microsoft.com/en-us/graph/api/federatedidentitycredential-list?view=graph-rest-1.0) |

| APPREG-delegated-grants | APPREG-I | Exact delegated consent grants and scope claims; effective user access and consent review remain separate: `oauth2PermissionGrants[].clientId/resourceId/consentType/principalId/scope` | [Definition](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-oauth2permissiongrants?view=graph-rest-1.0) |
| ACA-approved-arm-grants | ACA-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| APPC-approved-arm-grants | APPC-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| AUTO-approved-arm-grants | AUTO-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| REDIS-approved-arm-grants | REDIS-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| VM-approved-arm-grants | VM-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| VMSS-approved-arm-grants | VMSS-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| ACR-approved-arm-grants | ACR-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| AKS-approved-arm-grants | AKS-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| GRAF-approved-arm-grants | GRAF-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| BV-approved-arm-grants | BV-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| PG-approved-arm-grants | PG-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| COS-approved-arm-grants | COS-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| EG-approved-arm-grants | EG-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| EH-approved-arm-grants | EH-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| AI-approved-arm-grants | AI-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| KV-approved-arm-grants | KV-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| UAMI-approved-arm-grants | UAMI-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| PROM-approved-arm-grants | PROM-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| PE-approved-arm-grants | PE-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| LA-approved-arm-grants | LA-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| BV-approved-arm-grants-recovery | BV-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| ST-approved-arm-grants | ST-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| FUNC-approved-arm-grants | FUNC-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |
| FUNC-approved-arm-grants-slot | FUNC-I | Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate: `assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256` | [Definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) |

| ACA-diagnostic-routes | ACA-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| APPC-diagnostic-routes | APPC-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| AUTO-diagnostic-routes | AUTO-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| REDIS-diagnostic-routes | REDIS-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| VM-diagnostic-routes | VM-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| VMSS-diagnostic-routes | VMSS-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| ACR-diagnostic-routes | ACR-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| AKS-diagnostic-routes | AKS-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| GRAF-diagnostic-routes | GRAF-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| BV-diagnostic-routes | BV-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| PG-diagnostic-routes | PG-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| COS-diagnostic-routes | COS-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| EG-diagnostic-routes | EG-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| EH-diagnostic-routes | EH-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| AI-diagnostic-routes | AI-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| KV-diagnostic-routes | KV-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| PROM-diagnostic-routes | PROM-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| LA-diagnostic-routes | LA-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| BV-diagnostic-routes-recovery | BV-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| ST-diagnostic-routes | ST-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| FUNC-diagnostic-routes | FUNC-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |
| FUNC-diagnostic-routes-slot | FUNC-L | Enabled audit categories bound to configured destinations; delivery and retention remain separate: `logs and destination IDs per diagnostic setting` | [Definition](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview) |

| BV-backup-population | BV-B | Backup instance source, policy and reported protection state; restore success remains separate: `backupInstances[].dataSourceInfo.resourceID/policyInfo.policyId/currentProtectionState/protectionStatus.status` | [Definition](https://learn.microsoft.com/en-us/rest/api/dataprotection/backup-instances/list?view=rest-dataprotection-2026-03-01) |
| BV-recovery-population | BV-B | Recovery Services protected source, policy and reported protection state; restore success remains separate: `backupProtectedItems[].sourceResourceId/policyId/protectionState/protectionStatus` | [Definition](https://learn.microsoft.com/en-us/rest/api/backup/backup-protected-items/list?view=rest-backup-2026-02-01) |

## Observation freshness

An approved or draft criteria document may include `max_observation_age_seconds`, an integer from 1 through 31,536,000. When supplied, each configuration result saves the assessment time, window and fresh/stale/future classification. Stale or future-dated observations remain UNKNOWN; read failures remain ERROR. The age boundary is inclusive. Without this field no freshness window is inferred. This applies to configuration predicates, not legacy encryption conclusions. Historical reports retain their original freshness assessment; they do not silently use the current clock. Reassess a snapshot explicitly to apply a later time or new criteria.

## ARM authorization and delegated consent

The resource authorization checks use [role assignments at scope](https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01) with `$filter=atScope()` and API `2022-04-01`, then resolve each [role definition](https://learn.microsoft.com/en-us/rest/api/authorization/role-definitions/get?view=rest-authorization-2022-04-01). Required ARM actions are `Microsoft.Authorization/roleAssignments/read` and `Microsoft.Authorization/roleDefinitions/read`. Both endpoints are addressed under the selected resource, preserving resource-group read boundaries. The response can contain inherited assignments from subscription, management-group or root scope. Management-group ancestry is reported by the filtered API, not independently reconstructed.

Each approved-set comparison preserves assignment/principal IDs, principal type, assignment scope, role ID/type, all four permission arrays, delegation target and a SHA-256 digest/version of any assignment condition. Conditions are not executed or interpreted and their text is not retained. Empty completed enumeration is distinguishable from denied, partial, duplicate or malformed evidence. Failed role-definition reads prevent PASS. Definitions are cached only within a collection run. A change to a custom role's actions can fail the comparison even if its role ID is unchanged.

Graph also reads [delegated consent](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-oauth2permissiongrants?view=graph-rest-1.0) per client service principal. `AllPrincipals` grants require a null principal; individual grants require an explicit principal UUID. Scope claims are sorted/deduplicated, but their case is preserved. Grants for another client, malformed claims, incomplete pages and denied reads cannot pass. Recent changes may be subject to Graph replication delay.

These checks establish a match against explicitly supplied approved grant sets. They do not calculate effective permissions: group membership, PIM eligibility/activation, deny assignments, condition semantics, resource-provider behavior and user entitlements still require additional evidence. Names, descriptions, secret values and raw error bodies are excluded.

## Diagnostic routing

Each diagnostic setting's enabled category/group tokens are compared together with that same setting's Log Analytics workspace, Storage account, Event Hub authorization-rule/name and marketplace-partner IDs. The optional workspace table mode is retained. This prevents a valid category on one setting and an approved destination on another from being combined into a false routing match. The route check reuses the existing paginated diagnostic list; it adds no network request.

IDs and supported types are validated; names/connection strings/keys are not requested. A route with enabled logs but no valid destination, duplicate setting, wrong parent identity, partial page or denied read remains incomplete. Disabled log routes are omitted. A complete empty route list is assessed only against explicit supplied criteria. Exact expected per-resource routes normally belong in criteria `overrides`.

These are routing configuration checks. They do not prove event arrival, destination retention, alert evaluation or effective destination permissions. The source is the same versioned [diagnostic-settings API](https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview).

## Backup protected populations

Both vault families now compare the explicitly expected protected-item population, source ARM IDs, backup-policy IDs and reported protection state/status. Data Protection uses `/backupInstances` API `2026-03-01`; Recovery Services uses `/backupProtectedItems` API `2026-02-01`. Collection uses read-only metadata endpoints under the selected vault, follows pagination and never follows source IDs into other resource groups. The associated role read actions are `Microsoft.DataProtection/backupVaults/backupInstances/read` and `Microsoft.RecoveryServices/vaults/backupProtectedItems/read`.

Use per-vault approved expected item tuples in criteria overrides. A missing expected item or changed state/policy produces FAIL when the listing is complete. Denied/partial lists, unknown states, missing fields, unexpected item identities and unsupported non-ARM data sources remain incomplete. Recovery Services item identifiers preserve required semicolon-delimited components. Full payloads, friendly names, datasource credentials and error descriptions are not retained.

This comparison proves the returned population/configuration matches the supplied expectation. It does not infer the required protected workload population, prove backup-job success, validate retention/RPO/RTO or prove restoration. Those require operating records and approved criteria. New API versions are locally fixture-tested, not live-verified.


### Actual Uniform VM scale-set instances

`VMSS-instance-models` reads the paginated `/virtualMachines` child collection using Compute API `2026-03-01` and compares exact `{instance_id, latest_model_applied}` tuples against supplied criteria. This detects a missing expected instance or model application drift even when the scale-set model itself has approved settings. It requires `Microsoft.Compute/virtualMachineScaleSets/virtualMachines/read`, in addition to the parent read. Only instance IDs and the reported boolean are retained; OS profiles, custom data and extension payloads are excluded.

The parent must explicitly identify `orchestrationMode: Uniform`. Flexible, missing or unreadable parent evidence remains unassessed. Duplicate IDs, wrong parents, missing/nonboolean model status, denied reads and incomplete pagination cannot pass. Empty populations pass only when explicitly expected by supplied criteria. Exact population criteria should be maintained for autoscaling environments. The provider's latest-model flag does not prove guest configuration, patch compliance or image safety.

API contract: [VM scale-set VM list](https://learn.microsoft.com/en-us/rest/api/compute/virtual-machine-scale-set-vms/list?view=rest-compute-2026-03-01).


### Container Apps revision images

`ACA-revision-images` reads the paginated `/revisions` collection with API `2026-01-01`. It compares exact revision IDs, active flags and named application/init-container image references with supplied criteria. Both active and inactive revisions are retained, so activation changes and historical revision population changes are explicit. Use `Microsoft.App/containerApps/revisions/read`. Collection never activates/deactivates a revision or pulls an image.

Only the image declaration, container name/kind and revision identity/active flag are retained. Environment variables, commands, arguments, volume contents, secrets and provisioning-error text are excluded. Missing init-container image metadata, malformed identities, duplicate revisions, incomplete pagination and denied reads cannot pass. Image references preserve their case. A tag remains a tag: collection does not resolve it to a running digest or claim scan, signature or vulnerability validation. Supply approved digest-pinned expectations when that is your policy. Exact population criteria must account for intentional revision churn.

API contract: [Container Apps revisions list](https://learn.microsoft.com/en-us/rest/api/resource-manager/containerapps/container-apps-revisions/list-revisions?view=rest-resource-manager-containerapps-2026-01-01).


### Backup and restore job outcomes

`BV-backup-jobs` and `BV-recovery-jobs` enumerate `/backupJobs` for Data Protection (`2026-03-01`) and Recovery Services (`2026-02-01`). They retain job IDs, operation category, status, start/end timestamps and, for Data Protection, the source ARM ID. Job error messages, extended property bags, URLs and credential-bearing payloads are excluded. Required reads are `Microsoft.DataProtection/backupVaults/backupJobs/read` and `Microsoft.RecoveryServices/vaults/backupJobs/read` respectively. No backup or restore is initiated.

For these checks, `recent_jobs` evaluates the latest-started matching job independently for each expected source and operation. Example draft criterion:

```json
{
  "operator": "recent_jobs",
  "value": {
    "scope": "sources",
    "source_ids": ["/subscriptions/11111111-1111-1111-1111-111111111111/resourcegroups/example/providers/microsoft.compute/disks/required"],
    "operation": "BackupAndRestore",
    "max_age_seconds": 86400
  }
}
```

Choose `Backup`, `Restore` or `BackupAndRestore`; the combined option requires both, so a backup cannot substitute for a restore. The duration is an operator-supplied criterion, not a built-in recommendation. Each latest job must have status `Completed` and an end time within the supplied window. Failed/cancelled/warning jobs, absent required jobs and stale completion fail. Unfinished or future-dated job evidence is UNKNOWN unless another required population already fails. Conflicting equal-start-time jobs cannot hide a failure. All supplied job evidence remains in the report. Missing end times on completed jobs, malformed timestamps, unknown statuses/operations, denied reads and truncated pagination cannot pass.

Recovery Services' common job response does not supply a reliable source ARM identity. Its `recent_jobs` criterion therefore requires `scope: "vault"` and `source_ids: []`. A vault result says only that the selected latest job(s) completed; it never establishes backup/restore coverage for every protected item. Data Protection also permits this explicit vault scope, or exact source-scoped populations. Jobs are limited to the provider-returned history; absence is a missing-evidence finding, not proof a job never ran. Successful restore-job status does not establish restored-data integrity, application consistency, RPO/RTO or exercise approval. Use operational evidence for those additional assertions.

The evaluation time and criterion are frozen in the assessment. Historical reports replay the saved result without reassessing recency today. Collection retains jobs even when no approved criterion is supplied.

API contracts: [Data Protection jobs](https://learn.microsoft.com/en-us/rest/api/dataprotection/jobs/list?view=rest-dataprotection-2026-03-01), [Recovery Services jobs](https://learn.microsoft.com/en-us/rest/api/backup/backup-jobs/list?view=rest-backup-2026-02-01).


### Container-level anonymous access

`ST-container-access` reads ARM `/blobServices/default/containers` with API `2023-05-01`, requiring `Microsoft.Storage/storageAccounts/blobServices/containers/read`. Only container IDs and `publicAccess` values (`None`, `Blob`, `Container`) are retained. User metadata, legal-hold identities/tags and blob contents are excluded. Special containers such as `$web` and `$root` are supported. This makes no data-plane requests and reads no account keys.

Use `{"operator":"allowed_access","value":["None"]}` to require that all returned containers declare private access, or supply another explicit sorted set of approved levels. `equals` can instead compare an exact container population. With approved `allowed_access` criteria, a complete empty listing satisfies the narrow absence-of-disallowed-declarations predicate; it does not establish data recovery, inventory ownership or service availability. Missing/draft criteria remain UNKNOWN. Missing flags, duplicate/wrong-scope identities, malformed rows and truncated/denied reads cannot pass. Account restrictions and container declarations are assessed independently: an account-level block does not hide a public container declaration, and a declared public level is not proof of actual network reachability.

API contract: [Blob containers list](https://learn.microsoft.com/en-us/rest/api/storagerp/blob-containers/list?view=rest-storagerp-2023-05-01).

Job-recency results additionally freeze the selected job IDs and outcome for each source/operation. Missing or unfinished required evidence keeps overall coverage incomplete even when a different required job fails. JSON, Markdown and PDF expose these saved decisions; no current-time reassessment occurs during historical rendering.

## Key Vault base-object lifecycle metadata (0.13.0)

`CG_VAULT_METADATA_ENABLED=true` opts the Functions ARM collection pipeline into data-plane LIST operations for discovered Key Vaults within its existing scope. It reuses the configured identity, deadline and retry budget. Disabled collection leaves the three observations missing/UNKNOWN. It does not grant permissions or provision resources.

`KV-keys-lifecycle`, `KV-secrets-lifecycle` and `KV-certificates-lifecycle` use data-plane API `2025-07-01`. The adapter verifies the vault URI returned by the hydrated ARM resource against the vault's expected public-cloud DNS name. It permits GET on `/keys`, `/secrets` and `/certificates` only, verifies same-vault/same-list pagination, rejects redirects, and never requests an object value, individual version, cryptographic operation or deleted-object recovery action. Private endpoints require working DNS/routing to the usual vault hostname. Managed HSM and sovereign-cloud endpoints are not implemented.

Projected fields are base object ID, enabled flag and integer `created`, `updated`, `nbf`, `exp` timestamps. Tags, content types, values, certificate bytes/thumbprints and key material are excluded. Do not interpret `updated` as key rotation. Lists do not establish every historical version or pending/deleted certificate population. The adapter caps responses at 4 MiB and each list at 10000 received items and the lower of the configured page limit or 400 pages. Malformed/duplicate identities, denied reads, pagination failures and missing attributes cannot yield an unsupported positive lifecycle result.

For each check, the approved policy may use:

```json
{
  "operator": "lifecycle",
  "value": {
    "enabled_only": true,
    "require_expiration": true,
    "min_remaining_seconds": 604800
  }
}
```

This illustrative criterion is not a workplace recommendation. It assesses expiration declarations, not effective usability. With `enabled_only`, known disabled objects remain visibly excluded; unknown enabled flags are UNKNOWN. Missing required expiration, already expired objects and insufficient remaining time FAIL. Future creation/update timestamps remain UNKNOWN. Empty or entirely excluded populations are UNKNOWN. An object failure can coexist with unknown coverage, and both remain in the saved per-object decisions and PDF. Criteria and `as_of` decisions are frozen on collection; historical reports do not reevaluate expiry at today's date. All three checks provide partial support for KV-K.

Access-policy vaults require the `list` permission for keys, secrets and certificates, without `get` of secrets or cryptographic permissions. For RBAC vaults, review a narrowly scoped metadata-read role; Microsoft's [Key Vault Reader definition](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/security#key-vault-reader) describes metadata access without sensitive values. Scope grants to the intended vaults and validate actual denials at work.

API contracts: [keys list](https://learn.microsoft.com/en-us/rest/api/keyvault/keys/get-keys/get-keys?view=rest-keyvault-keys-2025-07-01), [secrets list](https://learn.microsoft.com/en-us/rest/api/keyvault/secrets/get-secrets/get-secrets?view=rest-keyvault-secrets-2025-07-01), [certificates list](https://learn.microsoft.com/en-us/rest/api/keyvault/certificates/get-certificates/get-certificates?view=rest-keyvault-certificates-2025-07-01). Local fixtures exercise the path; live UAMI, firewall and API acceptance remain pending.

## Flexible scale-set membership (0.14.0)

`VMSS-instance-members` records `{orchestration, scope, members}` for the actual observed population. Uniform membership reuses the existing instance-model read and inherits its completeness. Flexible membership lists standard VMs in the selected subscription, or only the configured resource group, and matches `properties.virtualMachineScaleSet.id` to the exact parent. No name-pattern inference or numeric Uniform instance-ID assumption is used for Flexible VMs.

The read uses Compute API `2026-03-01` and requires VM read permission. Newly discovered matching VMs are hydrated through the existing bounded-scope collector; raw OS profiles, custom data and passwords are not saved. Unknown/malformed associations, duplicate VM IDs, denials, changed pagination scope and out-of-group identities keep membership partial. `scope` explicitly records `subscription`, `resource_group` or `scale_set`. Resource-group membership does not claim visibility outside that group.

Use an explicit `equals` criterion containing the approved orchestration/scope/member IDs. A complete empty listing only proves the reported population is empty; it cannot satisfy a nonempty approved baseline. Guest supplements expand Flexible parents from saved membership and mark absent guest records UNKNOWN. Flexible membership does not establish Uniform `latestModelApplied` semantics or guest drift, so the separate Uniform model predicate remains unassessed on Flexible sets.

Primary contracts: [subscription VM list](https://learn.microsoft.com/en-us/rest/api/compute/virtual-machines/list-all?view=rest-compute-2026-03-01), [resource-group VM list](https://learn.microsoft.com/en-us/rest/api/compute/virtual-machines/list?view=rest-compute-2026-03-01), [instance identities](https://learn.microsoft.com/en-us/azure/virtual-machine-scale-sets/virtual-machine-scale-sets-instance-ids). The implementation is fixture-tested; live Flexible responses and permissions remain workplace acceptance items.

## Automation runbooks, modules and runtime packages (0.15.0)

Three predicates extend the existing scoped ARM collector, all using API `2024-10-23`:

- `AUTO-runbooks-metadata` (AUTO-C): account runbook IDs, type, publication state, runtime-environment reference, progress/verbose logging booleans and modification timestamp.
- `AUTO-modules-metadata` (AUTO-V): classic account module IDs, declared version, provisioning state and modification timestamp.
- `AUTO-runtime-packages` (AUTO-V): runtime-environment IDs, language/version, default package declarations and each environment's separately listed imported package IDs, versions and provisioning states.

The collector only reads metadata list endpoints. It does not fetch runbook content, published/draft content links, parameter values, descriptions, identity names, credential/variable assets, certificate private keys, webhook URLs, job output or provider error messages. It does not start runbooks or import packages. Missing module/package versions and missing runtime declarations remain partial/UNKNOWN; the API's null version cannot become an approved version by assumption.

Runbook and classic-module criteria may use `asset_baseline` with an exact list of projected records excluding `last_modified`. This compares population and stable selected fields while retaining observed modification times separately. Module baseline versions must be non-null. Runbook criteria include `asset_id`, `runbook_type`, `state`, `runtime_environment`, `log_progress`, and `log_verbose`; module criteria include `asset_id`, `version`, and `provisioning_state`. A null runbook runtime reference is allowed for classic runbooks and does not establish their effective runtime version. Runtime/package criteria use `equals` against the complete projected environment/package list. All criteria require explicit approved policy; examples are test data.

A missing expected asset, unexpected asset, changed publication state, runtime reference or version fails an exact baseline. Denied/truncated listings, duplicate/wrong-parent IDs, malformed metadata and future modification times keep evidence incomplete. Empty complete listings can only match an explicitly empty approved population. Classic modules and runtime-environment packages are distinct inventories; neither substitutes for the other. Observed versions do not prove vulnerability-free code, support status, content integrity, signing, change approval, Hybrid Worker patching or job effectiveness. Runbook references are reported, not asserted to prove successful execution in that environment.

Reads require the corresponding scoped Automation runbook, module, runtime-environment and package read actions. Runtime collection is limited to 100 environments, 1000 imported packages per environment and 10000 imported packages total; pagination uses the configured limit and execution deadline. No additional role assignments or infrastructure are created. Actual permissions and service responses still need live workplace acceptance.

Contracts: [runbooks](https://learn.microsoft.com/en-us/rest/api/automation/runbook/list-by-automation-account?view=rest-automation-2024-10-23), [classic modules](https://learn.microsoft.com/en-us/rest/api/automation/module/list-by-automation-account?view=rest-automation-2024-10-23), [runtime environments](https://learn.microsoft.com/en-us/rest/api/automation/runtime-environments/list-by-automation-account?view=rest-automation-2024-10-23), [runtime packages](https://learn.microsoft.com/en-us/rest/api/automation/package/list-by-runtime-environment?view=rest-automation-2024-10-23).

## Log Analytics table retention (0.16.0)

`LA-table-retention` adds a read-only ARM `/tables` listing using API `2025-07-01`, requiring `Microsoft.OperationalInsights/workspaces/tables/read` at the selected workspace scope. It retains table ID, plan, returned retention/total/long-term days, inheritance flags and provisioning state. Schemas, search/restore query payloads, system identities and raw data are excluded. The list is paginated and bounded to 10,000 projected tables. This establishes declared configuration, not actual ingestion, event completeness, query access or retained-data availability.

Use an exact `equals` baseline or a `table_retention` criterion:

```json
{
  "operator": "table_retention",
  "value": {
    "allow_unlisted": false,
    "tables": [{
      "table_id": "/subscriptions/11111111-1111-1111-1111-111111111111/resourcegroups/example/providers/microsoft.operationalinsights/workspaces/logs/tables/audittable",
      "allowed_plans": ["Analytics"],
      "minimum_retention_days": 30,
      "minimum_total_days": 365
    }]
  }
}
```

These example thresholds are not approved organization policy. At least one required table is mandatory for this operator. Missing required tables, unapproved plans, short retention and extra tables when `allow_unlisted` is false produce FAIL after a complete valid listing. Allowing unlisted tables does not waive requirements for the named tables. Numeric returned retention values are assessed; a `-1` sentinel is retained as incomplete instead of assuming a workspace default. Missing fields, inconsistent totals/long-term values, unresolved defaults, unstable provisioning, duplicates or truncated lists remain incomplete; read errors stay visible. Missing/draft criteria remain UNKNOWN. Basic and Auxiliary plans are only accepted when explicitly included in the criterion; no feature equivalence with Analytics is inferred.

Reference: [Microsoft table list API and field definitions](https://learn.microsoft.com/en-us/rest/api/loganalytics/tables/list-by-workspace?view=rest-loganalytics-2025-07-01). This adapter is locally fixture-tested and has not been live-verified.

## Additional scoped encryption rules (0.17.0)

These use the existing encryption result path, separate from the 177 configurable predicates. A successful matching resource detail read and the linked provider guarantee support PASS only for the stated stored-data boundary. Denied/mismatched reads and transitional provisioning cannot pass. No asset content, variable values, credentials or job streams are fetched.

| Exact ARM type | Pinned detail API | Covered boundary and source | Explicit remaining boundary |
| --- | --- | --- | --- |
| Microsoft.Dashboard/grafana | 2023-09-01 | [Provider-managed Grafana metadata and instance user stores](https://learn.microsoft.com/en-us/azure/managed-grafana/encryption) | Data sources and external dashboard/snapshot exports |
| Microsoft.Monitor/accounts | 2023-04-03 | [Stored Prometheus workspace data](https://learn.microsoft.com/en-us/azure/azure-monitor/metrics/azure-monitor-workspace-overview) | Agent/source disks and external copies; no substitution with Log Analytics |
| Microsoft.Automation/automationAccounts | 2023-11-01 | [Secure assets, runbooks and DSC scripts](https://learn.microsoft.com/en-us/azure/automation/automation-secure-asset-encryption) | Unencrypted variables, output streams, worker disks and exports |

Existing resource metadata read permissions suffice for these rules. Provider-managed keys are accepted; optional CMK fields are not a base-encryption switch. These are documented service guarantees paired with resource observations, not cryptographic measurements or whole-objective acceptance. Native encrypted-variable populations and consumers require separate evidence. The new rules remain offline-tested rather than live-verified.
