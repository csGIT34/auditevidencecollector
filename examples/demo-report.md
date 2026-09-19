# Azure encryption-at-rest technical assessment

**Conclusion: FAILURES_FOUND**

Evidence mode: **offline_fixture**. Generated: 2026-09-19T02:39:32+00:00.
Collection: 2026-09-19T02:39:32+00:00 to 2026-09-19T02:39:32+00:00.
Rule version: 2026.09.19.1; tool version: 0.1.1.

Provider-managed keys are acceptable. PASS is limited to each resource's stated scope and evidence basis.
This is technical evidence, not RCSA certification or an assertion that every workload is encrypted.

## Inventory and coverage

Resources: 34. Inventory page traversal complete: True. Known child traversal complete: True. Coverage incomplete: True. Collection errors: 1.

| Result | Count |
| --- | ---: |
| PASS | 21 |
| FAIL | 3 |
| UNKNOWN | 7 |
| ERROR | 1 |
| UNSUPPORTED | 1 |
| NOT_APPLICABLE | 1 |

| Subscription | Listing complete | Pages | Items received |
| --- | --- | ---: | ---: |
| 11111111-1111-1111-1111-111111111111 | True | 2 | 29 |

Subscription discovery: {&quot;complete&quot;: true, &quot;items_received&quot;: 1, &quot;mode&quot;: &quot;accessible_in_current_tenant&quot;, &quot;pages&quot;: 1}

| ARM type | Results |
| --- | --- |
| Microsoft.App/containerApps | UNKNOWN: 1 |
| Microsoft.App/managedEnvironments | UNKNOWN: 1 |
| Microsoft.AppConfiguration/configurationStores | PASS: 1 |
| Microsoft.Cache/Redis | UNKNOWN: 1 |
| Microsoft.Cache/redisEnterprise | PASS: 1 |
| Microsoft.Compute/disks | PASS: 1 |
| Microsoft.Compute/images | PASS: 1 |
| Microsoft.Compute/snapshots | PASS: 1 |
| Microsoft.ContainerRegistry/registries | PASS: 1 |
| Microsoft.ContainerService/managedClusters | UNKNOWN: 1 |
| Microsoft.ContainerService/managedClusters/agentPools | UNKNOWN: 1 |
| Microsoft.DBforMySQL/flexibleServers | PASS: 1 |
| Microsoft.DBforPostgreSQL/flexibleServers | PASS: 1 |
| Microsoft.DataProtection/backupVaults | PASS: 1 |
| Microsoft.DocumentDB/databaseAccounts | PASS: 1 |
| Microsoft.DocumentDB/mongoClusters | PASS: 1 |
| Microsoft.EventHub/namespaces | PASS: 1 |
| Microsoft.EventHub/namespaces/eventhubs | PASS: 1 |
| Microsoft.Insights/components | PASS: 1 |
| Microsoft.KeyVault/vaults | PASS: 1 |
| Microsoft.Kusto/clusters | FAIL: 1 |
| Microsoft.Network/virtualNetworks | NOT_APPLICABLE: 1 |
| Microsoft.OperationalInsights/workspaces | PASS: 1 |
| Microsoft.RecoveryServices/vaults | PASS: 1 |
| Microsoft.Search/searchServices | PASS: 1 |
| Microsoft.ServiceBus/namespaces | PASS: 1 |
| Microsoft.Sql/servers | FAIL: 1 |
| Microsoft.Sql/servers/databases | FAIL: 1, PASS: 1 |
| Microsoft.Storage/storageAccounts | ERROR: 1, PASS: 1 |
| Microsoft.Web/sites | UNKNOWN: 1 |
| Microsoft.Web/sites/slots | UNKNOWN: 1 |
| MongoDB.Atlas/organizations | UNSUPPORTED: 1 |

Unsupported types: MongoDB.Atlas/organizations.

## Independent verification

Azure CLI installed; an authorized existing sign-in in the correct tenant and Azure public cloud; metadata read rights on each resource/subscription. Commands use POSIX shell quoting (sh/bash/zsh); JSON argv is available for other launchers.

Rerunning retrieves CURRENT state, not historical proof of the saved observation. Compare returned fields with the timestamped evidence; retain the original report separately.

Resource identity alone is not cryptographic proof. For mandatory encryption, combine a successful matching identity read with the linked Microsoft guarantee for the exact service, tier and stated scope. Missing optional CMK fields do not establish encryption.

Commands use management-plane GETs and selected metadata only. They do not provision resources, read application data, fetch secrets/keys, enable diagnostics or activate paid services. No command is executed while generating a report. Do not add --debug or remove the projection; normal ARM responses may contain incidental sensitive fields before CLI projection.

List commands display one page and a more_pages indicator. A missing match or empty first page is not proof of absence. If more_pages is true, independently traverse all pages using the current nextLink and verify its ARM origin and unchanged collection path. Saved continuation tokens are not emitted.

offline_fixture commands are SYNTHETIC EXAMPLES — DO NOT RUN. Demo IDs do not identify deployed resources. Only commands in an authorized live report target observed resources, and those may since have changed or been deleted.

