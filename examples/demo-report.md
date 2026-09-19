# Azure encryption-at-rest technical assessment

**Conclusion: FAILURES_FOUND**

Evidence mode: **offline_fixture**. Generated: 2026-09-19T02:25:45+00:00.
Collection: 2026-09-19T02:25:45+00:00 to 2026-09-19T02:25:45+00:00.
Rule version: 2026.09.19.1; tool version: 0.1.0.

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

## Resource evidence

### UNKNOWN — app

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/containerApps/app

Type: Microsoft.App/containerApps; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
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

### UNKNOWN — apps-env

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.App/managedEnvironments/apps-env

Type: Microsoft.App/managedEnvironments; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: container-env / 2026.09.19.1; basis: backing_storage_required; API: 2024-03-01.

**Reason:** ARM metadata does not establish encryption for all workload storage. Review the explicit dependencies and gaps.

**Scope:** Environment metadata only; file shares, logs, application volumes and revision storage need separate evidence.

Safe configuration evidence:

```json
{}
```

- Gap: Environment metadata only; file shares, logs, application volumes and revision storage need separate evidence.
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts) (reviewed 2026-09-19).

### PASS — configuration

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.AppConfiguration/configurationStores/configuration

Type: Microsoft.AppConfiguration/configurationStores; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: appconfig / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-03-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Sensitive configuration values stored within App Configuration; clients and linked stores excluded.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-app-configuration/concept-customer-managed-keys) (reviewed 2026-09-19).

### UNKNOWN — cache

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Cache/Redis/cache

Type: Microsoft.Cache/Redis; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
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

### PASS — enterprise-cache

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Cache/redisEnterprise/enterprise-cache

Type: Microsoft.Cache/redisEnterprise; location: eastus; SKU: Enterprise_E10.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: redis-enterprise / 2026.09.19.1; basis: documented_service_guarantee; API: 2024-02-01.

**Reason:** The documented guarantee covers service disks and persistence with Microsoft-managed keys.

**Scope:** Enterprise and Enterprise Flash service disks and persistence only; newer Managed Redis SKUs need a separate rule.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/cache-how-to-premium-persistence) (reviewed 2026-09-19).

### PASS — image

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Compute/images/image

Type: Microsoft.Compute/images; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: disk-sse / 2026.09.19.1; basis: documented_service_guarantee; API: 2024-03-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Persisted managed disk, snapshot or managed image content; excludes VM temporary disks and caches.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/virtual-machines/disk-encryption) (reviewed 2026-09-19).

### PASS — snapshot

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Compute/snapshots/snapshot

Type: Microsoft.Compute/snapshots; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: disk-sse / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-10-02.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Persisted managed disk, snapshot or managed image content; excludes VM temporary disks and caches.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/virtual-machines/disk-encryption) (reviewed 2026-09-19).

### PASS — registry

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerRegistry/registries/registry

Type: Microsoft.ContainerRegistry/registries; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
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

### UNKNOWN — aks

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks

Type: Microsoft.ContainerService/managedClusters; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
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

### UNKNOWN — system

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ContainerService/managedClusters/aks/agentPools/system

Type: Microsoft.ContainerService/managedClusters/agentPools; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
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

### PASS — backups

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DataProtection/backupVaults/backups

Type: Microsoft.DataProtection/backupVaults; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: backup / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-01-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Backup data stored in the Azure vault only; source workloads, operational snapshots, local agents and restore destinations require separate evidence.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/backup/encryption-at-rest-with-cmk-for-backup-vault) (reviewed 2026-09-19).

### PASS — mysql

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DBforMySQL/flexibleServers/mysql

Type: Microsoft.DBforMySQL/flexibleServers; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: mysql-flex / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-12-30.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Managed server data at rest; excludes customer exports and downstream stores.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/mysql/security/security-overview) (reviewed 2026-09-19).

### PASS — postgres

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DBforPostgreSQL/flexibleServers/postgres

Type: Microsoft.DBforPostgreSQL/flexibleServers; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
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

### PASS — cosmos-mongo

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DocumentDB/databaseAccounts/cosmos-mongo

Type: Microsoft.DocumentDB/databaseAccounts; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: cosmos / 2026.09.19.1; basis: documented_service_guarantee; API: 2024-05-15.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Account databases, attachments and service backups, including the MongoDB API.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/database-encryption-at-rest) (reviewed 2026-09-19).

