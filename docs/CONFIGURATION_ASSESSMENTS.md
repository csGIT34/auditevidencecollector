# Configuration and identity assessments

Source 0.5.0 adds **115 scoped predicates spanning all 23 program service entries**, alongside the existing encryption assessment. The predicates provide partial support for broader research objectives. They do not complete the 215-objective audit program. The [delivery register](audit/delivery-register.json) accounts for every objective and preserves its remaining acceptance boundary.

## Run the complete synthetic example

With the project's development dependencies installed:

```sh
python scripts/demo_controls.py --output /tmp/cloud-governance-control-demo
```

Use a new directory outside the checkout. The command collects synthetic ARM and Graph responses through the real adapters, evaluates explicit fictional criteria, archives the run and renders a self-contained PDF plus JSON/Markdown. It makes no Azure or Graph calls. The supplied case exercises every predicate: 114 expected PASS and one expected expired-credential FAIL. These are software test expectations, not a recommended security baseline or workplace approval.

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

Graph verifies `/organization?$select=id` against the configured tenant before listing applications/service principals. It retains separate object/app IDs, owner IDs, application credential key IDs/start/end dates and granted application role principal/resource/role IDs. Password values, certificate key material, names/email addresses and raw provider error bodies are excluded. It does not yet collect delegated consent, PIM, group expansion, effective access. Credential metadata requests can be throttled; partial pages and denials remain visible.

Review the minimum permissions for the actual authentication mode. For application authentication, the implemented Graph metadata endpoints document `Application.Read.All`; tenant verification documents `Organization.Read.All`. These are separate from Azure ARM Reader and require workplace authorization/consent. Sources: [applications](https://learn.microsoft.com/en-us/graph/api/application-list?view=graph-rest-1.0), [owners](https://learn.microsoft.com/en-us/graph/api/application-list-owners?view=graph-rest-1.0), [service principals](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list?view=graph-rest-1.0), [application role grants](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-approleassignments?view=graph-rest-1.0), [organization](https://learn.microsoft.com/en-us/graph/api/organization-list?view=graph-rest-1.0). API definitions were reviewed on 2026-09-19; these new paths remain unverified against a live tenant in this release's local evidence.

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

## Observation freshness

An approved or draft criteria document may include `max_observation_age_seconds`, an integer from 1 through 31,536,000. When supplied, each configuration result saves the assessment time, window and fresh/stale/future classification. Stale or future-dated observations remain UNKNOWN; read failures remain ERROR. The age boundary is inclusive. Without this field no freshness window is inferred. This applies to configuration predicates, not legacy encryption conclusions. Historical reports retain their original freshness assessment; they do not silently use the current clock. Reassess a snapshot explicitly to apply a later time or new criteria.