[Azure CLI REST and query documentation](https://learn.microsoft.com/en-us/cli/azure/reference-index?view=azure-cli-latest#az-rest).

## Resource evidence

### UNKNOWN — app

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/containerApps/app

Type: Microsoft.App/containerApps; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: container-app / 2026.09.19.1; basis: backing_storage_required; API: 2024-03-01.

**Reason:** ARM metadata does not establish encryption for all workload storage. Review the explicit dependencies and gaps.

**Scope:** Declared environment and volume metadata only; mounted stores, revisions, ephemeral storage and application dependencies remain unverified.

Safe configuration evidence:

```json
{
  "managedEnvironmentId": "/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/managedEnvironments/apps-env",
  "volumes": [
    {
      "name": "data",
      "storageName": "shared-files",
      "storageType": "AzureFile"
    }
  ]
}
```

- Dependency (container_environment): /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/managedEnvironments/apps-env — UNKNOWN; resolved: True.
- Gap: Dependency container_environment is UNKNOWN: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/managedEnvironments/apps-env
- Gap: Declared environment and volume metadata only; mounted stores, revisions, ephemeral storage and application dependencies remain unverified.
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: UNKNOWN. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/containerApps/app?api-version=2024-03-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "managedEnvironmentId": properties."managedEnvironmentId", "environmentId": properties."environmentId", "volumes": properties.template.volumes[].{name: name, storageName: storageName, storageType: storageType}}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/containerApps/app&quot;, &quot;properties.managedEnvironmentId&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/managedEnvironments/apps-env&quot;, &quot;type&quot;: &quot;Microsoft.App/containerApps&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts).

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (container_environment)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/managedEnvironments/apps-env?api-version=2024-03-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/managedEnvironments/apps-env&quot;, &quot;type&quot;: &quot;Microsoft.App/managedEnvironments&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts).

### UNKNOWN — apps-env

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/managedEnvironments/apps-env

Type: Microsoft.App/managedEnvironments; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: container-env / 2026.09.19.1; basis: backing_storage_required; API: 2024-03-01.

**Reason:** ARM metadata does not establish encryption for all workload storage. Review the explicit dependencies and gaps.

**Scope:** Environment metadata only; file shares, logs, application volumes and revision storage need separate evidence.

Safe configuration evidence:

```json
{}
```

- Gap: Environment metadata only; file shares, logs, application volumes and revision storage need separate evidence.
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: UNKNOWN. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/managedEnvironments/apps-env?api-version=2024-03-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/managedEnvironments/apps-env&quot;, &quot;type&quot;: &quot;Microsoft.App/managedEnvironments&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts).

### PASS — configuration

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.AppConfiguration/configurationStores/configuration

Type: Microsoft.AppConfiguration/configurationStores; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: appconfig / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-03-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Sensitive configuration values stored within App Configuration; clients and linked stores excluded.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-app-configuration/concept-customer-managed-keys) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.AppConfiguration/configurationStores/configuration?api-version=2023-03-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.AppConfiguration/configurationStores/configuration&quot;, &quot;type&quot;: &quot;Microsoft.AppConfiguration/configurationStores&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-app-configuration/concept-customer-managed-keys).

### UNKNOWN — cache

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Cache/Redis/cache

Type: Microsoft.Cache/Redis; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: redis / 2026.09.19.1; basis: backing_storage_required; API: 2024-03-01.

**Reason:** Redis persistence flags do not establish the identity and encryption of every backing destination.

**Scope:** Premium RDB/AOF persistence destinations require verification; export, external and temporary copies excluded.

Safe configuration evidence:

```json
{
  "redisConfiguration.rdb-backup-enabled": "true"
}
```

- Gap: Persistence account identifiers are not available safely from this read without inspecting connection strings. Supply separate destination evidence; no secret/listKeys calls are made.
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/cache-how-to-premium-persistence) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: UNKNOWN. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Cache/Redis/cache?api-version=2024-03-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "redisConfiguration.rdb-backup-enabled": properties."redisConfiguration"."rdb-backup-enabled", "redisConfiguration.aof-backup-enabled": properties."redisConfiguration"."aof-backup-enabled"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Cache/Redis/cache&quot;, &quot;properties.redisConfiguration.rdb-backup-enabled&quot;: &quot;true&quot;, &quot;type&quot;: &quot;Microsoft.Cache/Redis&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/cache-how-to-premium-persistence).

### PASS — enterprise-cache

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Cache/redisEnterprise/enterprise-cache

Type: Microsoft.Cache/redisEnterprise; location: eastus; SKU: Enterprise_E10.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: redis-enterprise / 2026.09.19.1; basis: documented_service_guarantee; API: 2024-02-01.

**Reason:** The documented guarantee covers service disks and persistence with Microsoft-managed keys.

**Scope:** Enterprise and Enterprise Flash service disks and persistence only; newer Managed Redis SKUs need a separate rule.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/cache-how-to-premium-persistence) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Cache/redisEnterprise/enterprise-cache?api-version=2024-02-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Cache/redisEnterprise/enterprise-cache&quot;, &quot;sku.name&quot;: &quot;Enterprise_* or EnterpriseFlash_* (reviewed SKUs only)&quot;, &quot;type&quot;: &quot;Microsoft.Cache/redisEnterprise&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/cache-how-to-premium-persistence).

### PASS — image

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Compute/images/image

Type: Microsoft.Compute/images; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: disk-sse / 2026.09.19.1; basis: documented_service_guarantee; API: 2024-03-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Persisted managed disk, snapshot or managed image content; excludes VM temporary disks and caches.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/virtual-machines/disk-encryption) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Compute/images/image?api-version=2024-03-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "encryption.type": properties."encryption"."type", "storageProfile.osDiskId": properties.storageProfile.osDisk.managedDisk.id, "storageProfile.dataDiskIds": properties.storageProfile.dataDisks[].managedDisk.id, "virtualMachineProfile.storageProfile.osDiskId": properties.virtualMachineProfile.storageProfile.osDisk.managedDisk.id, "virtualMachineProfile.storageProfile.dataDiskIds": properties.virtualMachineProfile.storageProfile.dataDisks[].managedDisk.id}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Compute/images/image&quot;, &quot;type&quot;: &quot;Microsoft.Compute/images&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/virtual-machines/disk-encryption).

### PASS — snapshot

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Compute/snapshots/snapshot

Type: Microsoft.Compute/snapshots; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: disk-sse / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-10-02.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Persisted managed disk, snapshot or managed image content; excludes VM temporary disks and caches.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/virtual-machines/disk-encryption) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Compute/snapshots/snapshot?api-version=2023-10-02' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "encryption.type": properties."encryption"."type", "storageProfile.osDiskId": properties.storageProfile.osDisk.managedDisk.id, "storageProfile.dataDiskIds": properties.storageProfile.dataDisks[].managedDisk.id, "virtualMachineProfile.storageProfile.osDiskId": properties.virtualMachineProfile.storageProfile.osDisk.managedDisk.id, "virtualMachineProfile.storageProfile.dataDiskIds": properties.virtualMachineProfile.storageProfile.dataDisks[].managedDisk.id}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Compute/snapshots/snapshot&quot;, &quot;type&quot;: &quot;Microsoft.Compute/snapshots&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/virtual-machines/disk-encryption).

