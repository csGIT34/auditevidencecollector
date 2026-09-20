"""Versioned, exact ARM type rules. No wildcard service guarantees."""
from dataclasses import dataclass, replace

RULE_VERSION = "2026.09.20.1"
SOURCE_REVIEWED = "2026-09-19"
LEARN = "https://learn.microsoft.com/en-us/"

@dataclass(frozen=True)
class Rule:
    key: str
    api: str
    mode: str
    scope: str
    source: str
    paths: tuple[str, ...] = ()
    children: tuple[tuple[str, str], ...] = ()

RULES: dict[str, Rule] = {}

def add(types, key, api, mode, scope, source, paths=(), children=()):
    for resource_type in types.split("|"):
        RULES[resource_type.lower()] = Rule(key, api, mode, scope, LEARN + source, paths, children)

add("Microsoft.Storage/storageAccounts", "storage-sse", "2023-05-01", "guarantee",
    "Account blobs, files, queues and tables, including service replicas; excludes external copies.",
    "azure/storage/common/storage-service-encryption",
    ("encryption.keySource", "encryption.services.blob.enabled", "encryption.services.file.enabled",
     "encryption.services.queue.enabled", "encryption.services.table.enabled"))
add("Microsoft.Compute/disks|Microsoft.Compute/snapshots|Microsoft.Compute/images", "disk-sse", "2023-10-02", "guarantee",
    "Persisted managed disk, snapshot or managed image content; excludes VM temporary disks and caches.",
    "azure/virtual-machines/disk-encryption", ("encryption.type",))
add("Microsoft.DBforPostgreSQL/flexibleServers", "postgres-flex", "2024-08-01", "guarantee",
    "Managed server databases, logs, temporary files and service backups.",
    "azure/postgresql/security/security-data-encryption", ("dataEncryption.type",))
add("Microsoft.DBforMySQL/flexibleServers", "mysql-flex", "2023-12-30", "guarantee",
    "Managed server data at rest; excludes customer exports and downstream stores.",
    "azure/mysql/security/security-overview", ("dataEncryption.type",))
add("Microsoft.DocumentDB/databaseAccounts", "cosmos", "2024-05-15", "guarantee",
    "Account databases, attachments and service backups, including the MongoDB API.",
    "azure/cosmos-db/database-encryption-at-rest")
add("Microsoft.DocumentDB/mongoClusters", "documentdb-mongo", "2024-07-01", "guarantee",
    "Azure DocumentDB (formerly Cosmos DB for MongoDB vCore) managed cluster data, logs, temporary files and backups; not MongoDB Atlas or self-hosted MongoDB.",
    "azure/documentdb/database-encryption-at-rest", ("dataEncryption.type",))
add("Microsoft.ContainerRegistry/registries", "acr", "2023-07-01", "guarantee",
    "Registry images and artifacts; downloaded images and runtime writes excluded.",
    "azure/container-registry/tutorial-customer-managed-keys", ("encryption.status",))
add("Microsoft.RecoveryServices/vaults|Microsoft.DataProtection/backupVaults", "backup", "2023-01-01", "guarantee",
    "Backup data stored in the Azure vault only; source workloads, operational snapshots, local agents and restore destinations require separate evidence.",
    "azure/backup/backup-encryption", ("encryption.infrastructureEncryption",))
add("Microsoft.OperationalInsights/workspaces", "logs", "2023-09-01", "guarantee",
    "Workspace data and saved queries inside Azure Monitor; exports excluded.",
    "azure/azure-monitor/logs/customer-managed-keys")
add("Microsoft.EventHub/namespaces", "eventhubs", "2024-01-01", "guarantee",
    "Messages retained by Event Hubs; Capture destinations and consumer stores excluded.",
    "azure/event-hubs/configure-customer-managed-key", ("encryption.keySource",),
    (("eventhubs", "Microsoft.EventHub/namespaces/eventhubs"),))
add("Microsoft.EventHub/namespaces/eventhubs", "eventhub-capture", "2024-01-01", "eventhub",
    "Event Hub retained messages and declared Capture storage destination.",
    "azure/event-hubs/event-hubs-capture-overview",
    ("captureDescription.enabled", "captureDescription.destination.name", "captureDescription.destination.properties.storageAccountResourceId"))