### PASS — mongo-vcore

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.DocumentDB/mongoClusters/mongo-vcore

Type: Microsoft.DocumentDB/mongoClusters; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: documentdb-mongo / 2026.09.19.1; basis: documented_service_guarantee; API: 2024-07-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Azure DocumentDB (formerly Cosmos DB for MongoDB vCore) managed cluster data, logs, temporary files and backups; not MongoDB Atlas or self-hosted MongoDB.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/documentdb/database-encryption-at-rest) (reviewed 2026-09-19).

### PASS — events

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events

Type: Microsoft.EventHub/namespaces; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: eventhubs / 2026.09.19.1; basis: documented_service_guarantee; API: 2024-01-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Messages retained by Event Hubs; Capture destinations and consumer stores excluded.

Safe configuration evidence:

```json
{}
```

- Dependency (eventhubs): /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events/eventhubs/captured — PASS; resolved: True.
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/event-hubs/configure-customer-managed-key) (reviewed 2026-09-19).

### PASS — captured

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.EventHub/namespaces/events/eventhubs/captured

Type: Microsoft.EventHub/namespaces/eventhubs; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
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

### PASS — telemetry

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Insights/components/telemetry

Type: Microsoft.Insights/components; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
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

### PASS — secrets

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.KeyVault/vaults/secrets

Type: Microsoft.KeyVault/vaults; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: keyvault / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-07-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Vault-managed secret values, including certificate private-key secret representations; cryptographic key objects, consuming services and backups outside the vault are excluded.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/key-vault/secrets/about-secrets) (reviewed 2026-09-19).

### FAIL — analytics

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Kusto/clusters/analytics

Type: Microsoft.Kusto/clusters; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
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

### NOT_APPLICABLE — network

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Network/virtualNetworks/network

Type: Microsoft.Network/virtualNetworks; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: non-data-plane / 2026.09.19.1; basis: justified_applicability; API: None.

**Reason:** Resource is a networking or identity construct, not a customer data-at-rest store in this assessment. Network controls and diagnostic destinations are separate responsibilities.

**Scope:** Resource is a networking or identity construct, not a customer data-at-rest store in this assessment. Network controls and diagnostic destinations are separate responsibilities.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/security/fundamentals/shared-responsibility) (reviewed 2026-09-19).

### PASS — logs

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.OperationalInsights/workspaces/logs

Type: Microsoft.OperationalInsights/workspaces; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: logs / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-09-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Workspace data and saved queries inside Azure Monitor; exports excluded.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/customer-managed-keys) (reviewed 2026-09-19).

### PASS — recovery

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.RecoveryServices/vaults/recovery

Type: Microsoft.RecoveryServices/vaults; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: backup / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-01-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Backup data stored in the Azure vault only; source workloads, operational snapshots, local agents and restore destinations require separate evidence.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/backup/backup-encryption) (reviewed 2026-09-19).

### PASS — search

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Search/searchServices/search

Type: Microsoft.Search/searchServices; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: search / 2026.09.19.1; basis: documented_service_guarantee; API: 2023-11-01.

**Reason:** Verified resource identity is covered by Microsoft&#x27;s service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.

**Scope:** Search indexes, synonym maps and object definitions, on data and temporary disks; sources and enrichment dependencies excluded.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/search/search-security-built-in) (reviewed 2026-09-19).

### PASS — messages

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ServiceBus/namespaces/messages

Type: Microsoft.ServiceBus/namespaces; location: eastus; SKU: Premium.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: servicebus / 2026.09.19.1; basis: documented_service_guarantee; API: 2024-01-01.

**Reason:** Verified Premium resource identity is covered by the service-enforced encryption guarantee.

**Scope:** Premium namespace retained messages; other tiers need a separately substantiated guarantee.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/service-bus-messaging/configure-customer-managed-key) (reviewed 2026-09-19).

### FAIL — sql

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql

Type: Microsoft.Sql/servers; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
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

### FAIL — legacy

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/legacy

Type: Microsoft.Sql/servers/databases; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: sql-tde / 2026.09.19.1; basis: api_configuration; API: 2023-08-01.