### PASS — registry

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerRegistry/registries/registry

Type: Microsoft.ContainerRegistry/registries; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: acr / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-07-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Registry images and artifacts; downloaded images and runtime writes excluded.

Safe configuration evidence:

```json
{
  "encryption.status": "disabled"
}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/container-registry/tutorial-customer-managed-keys) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerRegistry/registries/registry?api-version=2023-07-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "encryption.status": properties."encryption"."status"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerRegistry/registries/registry&quot;, &quot;properties.encryption.status&quot;: &quot;disabled&quot;, &quot;type&quot;: &quot;Microsoft.ContainerRegistry/registries&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/container-registry/tutorial-customer-managed-keys).

### UNKNOWN — aks

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks

Type: Microsoft.ContainerService/managedClusters; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: aks / 2026.09.19.1; basis: backing_storage_required; API: 2024-05-01.

**Reason:** ARM metadata does not establish encryption for all workload storage. Review the explicit dependencies and gaps.

**Scope:** ARM node-pool and node-resource-group evidence only; Kubernetes PVs, CSI drivers, emptyDir, hostPath, external stores and runtime workloads remain unverified.

Safe configuration evidence:

```json
{
  "agent_pools": [
    {
      "enableEncryptionAtHost": true,
      "name": "system",
      "osDiskType": "Ephemeral"
    }
  ],
  "nodeResourceGroup": "demo-nodes"
}
```

- Dependency (agentPools): /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks/agentPools/system — UNKNOWN; resolved: True.
- Dependency (node_resource_group_storage): /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/demo-nodes/providers/Microsoft.Compute/disks/node-disk — PASS; resolved: True.
- Gap: Dependency agentPools is UNKNOWN: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks/agentPools/system
- Gap: ARM node-pool and node-resource-group evidence only; Kubernetes PVs, CSI drivers, emptyDir, hostPath, external stores and runtime workloads remain unverified.
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/aks/concepts-storage) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: UNKNOWN. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks?api-version=2024-05-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "nodeResourceGroup": properties."nodeResourceGroup", "agent_pools": properties.agentPoolProfiles[].{name: name, osDiskType: osDiskType, enableEncryptionAtHost: enableEncryptionAtHost}}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks&quot;, &quot;properties.nodeResourceGroup&quot;: &quot;demo-nodes&quot;, &quot;type&quot;: &quot;Microsoft.ContainerService/managedClusters&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/aks/concepts-storage).

**SYNTHETIC EXAMPLE — DO NOT RUN / list_agentPools (self)**

Enumerate agentPools identities; separate child reads establish configuration.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks/agentPools?api-version=2024-05-01' --query '{"resources": value[].{id: id, type: type}, "more_pages": nextLink != `null` && nextLink != '"'"''"'"'}' --output json --only-show-errors
```

Expected / saved fields: {&quot;previously_observed_ids&quot;: [&quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks/agentPools/system&quot;]}

Traverse every page. A first page, resource count or identity list cannot prove encryption; run each child&#x27;s configuration commands. Missing children/read errors keep coverage incomplete.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/aks/concepts-storage).

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (agentPools)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks/agentPools/system?api-version=2024-05-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "enableEncryptionAtHost": properties."enableEncryptionAtHost", "osDiskType": properties."osDiskType", "osDiskSizeGB": properties."osDiskSizeGB"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks/agentPools/system&quot;, &quot;properties.enableEncryptionAtHost&quot;: true, &quot;properties.osDiskType&quot;: &quot;Ephemeral&quot;, &quot;type&quot;: &quot;Microsoft.ContainerService/managedClusters/agentPools&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/aks/enable-host-encryption).

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (node_resource_group_storage)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/demo-nodes/providers/Microsoft.Compute/disks/node-disk?api-version=2023-10-02' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "encryption.type": properties."encryption"."type", "storageProfile.osDiskId": properties.storageProfile.osDisk.managedDisk.id, "storageProfile.dataDiskIds": properties.storageProfile.dataDisks[].managedDisk.id, "virtualMachineProfile.storageProfile.osDiskId": properties.virtualMachineProfile.storageProfile.osDisk.managedDisk.id, "virtualMachineProfile.storageProfile.dataDiskIds": properties.virtualMachineProfile.storageProfile.dataDisks[].managedDisk.id}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/demo-nodes/providers/Microsoft.Compute/disks/node-disk&quot;, &quot;properties.encryption.type&quot;: &quot;EncryptionAtRestWithPlatformKey&quot;, &quot;type&quot;: &quot;Microsoft.Compute/disks&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/virtual-machines/disk-encryption).

### UNKNOWN — system

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks/agentPools/system

Type: Microsoft.ContainerService/managedClusters/agentPools; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: aks-pool / 2026.09.19.1; basis: backing_storage_required; API: 2024-05-01.

**Reason:** ARM metadata does not establish encryption for all workload storage. Review the explicit dependencies and gaps.

**Scope:** Node host-encryption configuration only; does not establish workload or persistent-volume protection.

Safe configuration evidence:

```json
{
  "enableEncryptionAtHost": true,
  "osDiskType": "Ephemeral"
}
```

- Gap: Node host-encryption configuration only; does not establish workload or persistent-volume protection.
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/aks/enable-host-encryption) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: UNKNOWN. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks/agentPools/system?api-version=2024-05-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "enableEncryptionAtHost": properties."enableEncryptionAtHost", "osDiskType": properties."osDiskType", "osDiskSizeGB": properties."osDiskSizeGB"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks/agentPools/system&quot;, &quot;properties.enableEncryptionAtHost&quot;: true, &quot;properties.osDiskType&quot;: &quot;Ephemeral&quot;, &quot;type&quot;: &quot;Microsoft.ContainerService/managedClusters/agentPools&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/aks/enable-host-encryption).