add("Microsoft.ServiceBus/namespaces", "servicebus", "2024-01-01", "servicebus",
    "Premium namespace retained messages; other tiers need a separately substantiated guarantee.",
    "azure/service-bus-messaging/configure-customer-managed-key", ("encryption.keySource",))
add("Microsoft.Search/searchServices", "search", "2023-11-01", "guarantee",
    "Search indexes, synonym maps and object definitions, on data and temporary disks; sources and enrichment dependencies excluded.",
    "azure/search/search-security-built-in")
add("Microsoft.AppConfiguration/configurationStores", "appconfig", "2023-03-01", "guarantee",
    "Sensitive configuration values stored within App Configuration; clients and linked stores excluded.",
    "azure/azure-app-configuration/concept-customer-managed-keys")
add("Microsoft.KeyVault/vaults", "keyvault", "2023-07-01", "guarantee",
    "Vault-managed secret values, including certificate private-key secret representations; cryptographic key objects, consuming services and backups outside the vault are excluded.",
    "azure/key-vault/secrets/about-secrets")
add("Microsoft.Kusto/clusters", "kusto", "2023-08-15", "kusto",
    "Cluster backing storage and VM cache disks; external tables and exports excluded.",
    "azure/data-explorer/cluster-encryption-overview", ("enableDiskEncryption",))
add("Microsoft.Sql/servers", "sql-server", "2023-08-01", "database_parent",
    "Aggregated TDE state of enumerated user databases only.",
    "azure/azure-sql/database/transparent-data-encryption-tde-overview",
    children=(("databases", "Microsoft.Sql/servers/databases"),))
add("Microsoft.Sql/managedInstances", "sql-mi", "2023-08-01", "database_parent",
    "Aggregated TDE state of enumerated user databases only; system database content is not covered.",
    "azure/azure-sql/database/transparent-data-encryption-tde-overview",
    children=(("databases", "Microsoft.Sql/managedInstances/databases"),))
add("Microsoft.Sql/servers/databases|Microsoft.Sql/managedInstances/databases", "sql-tde", "2023-08-01", "tde",
    "Database, transaction logs and TDE-protected backups; exported BACPAC and external data excluded.",
    "azure/azure-sql/database/transparent-data-encryption-tde-overview")
add("Microsoft.Synapse/workspaces/sqlPools", "synapse-tde", "2021-06-01", "tde",
    "Dedicated SQL pool data, logs and backups; workspace, Spark and data lake storage excluded.",
    "azure/synapse-analytics/security/workspaces-encryption")
add("Microsoft.Synapse/workspaces", "synapse", "2021-06-01", "workload",
    "Dedicated pools and declared data lake can be examined; Spark, pipelines, external stores and temporary storage remain unverified.",
    "azure/synapse-analytics/security/workspaces-encryption", ("defaultDataLakeStorage.accountUrl",),
    (("sqlPools", "Microsoft.Synapse/workspaces/sqlPools"),))
add("Microsoft.Compute/virtualMachines|Microsoft.Compute/virtualMachineScaleSets", "compute", "2024-03-01", "workload",
    "Declared managed disks and host encryption observations; guest, temporary, remote and runtime-mounted storage require additional evidence.",
    "azure/virtual-machines/disk-encryption-overview",
    ("securityProfile.encryptionAtHost", "virtualMachineProfile.securityProfile.encryptionAtHost"))
add("Microsoft.ContainerService/managedClusters", "aks", "2024-05-01", "workload",
    "ARM node-pool and node-resource-group evidence only; Kubernetes PVs, CSI drivers, emptyDir, hostPath, external stores and runtime workloads remain unverified.",
    "azure/aks/concepts-storage", ("nodeResourceGroup",),
    (("agentPools", "Microsoft.ContainerService/managedClusters/agentPools"),))
add("Microsoft.ContainerService/managedClusters/agentPools", "aks-pool", "2024-05-01", "workload",
    "Node host-encryption configuration only; does not establish workload or persistent-volume protection.",
    "azure/aks/enable-host-encryption", ("enableEncryptionAtHost", "osDiskType", "osDiskSizeGB"))