**Reason:** The database TDE endpoint explicitly reports Disabled.

**Scope:** Database, transaction logs and TDE-protected backups; exported BACPAC and external data excluded.

Safe configuration evidence:

```json
{
  "tde.observed_at": "2026-09-19T02:25:45+00:00",
  "tde.state": "Disabled"
}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview) (reviewed 2026-09-19).

### PASS — modern

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Sql/servers/sql/databases/modern

Type: Microsoft.Sql/servers/databases; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: sql-tde / 2026.09.19.1; basis: api_configuration; API: 2023-08-01.

**Reason:** The database TDE endpoint explicitly reports Enabled; provider-managed keys are acceptable.

**Scope:** Database, transaction logs and TDE-protected backups; exported BACPAC and external data excluded.

Safe configuration evidence:

```json
{
  "tde.observed_at": "2026-09-19T02:25:45+00:00",
  "tde.state": "Enabled"
}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/transparent-data-encryption-tde-overview) (reviewed 2026-09-19).

### PASS — demostore

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/demostore

Type: Microsoft.Storage/storageAccounts; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
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

### ERROR — deniedstore

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/deniedstore

Type: Microsoft.Storage/storageAccounts; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: storage-sse / 2026.09.19.1; basis: none; API: 2023-05-01.

**Reason:** A required resource or encryption read failed. No positive conclusion is available.

**Scope:** Account blobs, files, queues and tables, including service replicas; excludes external copies.

Safe configuration evidence:

```json
{}
```

- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/storage/common/storage-service-encryption) (reviewed 2026-09-19).
- Read error: resource_get / http_error / HTTP 403.

### UNKNOWN — function-app

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app

Type: Microsoft.Web/sites; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
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

### UNKNOWN — staging

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Web/sites/function-app/slots/staging

Type: Microsoft.Web/sites/slots; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: web-slot / 2026.09.19.1; basis: backing_storage_required; API: 2023-12-01.

**Reason:** ARM metadata does not establish encryption for all workload storage. Review the explicit dependencies and gaps.

**Scope:** Slot identity only; host/content storage, deployment packages and application stores unverified.

Safe configuration evidence:

```json
{}
```

- Gap: Slot identity only; host/content storage, deployment packages and application stores unverified.
- [Microsoft service documentation](https://learn.microsoft.com/en-us/azure/azure-functions/storage-considerations) (reviewed 2026-09-19).

### UNSUPPORTED — external-mongodb

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/MongoDB.Atlas/organizations/external-mongodb

Type: MongoDB.Atlas/organizations; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
Rule: unsupported / 2026.09.19.1; basis: none; API: None.

**Reason:** Inventory retained; no service or applicability assumptions made for this type.

**Scope:** No reviewed rule for this exact ARM resource type.

Safe configuration evidence:

```json
{}
```


### PASS — node-disk

Resource: /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/demo-nodes/providers/Microsoft.Compute/disks/node-disk

Type: Microsoft.Compute/disks; location: eastus; SKU: unspecified.
Observed: 2026-09-19T02:25:45+00:00; assessed: 2026-09-19T02:25:45+00:00.
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

## Collection errors

- /subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/deniedstore: resource_get, http_error, HTTP 403, 2026-09-19T02:25:45+00:00.

## Control mapping and limits

Provisional technical configuration examination and documented service guarantees; not certification or full control effectiveness.

[NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) / [NIST SP 800-53A Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final). Mappings: SC-28 and SC-28(1).

- Inventory covers only the explicitly selected subscriptions or those visible to the CLI identity in its current tenant, in Azure public cloud.
- The ARM subscription resource list is not a universal child-resource or data-plane inventory. Only catalogued child collections are enumerated. Deleted, inaccessible, external and unlisted child resources may be absent.
- A PASS applies only to the stated resource scope and basis. Documented service enforcement is an inference from verified resource identity and a Microsoft guarantee, not a cryptographic measurement.
- Application data flows, Kubernetes runtime volumes, external SaaS, local copies, exports, diagnostics destinations and key lifecycle/availability are not comprehensively discovered.
- This is point-in-time technical evidence provisionally mapped to NIST SP 800-53 SC-28 and SC-28(1). Organizational scope, information types, integrity protection, procedures and operating effectiveness require separate RCSA/800-53A assessment.