### PASS — backups

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DataProtection/backupVaults/backups

Type: Microsoft.DataProtection/backupVaults; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: backup / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-01-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Backup data stored in the Azure vault only; source workloads, operational snapshots, local agents and restore destinations require separate evidence.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/backup/encryption-at-rest-with-cmk-for-backup-vault) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DataProtection/backupVaults/backups?api-version=2023-01-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "encryption.infrastructureEncryption": properties."encryption"."infrastructureEncryption"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DataProtection/backupVaults/backups&quot;, &quot;type&quot;: &quot;Microsoft.DataProtection/backupVaults&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/backup/encryption-at-rest-with-cmk-for-backup-vault).

### PASS — mysql

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DBforMySQL/flexibleServers/mysql

Type: Microsoft.DBforMySQL/flexibleServers; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: mysql-flex / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-12-30.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Managed server data at rest; excludes customer exports and downstream stores.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/mysql/security/security-overview) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DBforMySQL/flexibleServers/mysql?api-version=2023-12-30' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "dataEncryption.type": properties."dataEncryption"."type"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DBforMySQL/flexibleServers/mysql&quot;, &quot;type&quot;: &quot;Microsoft.DBforMySQL/flexibleServers&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/mysql/security/security-overview).

### PASS — postgres

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DBforPostgreSQL/flexibleServers/postgres

Type: Microsoft.DBforPostgreSQL/flexibleServers; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: postgres-flex / 2026.09.19.1; basis: documented_service_guarantee; API: 2024-08-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Managed server databases, logs, temporary files and service backups.

Safe configuration evidence:

```json
{
  "dataEncryption.type": "SystemManaged"
}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/postgresql/security/security-data-encryption) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DBforPostgreSQL/flexibleServers/postgres?api-version=2024-08-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "dataEncryption.type": properties."dataEncryption"."type"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DBforPostgreSQL/flexibleServers/postgres&quot;, &quot;properties.dataEncryption.type&quot;: &quot;SystemManaged&quot;, &quot;type&quot;: &quot;Microsoft.DBforPostgreSQL/flexibleServers&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/postgresql/security/security-data-encryption).

### PASS — cosmos-mongo

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DocumentDB/databaseAccounts/cosmos-mongo

Type: Microsoft.DocumentDB/databaseAccounts; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: cosmos / 2026.09.19.1; basis: documented_service_guarantee; API: 2024-05-15.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Account databases, attachments and service backups, including the MongoDB API.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/database-encryption-at-rest) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DocumentDB/databaseAccounts/cosmos-mongo?api-version=2024-05-15' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DocumentDB/databaseAccounts/cosmos-mongo&quot;, &quot;type&quot;: &quot;Microsoft.DocumentDB/databaseAccounts&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/database-encryption-at-rest).

### PASS — mongo-vcore

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DocumentDB/mongoClusters/mongo-vcore

Type: Microsoft.DocumentDB/mongoClusters; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: documentdb-mongo / 2026.09.19.1; basis: documented_service_guarantee; API: 2024-07-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Azure DocumentDB (formerly Cosmos DB for MongoDB vCore) managed cluster data, logs, temporary files and backups; not MongoDB Atlas or self-hosted MongoDB.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/documentdb/database-encryption-at-rest) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DocumentDB/mongoClusters/mongo-vcore?api-version=2024-07-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "dataEncryption.type": properties."dataEncryption"."type"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DocumentDB/mongoClusters/mongo-vcore&quot;, &quot;type&quot;: &quot;Microsoft.DocumentDB/mongoClusters&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/documentdb/database-encryption-at-rest).

### PASS — events

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events

Type: Microsoft.EventHub/namespaces; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: eventhubs / 2026.09.19.1; basis: documented_service_guarantee; API: 2024-01-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Messages retained by Event Hubs; Capture destinations and consumer stores excluded.

Safe configuration evidence:

```json
{}
```

- Dependency (eventhubs): /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events/eventhubs/captured — PASS; resolved: True.
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/event-hubs/configure-customer-managed-key) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events?api-version=2024-01-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "encryption.keySource": properties."encryption"."keySource"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events&quot;, &quot;type&quot;: &quot;Microsoft.EventHub/namespaces&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/event-hubs/configure-customer-managed-key).

**SYNTHETIC EXAMPLE — DO NOT RUN / list_eventhubs (self)**

Enumerate eventhubs identities; separate child reads establish configuration.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events/eventhubs?api-version=2024-01-01' --query '{"resources": value[].{id: id, type: type}, "more_pages": nextLink != `null` && nextLink != '"'"''"'"'}' --output json --only-show-errors
```

Expected / saved fields: {&quot;previously_observed_ids&quot;: [&quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events/eventhubs/captured&quot;]}

Traverse every page. A first page, resource count or identity list cannot prove encryption; run each child&#x27;s configuration commands. Missing children/read errors keep coverage incomplete.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/event-hubs/configure-customer-managed-key).

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (eventhubs)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events/eventhubs/captured?api-version=2024-01-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "captureDescription.enabled": properties."captureDescription"."enabled", "captureDescription.destination.name": properties."captureDescription"."destination"."name", "captureDescription.destination.properties.storageAccountResourceId": properties."captureDescription"."destination"."properties"."storageAccountResourceId"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events/eventhubs/captured&quot;, &quot;properties.captureDescription.destination.name&quot;: &quot;EventHubArchive.AzureBlockBlob&quot;, &quot;properties.captureDescription.destination.properties.storageAccountResourceId&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/demostore&quot;, &quot;properties.captureDescription.enabled&quot;: true, &quot;type&quot;: &quot;Microsoft.EventHub/namespaces/eventhubs&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-capture-overview).

### PASS — captured

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events/eventhubs/captured