add("Microsoft.App/containerApps|Microsoft.App/jobs", "container-app", "2024-03-01", "workload",
    "Declared environment and volume metadata only; mounted stores, revisions, ephemeral storage and application dependencies remain unverified.",
    "azure/container-apps/storage-mounts", ("managedEnvironmentId", "environmentId"))
add("Microsoft.App/managedEnvironments", "container-env", "2024-03-01", "workload",
    "Environment metadata only; file shares, logs, application volumes and revision storage need separate evidence.",
    "azure/container-apps/storage-mounts")
add("Microsoft.Web/sites", "web-app", "2023-12-01", "workload",
    "App Service / Functions identity and slot inventory only; host storage, deployment packages, mounts, temporary files, settings and downstream stores require evidence.",
    "azure/azure-functions/storage-considerations", children=(("slots", "Microsoft.Web/sites/slots"),))
add("Microsoft.Web/sites/slots", "web-slot", "2023-12-01", "workload",
    "Slot identity only; host/content storage, deployment packages and application stores unverified.",
    "azure/azure-functions/storage-considerations")
add("Microsoft.Cache/Redis", "redis", "2024-03-01", "redis",
    "Premium RDB/AOF persistence destinations require verification; export, external and temporary copies excluded.",
    "azure/azure-cache-for-redis/cache-how-to-premium-persistence",
    ("redisConfiguration.rdb-backup-enabled", "redisConfiguration.aof-backup-enabled"))
add("Microsoft.Cache/redisEnterprise", "redis-enterprise", "2024-02-01", "redis_enterprise",
    "Enterprise and Enterprise Flash service disks and persistence only; newer Managed Redis SKUs need a separate rule.",
    "azure/azure-cache-for-redis/cache-how-to-premium-persistence")
add("Microsoft.Dashboard/grafana", "grafana-storage", "2023-09-01", "guarantee",
    "Grafana-owned system metadata and instance user data in its provider-managed Cosmos DB/PostgreSQL stores only; data sources, exported dashboards and snapshots outside those stores are separate.",
    "azure/managed-grafana/encryption")
add("Microsoft.Monitor/accounts", "prometheus-storage", "2023-04-03", "guarantee",
    "Prometheus metrics stored in this Azure Monitor workspace only; source/agent disks, external remote-write destinations and exported copies are separate. This is not a Log Analytics workspace rule.",
    "azure/azure-monitor/metrics/azure-monitor-workspace-overview")
add("Microsoft.Automation/automationAccounts", "automation-secure-assets", "2023-11-01", "guarantee",
    "Automation secure credentials, certificates, connections, encrypted variables, runbooks and DSC scripts only; unencrypted variables, job output, worker disks and exported code/logs are not covered.",
    "azure/automation/automation-secure-asset-encryption")
add("Microsoft.Insights/components", "app-insights", "2020-02-02", "linked",
    "Workspace-backed telemetry only; classic Application Insights and exported copies unverified.",
    "azure/azure-monitor/app/create-workspace-resource", ("WorkspaceResourceId",))
add("Microsoft.Network/virtualNetworks|Microsoft.Network/virtualNetworks/subnets|Microsoft.Network/networkInterfaces|Microsoft.Network/networkSecurityGroups|Microsoft.Network/routeTables|Microsoft.Network/publicIPAddresses|Microsoft.Network/privateEndpoints|Microsoft.ManagedIdentity/userAssignedIdentities", "non-data-plane", "", "na",
    "Resource is a networking or identity construct, not a customer data-at-rest store in this assessment. Network controls and diagnostic destinations are separate responsibilities.",
    "azure/security/fundamentals/shared-responsibility")

# Service-specific API/source overrides; Compute image versions differ from disk versions.
RULES["microsoft.compute/images"] = replace(RULES["microsoft.compute/images"], api="2024-03-01")
RULES["microsoft.dataprotection/backupvaults"] = replace(RULES["microsoft.dataprotection/backupvaults"], source=LEARN + "azure/backup/encryption-at-rest-with-cmk-for-backup-vault")