Type: Microsoft.EventHub/namespaces/eventhubs; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: eventhub-capture / 2026.09.19.1; basis: dependency_assessment_and_service_guarantee; API: 2024-01-01.

**Reason:** Namespace retained-message encryption and declared Capture configuration are substantiated.

**Scope:** Event Hub retained messages and declared Capture storage destination.

Safe configuration evidence:

```json
{
  "captureDescription.destination.name": "EventHubArchive.AzureBlockBlob",
  "captureDescription.destination.properties.storageAccountResourceId": "/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/demostore",
  "captureDescription.enabled": true
}
```

- Dependency (capture_storage): /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/demostore — PASS; resolved: True.
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-capture-overview) (reviewed 2026-09-19).
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/event-hubs/configure-customer-managed-key) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events/eventhubs/captured?api-version=2024-01-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "captureDescription.enabled": properties."captureDescription"."enabled", "captureDescription.destination.name": properties."captureDescription"."destination"."name", "captureDescription.destination.properties.storageAccountResourceId": properties."captureDescription"."destination"."properties"."storageAccountResourceId"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events/eventhubs/captured&quot;, &quot;properties.captureDescription.destination.name&quot;: &quot;EventHubArchive.AzureBlockBlob&quot;, &quot;properties.captureDescription.destination.properties.storageAccountResourceId&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/demostore&quot;, &quot;properties.captureDescription.enabled&quot;: true, &quot;type&quot;: &quot;Microsoft.EventHub/namespaces/eventhubs&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-capture-overview).

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (capture_storage)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/demostore?api-version=2023-05-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "encryption.keySource": properties."encryption"."keySource", "encryption.services.blob.enabled": properties."encryption"."services"."blob"."enabled", "encryption.services.file.enabled": properties."encryption"."services"."file"."enabled", "encryption.services.queue.enabled": properties."encryption"."services"."queue"."enabled", "encryption.services.table.enabled": properties."encryption"."services"."table"."enabled"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/demostore&quot;, &quot;properties.encryption.keySource&quot;: &quot;Microsoft.Storage&quot;, &quot;properties.encryption.services.blob.enabled&quot;: true, &quot;properties.encryption.services.file.enabled&quot;: true, &quot;type&quot;: &quot;Microsoft.Storage/storageAccounts&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/storage/common/storage-service-encryption).

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (owning_namespace)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events?api-version=2024-01-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "encryption.keySource": properties."encryption"."keySource"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events&quot;, &quot;type&quot;: &quot;Microsoft.EventHub/namespaces&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/event-hubs/configure-customer-managed-key).

### PASS — telemetry

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Insights/components/telemetry

Type: Microsoft.Insights/components; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: app-insights / 2026.09.19.1; basis: dependency_assessment; API: 2020-02-02.

**Reason:** The referenced Log Analytics workspace has positive encryption evidence for telemetry storage.

**Scope:** Workspace-backed telemetry only; classic Application Insights and exported copies unverified.

Safe configuration evidence:

```json
{
  "WorkspaceResourceId": "/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.OperationalInsights/workspaces/logs"
}
```

- Dependency (log_analytics_workspace): /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.OperationalInsights/workspaces/logs — PASS; resolved: True.
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/app/create-workspace-resource) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Insights/components/telemetry?api-version=2020-02-02' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "WorkspaceResourceId": properties."WorkspaceResourceId"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Insights/components/telemetry&quot;, &quot;properties.WorkspaceResourceId&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.OperationalInsights/workspaces/logs&quot;, &quot;type&quot;: &quot;Microsoft.Insights/components&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/app/create-workspace-resource).

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (log_analytics_workspace)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.OperationalInsights/workspaces/logs?api-version=2023-09-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.OperationalInsights/workspaces/logs&quot;, &quot;type&quot;: &quot;Microsoft.OperationalInsights/workspaces&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/customer-managed-keys).

### PASS — secrets

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.KeyVault/vaults/secrets

Type: Microsoft.KeyVault/vaults; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: keyvault / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-07-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Vault-managed secret values, including certificate private-key secret representations; cryptographic key objects, consuming services and backups outside the vault are excluded.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/key-vault/secrets/about-secrets) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.KeyVault/vaults/secrets?api-version=2023-07-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.KeyVault/vaults/secrets&quot;, &quot;type&quot;: &quot;Microsoft.KeyVault/vaults&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/key-vault/secrets/about-secrets).

### FAIL — analytics

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Kusto/clusters/analytics

Type: Microsoft.Kusto/clusters; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: kusto / 2026.09.19.1; basis: api_configuration; API: 2023-08-15.

**Reason:** VM cache disk encryption is explicitly disabled; backing-storage encryption alone does not cover it.

**Scope:** Cluster backing storage and VM cache disks; external tables and exports excluded.

Safe configuration evidence:

```json
{
  "enableDiskEncryption": false
}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/data-explorer/cluster-encryption-overview) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: FAIL. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Kusto/clusters/analytics?api-version=2023-08-15' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "enableDiskEncryption": properties."enableDiskEncryption"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Kusto/clusters/analytics&quot;, &quot;properties.enableDiskEncryption&quot;: false, &quot;type&quot;: &quot;Microsoft.Kusto/clusters&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. properties.enableDiskEncryption must be true for the VM cache check; false is a failure, missing is unknown. The linked guarantee covers backing storage separately.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/data-explorer/cluster-encryption-overview).

### NOT_APPLICABLE — network

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Network/virtualNetworks/network

Type: Microsoft.Network/virtualNetworks; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: non-data-plane / 2026.09.19.1; basis: justified_applicability; API: None.

**Reason:** Resource is a networking or identity construct, not a customer data-at-rest store in this assessment. Network controls and diagnostic destinations are separate responsibilities.

**Scope:** Resource is a networking or identity construct, not a customer data-at-rest store in this assessment. Network controls and diagnostic destinations are separate responsibilities.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/security/fundamentals/shared-responsibility) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: NOT_APPLICABLE. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / inventory_lookup (self)**

Locate this resource&#x27;s identity in subscription inventory.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resources?api-version=2021-04-01' --query '{"matches": value[?id == '"'"'/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Network/virtualNetworks/network'"'"'].{id: id, type: type, location: location}, "more_pages": nextLink != `null` && nextLink != '"'"''"'"'}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Network/virtualNetworks/network&quot;, &quot;type&quot;: &quot;Microsoft.Network/virtualNetworks&quot;}

Identity only; no service-specific encryption verification is available from this command. Follow all pages; an absent match is inconclusive. Unsupported or not-applicable status is not a PASS.


### PASS — logs

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.OperationalInsights/workspaces/logs

Type: Microsoft.OperationalInsights/workspaces; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: logs / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-09-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Workspace data and saved queries inside Azure Monitor; exports excluded.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/customer-managed-keys) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.OperationalInsights/workspaces/logs?api-version=2023-09-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.OperationalInsights/workspaces/logs&quot;, &quot;type&quot;: &quot;Microsoft.OperationalInsights/workspaces&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/customer-managed-keys).

### PASS — recovery

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.RecoveryServices/vaults/recovery

Type: Microsoft.RecoveryServices/vaults; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: backup / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-01-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Backup data stored in the Azure vault only; source workloads, operational snapshots, local agents and restore destinations require separate evidence.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/backup/backup-encryption) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.RecoveryServices/vaults/recovery?api-version=2023-01-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "encryption.infrastructureEncryption": properties."encryption"."infrastructureEncryption"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.RecoveryServices/vaults/recovery&quot;, &quot;type&quot;: &quot;Microsoft.RecoveryServices/vaults&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/backup/backup-encryption).

### PASS — search

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Search/searchServices/search

Type: Microsoft.Search/searchServices; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: search / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-11-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Search indexes, synonym maps and object definitions, on data and temporary disks; sources and enrichment dependencies excluded.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/search/search-security-built-in) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Search/searchServices/search?api-version=2023-11-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Search/searchServices/search&quot;, &quot;type&quot;: &quot;Microsoft.Search/searchServices&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/search/search-security-built-in).

### PASS — messages

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ServiceBus/namespaces/messages

Type: Microsoft.ServiceBus/namespaces; location: eastus; SKU: Premium.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: servicebus / 2026.09.19.1; basis: documented_service_guarantee; API: 2024-01-01.

**Reason:** Verified Premium resource identity is covered by the service-enforced encryption guarantee.

**Scope:** Premium namespace retained messages; other tiers need a separately substantiated guarantee.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/service-bus-messaging/configure-customer-managed-key) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ServiceBus/namespaces/messages?api-version=2024-01-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "encryption.keySource": properties."encryption"."keySource"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ServiceBus/namespaces/messages&quot;, &quot;sku.name&quot;: &quot;Premium (required for this rule&#x27;s guarantee)&quot;, &quot;type&quot;: &quot;Microsoft.ServiceBus/namespaces&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/service-bus-messaging/configure-customer-managed-key).

### FAIL — sql

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql

Type: Microsoft.Sql/servers; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: sql-server / 2026.09.19.1; basis: dependency_assessment; API: 2023-08-01.

**Reason:** At least one enumerated user database has disabled TDE.

**Scope:** Aggregated TDE state of enumerated user databases only.

Safe configuration evidence:

```json
{}
```

- Dependency (databases): /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/legacy — FAIL; resolved: True.
- Dependency (databases): /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/modern — PASS; resolved: True.
- Gap: Dependency databases is FAIL: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/legacy
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: FAIL. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql?api-version=2023-08-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql&quot;, &quot;type&quot;: &quot;Microsoft.Sql/servers&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Database or server identity does not prove TDE. Use the separate per-database TDE reads; SQL master cannot use this mechanism.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview).

**SYNTHETIC EXAMPLE — DO NOT RUN / list_databases (self)**

Enumerate databases identities; separate child reads establish configuration.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases?api-version=2023-08-01' --query '{"resources": value[].{id: id, type: type}, "more_pages": nextLink != `null` && nextLink != '"'"''"'"'}' --output json --only-show-errors
```

Expected / saved fields: {&quot;previously_observed_ids&quot;: [&quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/legacy&quot;, &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/modern&quot;]}

Traverse every page. A first page, resource count or identity list cannot prove encryption; run each child&#x27;s configuration commands. Missing children/read errors keep coverage incomplete.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview).

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (databases)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/legacy?api-version=2023-08-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/legacy&quot;, &quot;type&quot;: &quot;Microsoft.Sql/servers/databases&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Database or server identity does not prove TDE. Use the separate per-database TDE reads; SQL master cannot use this mechanism.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview).

**SYNTHETIC EXAMPLE — DO NOT RUN / tde_get (databases)**

Read the database&#x27;s TDE configuration, not the server&#x27;s key/protector setting.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/legacy/transparentDataEncryption/current?api-version=2023-08-01' --query '{"id": id, "state": properties.state}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/legacy/transparentDataEncryption/current&quot;, &quot;properties.state&quot;: &quot;Disabled&quot;}

Enabled supports the scoped configuration check; Disabled fails it. Missing, transitional or denied results remain unverified. This is current configuration, not a cryptographic test.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview).

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (databases)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/modern?api-version=2023-08-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/modern&quot;, &quot;type&quot;: &quot;Microsoft.Sql/servers/databases&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Database or server identity does not prove TDE. Use the separate per-database TDE reads; SQL master cannot use this mechanism.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview).

**SYNTHETIC EXAMPLE — DO NOT RUN / tde_get (databases)**

Read the database&#x27;s TDE configuration, not the server&#x27;s key/protector setting.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/modern/transparentDataEncryption/current?api-version=2023-08-01' --query '{"id": id, "state": properties.state}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/modern/transparentDataEncryption/current&quot;, &quot;properties.state&quot;: &quot;Enabled&quot;}

Enabled supports the scoped configuration check; Disabled fails it. Missing, transitional or denied results remain unverified. This is current configuration, not a cryptographic test.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview).

### FAIL — legacy

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/legacy

Type: Microsoft.Sql/servers/databases; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: sql-tde / 2026.09.19.1; basis: api_configuration; API: 2023-08-01.

**Reason:** The database TDE endpoint explicitly reports Disabled.

**Scope:** Database, transaction logs and TDE-protected backups; exported BACPAC and external data excluded.

Safe configuration evidence:

```json
{
  "tde.observed_at": "2026-09-19T02:39:32+00:00",
  "tde.state": "Disabled"
}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: FAIL. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/legacy?api-version=2023-08-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/legacy&quot;, &quot;type&quot;: &quot;Microsoft.Sql/servers/databases&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Database or server identity does not prove TDE. Use the separate per-database TDE reads; SQL master cannot use this mechanism.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview).

**SYNTHETIC EXAMPLE — DO NOT RUN / tde_get (self)**

Read the database&#x27;s TDE configuration, not the server&#x27;s key/protector setting.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/legacy/transparentDataEncryption/current?api-version=2023-08-01' --query '{"id": id, "state": properties.state}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/legacy/transparentDataEncryption/current&quot;, &quot;properties.state&quot;: &quot;Disabled&quot;}

Enabled supports the scoped configuration check; Disabled fails it. Missing, transitional or denied results remain unverified. This is current configuration, not a cryptographic test.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview).

### PASS — modern

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/modern

Type: Microsoft.Sql/servers/databases; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: sql-tde / 2026.09.19.1; basis: api_configuration; API: 2023-08-01.

**Reason:** The database TDE endpoint explicitly reports Enabled; provider-managed keys are acceptable.

**Scope:** Database, transaction logs and TDE-protected backups; exported BACPAC and external data excluded.

Safe configuration evidence:

```json
{
  "tde.observed_at": "2026-09-19T02:39:32+00:00",
  "tde.state": "Enabled"
}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/modern?api-version=2023-08-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/modern&quot;, &quot;type&quot;: &quot;Microsoft.Sql/servers/databases&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Database or server identity does not prove TDE. Use the separate per-database TDE reads; SQL master cannot use this mechanism.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview).

**SYNTHETIC EXAMPLE — DO NOT RUN / tde_get (self)**

Read the database&#x27;s TDE configuration, not the server&#x27;s key/protector setting.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/modern/transparentDataEncryption/current?api-version=2023-08-01' --query '{"id": id, "state": properties.state}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/modern/transparentDataEncryption/current&quot;, &quot;properties.state&quot;: &quot;Enabled&quot;}

Enabled supports the scoped configuration check; Disabled fails it. Missing, transitional or denied results remain unverified. This is current configuration, not a cryptographic test.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview).

### PASS — demostore

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/demostore

Type: Microsoft.Storage/storageAccounts; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: storage-sse / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-05-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Account blobs, files, queues and tables, including service replicas; excludes external copies.

Safe configuration evidence:

```json
{
  "encryption.keySource": "Microsoft.Storage",
  "encryption.services.blob.enabled": true,
  "encryption.services.file.enabled": true
}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/storage/common/storage-service-encryption) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/demostore?api-version=2023-05-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "encryption.keySource": properties."encryption"."keySource", "encryption.services.blob.enabled": properties."encryption"."services"."blob"."enabled", "encryption.services.file.enabled": properties."encryption"."services"."file"."enabled", "encryption.services.queue.enabled": properties."encryption"."services"."queue"."enabled", "encryption.services.table.enabled": properties."encryption"."services"."table"."enabled"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/demostore&quot;, &quot;properties.encryption.keySource&quot;: &quot;Microsoft.Storage&quot;, &quot;properties.encryption.services.blob.enabled&quot;: true, &quot;properties.encryption.services.file.enabled&quot;: true, &quot;type&quot;: &quot;Microsoft.Storage/storageAccounts&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/storage/common/storage-service-encryption).

### ERROR — deniedstore

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/deniedstore

Type: Microsoft.Storage/storageAccounts; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: storage-sse / 2026.09.19.1; basis: none; API: 2023-05-01.

**Reason:** A required resource or encryption read failed. No positive conclusion is available.

**Scope:** Account blobs, files, queues and tables, including service replicas; excludes external copies.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/storage/common/storage-service-encryption) (reviewed 2026-09-19).
- Read error: resource_get / http_error / HTTP 403.

Read-only verification commands:

Saved result: ERROR. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/deniedstore?api-version=2023-05-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "encryption.keySource": properties."encryption"."keySource", "encryption.services.blob.enabled": properties."encryption"."services"."blob"."enabled", "encryption.services.file.enabled": properties."encryption"."services"."file"."enabled", "encryption.services.queue.enabled": properties."encryption"."services"."queue"."enabled", "encryption.services.table.enabled": properties."encryption"."services"."table"."enabled"}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/deniedstore&quot;, &quot;type&quot;: &quot;Microsoft.Storage/storageAccounts&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/storage/common/storage-service-encryption).

### UNKNOWN — function-app

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app

Type: Microsoft.Web/sites; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: web-app / 2026.09.19.1; basis: backing_storage_required; API: 2023-12-01.

**Reason:** ARM metadata does not establish encryption for all workload storage. Review the explicit dependencies and gaps.

**Scope:** App Service / Functions identity and slot inventory only; host storage, deployment packages, mounts, temporary files, settings and downstream stores require evidence.

Safe configuration evidence:

```json
{}
```

- Dependency (slots): /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app/slots/staging — UNKNOWN; resolved: True.
- Gap: Dependency slots is UNKNOWN: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app/slots/staging
- Gap: App Service / Functions identity and slot inventory only; host storage, deployment packages, mounts, temporary files, settings and downstream stores require evidence.
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-functions/storage-considerations) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: UNKNOWN. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app?api-version=2023-12-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app&quot;, &quot;type&quot;: &quot;Microsoft.Web/sites&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-functions/storage-considerations).

**SYNTHETIC EXAMPLE — DO NOT RUN / list_slots (self)**

Enumerate slots identities; separate child reads establish configuration.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app/slots?api-version=2023-12-01' --query '{"resources": value[].{id: id, type: type}, "more_pages": nextLink != `null` && nextLink != '"'"''"'"'}' --output json --only-show-errors
```

Expected / saved fields: {&quot;previously_observed_ids&quot;: [&quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app/slots/staging&quot;]}

Traverse every page. A first page, resource count or identity list cannot prove encryption; run each child&#x27;s configuration commands. Missing children/read errors keep coverage incomplete.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-functions/storage-considerations).

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (slots)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app/slots/staging?api-version=2023-12-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app/slots/staging&quot;, &quot;type&quot;: &quot;Microsoft.Web/sites/slots&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-functions/storage-considerations).

### UNKNOWN — staging

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app/slots/staging

Type: Microsoft.Web/sites/slots; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: web-slot / 2026.09.19.1; basis: backing_storage_required; API: 2023-12-01.

**Reason:** ARM metadata does not establish encryption for all workload storage. Review the explicit dependencies and gaps.

**Scope:** Slot identity only; host/content storage, deployment packages and application stores unverified.

Safe configuration evidence:

```json
{}
```

- Gap: Slot identity only; host/content storage, deployment packages and application stores unverified.
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-functions/storage-considerations) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: UNKNOWN. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app/slots/staging?api-version=2023-12-01' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app/slots/staging&quot;, &quot;type&quot;: &quot;Microsoft.Web/sites/slots&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/azure-functions/storage-considerations).

### UNSUPPORTED — external-mongodb

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/MongoDB.Atlas/organizations/external-mongodb

Type: MongoDB.Atlas/organizations; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: unsupported / 2026.09.19.1; basis: none; API: None.

**Reason:** Inventory retained; no service or applicability assumptions made for this type.

**Scope:** No reviewed rule for this exact ARM resource type.

Safe configuration evidence:

```json
{}
```


Read-only verification commands:

Saved result: UNSUPPORTED. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / inventory_lookup (self)**

Locate this resource&#x27;s identity in subscription inventory.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resources?api-version=2021-04-01' --query '{"matches": value[?id == '"'"'/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/MongoDB.Atlas/organizations/external-mongodb'"'"'].{id: id, type: type, location: location}, "more_pages": nextLink != `null` && nextLink != '"'"''"'"'}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/MongoDB.Atlas/organizations/external-mongodb&quot;, &quot;type&quot;: &quot;MongoDB.Atlas/organizations&quot;}

Identity only; no service-specific encryption verification is available from this command. Follow all pages; an absent match is inconclusive. Unsupported or not-applicable status is not a PASS.


### PASS — node-disk

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/demo-nodes/providers/Microsoft.Compute/disks/node-disk

Type: Microsoft.Compute/disks; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:39:32+00:00; assessed: 2026-09-19T02:39:32+00:00.
Rule: disk-sse / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-10-02.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Persisted managed disk, snapshot or managed image content; excludes VM temporary disks and caches.

Safe configuration evidence:

```json
{
  "encryption.type": "EncryptionAtRestWithPlatformKey"
}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/virtual-machines/disk-encryption) (reviewed 2026-09-19).

Read-only verification commands:

Saved result: PASS. Commands are independent read suggestions; they do not change the assessment or guarantee a PASS.

SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.

**SYNTHETIC EXAMPLE — DO NOT RUN / resource_get (self)**

Read resource identity and selected encryption/dependency metadata using the collector&#x27;s recorded API version.

```sh
az rest --method get --url 'https://management.azure.com/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/demo-nodes/providers/Microsoft.Compute/disks/node-disk?api-version=2023-10-02' --query '{"id": id, "type": type, "location": location, "kind": kind, "sku": sku.name, "provisioningState": properties.provisioningState, "encryption.type": properties."encryption"."type", "storageProfile.osDiskId": properties.storageProfile.osDisk.managedDisk.id, "storageProfile.dataDiskIds": properties.storageProfile.dataDisks[].managedDisk.id, "virtualMachineProfile.storageProfile.osDiskId": properties.virtualMachineProfile.storageProfile.osDisk.managedDisk.id, "virtualMachineProfile.storageProfile.dataDiskIds": properties.virtualMachineProfile.storageProfile.dataDisks[].managedDisk.id}' --output json --only-show-errors
```

Expected / saved fields: {&quot;id&quot;: &quot;/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/demo-nodes/providers/Microsoft.Compute/disks/node-disk&quot;, &quot;properties.encryption.type&quot;: &quot;EncryptionAtRestWithPlatformKey&quot;, &quot;type&quot;: &quot;Microsoft.Compute/disks&quot;}

Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch.

[Supporting service documentation](https://learn.microsoft.com/en-us/azure/virtual-machines/disk-encryption).

## Collection errors

- /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/deniedstore: resource_get, http_error, HTTP 403, 2026-09-19T02:39:32+00:00.

## Control mapping and limits

Provisional technical configuration examination and documented service guarantees; not certification or full control effectiveness.

[NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) / [NIST SP 800-53A Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final). Mappings: SC-28 and SC-28(1).

- Inventory covers only the explicitly selected subscriptions or those visible to the CLI identity in its current tenant, in Azure public cloud.
- The ARM subscription resource list is not a universal child-resource or data-plane inventory. Only catalogued child collections are enumerated. Deleted, inaccessible, external and unlisted child resources may be absent.
- A PASS applies only to the stated resource scope and basis. Documented service enforcement is an inference from verified resource identity and a Microsoft guarantee, not a cryptographic measurement.
- Application data flows, Kubernetes runtime volumes, external SaaS, local copies, exports, diagnostics destinations and key lifecycle/availability are not comprehensively discovered.
- This is point-in-time technical evidence provisionally mapped to NIST SP 800-53 SC-28 and SC-28(1). Organizational scope, information types, integrity protection, procedures and operating effectiveness require separate RCSA/800-53A assessment.
