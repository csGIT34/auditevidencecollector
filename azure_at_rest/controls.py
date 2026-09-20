"""Allowlisted configuration checks, independent of encryption conclusions.

Each predicate examines one returned configuration value. Catalog references are
supporting evidence links, not completion of the larger research objective.
"""
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import json
from urllib.parse import urlsplit
from .safety import MISSING, INVALID, get, now, resource_id, subscription_id

VERSION = '2026.09.20.5'
OBJECTIVES = json.loads(Path(__file__).with_name('control_objectives.json').read_text())

@dataclass(frozen=True)
class Check:
    id: str
    resource_type: str
    api: str
    path: str
    values: tuple
    catalog_ref: str
    title: str
    source: str
    suffix: str = ''
    kind: str = 'scalar'
    operation: str = 'get'

CHECKS = {}

def add(rt, api, service, rows, *, suffix='', source_type=None):
    namespace, name = (source_type or rt).lower().split('/', 1)
    source = f'https://learn.microsoft.com/en-us/azure/templates/{namespace}/{api}/{name}'
    for domain, key, path, values, title in rows:
        cid = service + '-' + key
        # Slot predicates use their own IDs but map to the same service objective.
        if rt.lower().endswith('/slots'):
            cid += '-slot'
        if cid in CHECKS:
            raise ValueError('Duplicate configuration check')
        CHECKS[cid] = Check(cid, rt.lower(), api, path, tuple(values), service + '-' + domain, title, source, suffix)

B = (False, True)
ACCESS = ('Enabled', 'Disabled', 'SecuredByPerimeter')
add('Microsoft.Storage/storageAccounts', '2023-05-01', 'ST', [
 ('N','public-network','publicNetworkAccess',ACCESS,'Account public network access configuration'),
 ('N','anonymous-blob','allowBlobPublicAccess',B,'Account permission for anonymous blob access; container state is separate'),
 ('I','shared-key','allowSharedKeyAccess',B,'Shared-key authorization configuration'),
 ('T','https','supportsHttpsTrafficOnly',B,'Secure transfer requirement'),
 ('T','tls','minimumTlsVersion',('TLS1_0','TLS1_1','TLS1_2'),'Minimum configured TLS version'),
 ('N','network-default','networkAcls.defaultAction',('Allow','Deny'),'Network ACL default action; exceptions require separate review')])
for rt in ('Microsoft.Web/sites','Microsoft.Web/sites/slots'):
 add(rt,'2023-12-01','FUNC',[
  ('T','https','httpsOnly',B,'HTTPS-only configuration'),
  ('N','public-network','publicNetworkAccess',('Enabled','Disabled'),'Public network access configuration')])
add('Microsoft.KeyVault/vaults','2023-07-01','KV',[
 ('I','rbac','enableRbacAuthorization',B,'RBAC authorization model; actual assignments remain separate'),
 ('N','public-network','publicNetworkAccess',ACCESS,'Public network access configuration'),
 ('N','network-default','networkAcls.defaultAction',('Allow','Deny'),'Network ACL default action'),
 ('B','purge-protection','enablePurgeProtection',B,'Purge protection configuration'),
 ('B','soft-delete','enableSoftDelete',B,'Soft delete configuration')])
add('Microsoft.EventHub/namespaces','2024-01-01','EH',[
 ('I','local-auth','disableLocalAuth',B,'Local authentication disabled setting'),
 ('N','public-network','publicNetworkAccess',ACCESS,'Public network access configuration'),
 ('T','tls','minimumTlsVersion',('1.0','1.1','1.2'),'Minimum configured TLS version')])
add('Microsoft.DocumentDB/databaseAccounts','2024-05-15','COS',[
 ('I','local-auth','disableLocalAuth',B,'Key-based authentication disabled setting'),
 ('N','public-network','publicNetworkAccess',ACCESS,'Public network access configuration'),
 ('T','tls','minimalTlsVersion',('Tls','Tls11','Tls12'),'Minimum configured TLS version')])
add('Microsoft.ContainerRegistry/registries','2023-07-01','ACR',[
 ('I','admin-user','adminUserEnabled',B,'Registry admin account enabled setting'),
 ('N','public-network','publicNetworkAccess',('Enabled','Disabled'),'Public network access configuration')])
add('Microsoft.AppConfiguration/configurationStores','2023-03-01','APPC',[
 ('I','local-auth','disableLocalAuth',B,'Local authentication disabled setting'),
 ('N','public-network','publicNetworkAccess',('Enabled','Disabled'),'Public network access configuration'),
 ('B','purge-protection','enablePurgeProtection',B,'Purge protection configuration')])
add('Microsoft.OperationalInsights/workspaces','2023-09-01','LA',[
 ('I','local-auth','features.disableLocalAuth',B,'Local authentication disabled setting'),
 ('N','public-ingestion','publicNetworkAccessForIngestion',('Enabled','Disabled'),'Public ingestion configuration'),
 ('N','public-query','publicNetworkAccessForQuery',('Enabled','Disabled'),'Public query configuration'),
 ('L','retention','retentionInDays',(),'Workspace default retention days; table overrides remain separate')])
add('Microsoft.Insights/components','2020-02-02','AI',[
 ('I','local-auth','DisableLocalAuth',B,'Local authentication disabled setting'),
 ('N','public-ingestion','publicNetworkAccessForIngestion',('Enabled','Disabled'),'Public ingestion configuration'),
 ('N','public-query','publicNetworkAccessForQuery',('Enabled','Disabled'),'Public query configuration')])
add('Microsoft.ContainerService/managedClusters','2024-05-01','AKS',[
 ('I','local-accounts','disableLocalAccounts',B,'Local Kubernetes accounts disabled setting'),
 ('I','rbac','enableRBAC',B,'Kubernetes RBAC enabled setting; bindings remain separate'),
 ('I','azure-rbac','aadProfile.enableAzureRBAC',B,'Azure RBAC integration setting'),
 ('N','private-api','apiServerAccessProfile.enablePrivateCluster',B,'Private control-plane configuration')])
add('Microsoft.App/containerApps','2024-03-01','ACA',[
 ('T','insecure-ingress','configuration.ingress.allowInsecure',B,'Insecure ingress allowed setting'),
 ('N','external-ingress','configuration.ingress.external',B,'External ingress configuration; missing ingress is unassessed')])
add('Microsoft.DBforPostgreSQL/flexibleServers','2024-08-01','PG',[
 ('I','password-auth','authConfig.passwordAuth',('Enabled','Disabled'),'Password authentication configuration'),
 ('I','entra-auth','authConfig.activeDirectoryAuth',('Enabled','Disabled'),'Entra authentication configuration'),
 ('N','public-network','network.publicNetworkAccess',('Enabled','Disabled'),'Public network access configuration'),
 ('B','backup-retention','backup.backupRetentionDays',(),'Configured backup retention days; restore success remains separate')])
add('Microsoft.Cache/redisEnterprise','2025-04-01','REDIS',[
 ('T','tls','minimumTlsVersion',('1.0','1.1','1.2'),'Minimum configured TLS version; database protocol remains separate'),
 ('B','high-availability','highAvailability',('Disabled','Enabled'),'Cluster replication configuration; recovery testing remains separate')])
add('Microsoft.Cache/redisEnterprise/databases','2025-04-01','REDIS',[
 ('I','access-keys','accessKeysAuthentication',('Disabled','Enabled'),'Database access-key authentication configuration; Entra role assignments remain separate'),
 ('T','client-protocol','clientProtocol',('Encrypted','Plaintext'),'Configured client connection protocol'),
 ('C','clustering-policy','clusteringPolicy',('EnterpriseCluster','OSSCluster'),'Database clustering policy; client compatibility remains separate'),
 ('C','eviction-policy','evictionPolicy',('AllKeysLFU','AllKeysLRU','AllKeysRandom','NoEviction','VolatileLFU','VolatileLRU','VolatileRandom','VolatileTTL'),'Database eviction policy; data-loss impact remains an owner judgement'),
 ('V','defer-upgrade','deferUpgrade',('Deferred','NotDeferred'),'Deferred Redis version upgrade configuration; the installed version remains separate'),
 ('B','rdb-persistence','persistence.rdbEnabled',B,'RDB persistence configuration; snapshot recovery testing remains separate'),
 ('B','aof-persistence','persistence.aofEnabled',B,'AOF persistence configuration; recovery testing remains separate')])
add('Microsoft.Automation/automationAccounts','2023-11-01','AUTO',[
 ('I','local-auth','disableLocalAuth',B,'Local authentication disabled setting'),
 ('N','public-network','publicNetworkAccess',B,'Public network access configuration')])
add('Microsoft.Dashboard/grafana','2023-09-01','GRAF',[
 ('N','public-network','publicNetworkAccess',('Enabled','Disabled'),'Public network access configuration'),
 ('B','zone-redundancy','zoneRedundancy',('Enabled','Disabled'),'Zone redundancy configuration; availability testing remains separate')])
add('Microsoft.Monitor/accounts','2023-04-03','PROM',[
 ('N','public-network','publicNetworkAccess',('Enabled','Disabled'),'Workspace public network configuration; collection endpoints remain separate')])
add('Microsoft.EventGrid/topics','2022-06-15','EG',[
 ('I','local-auth','disableLocalAuth',B,'Custom topic local authentication disabled setting'),
 ('N','public-network','publicNetworkAccess',('Enabled','Disabled'),'Custom topic public network access configuration')])
add('Microsoft.DataProtection/backupVaults','2023-01-01','BV',[
 ('B','backup-immutability','securitySettings.immutabilitySettings.state',('Disabled','Unlocked','Locked'),'Backup vault immutability configuration'),
 ('B','backup-soft-delete','securitySettings.softDeleteSettings.state',('Off','On','AlwaysOn'),'Backup vault soft delete configuration')])
add('Microsoft.RecoveryServices/vaults','2023-01-01','BV',[
 ('B','recovery-immutability','securitySettings.immutabilitySettings.state',('Disabled','Unlocked','Locked'),'Recovery Services vault immutability configuration'),
 ('N','recovery-public-network','publicNetworkAccess',('Enabled','Disabled'),'Recovery Services vault public network configuration')])



for rt in ('Microsoft.Web/sites','Microsoft.Web/sites/slots'):
 add(rt,'2023-12-01','FUNC',[
  ('T','tls','minTlsVersion',('1.0','1.1','1.2','1.3'),'Minimum site TLS configuration'),
  ('T','scm-tls','scmMinTlsVersion',('1.0','1.1','1.2','1.3'),'Minimum SCM TLS configuration'),
  ('T','ftp','ftpsState',('AllAllowed','FtpsOnly','Disabled'),'FTP transport configuration'),
  ('C','remote-debugging','remoteDebuggingEnabled',B,'Remote debugging enabled setting')],suffix='/config/web',source_type=rt+'/config')
 add(rt,'2023-12-01','FUNC',[
  ('I','auth-platform','platform.enabled',B,'App Service authentication platform enabled setting'),
  ('I','auth-required','globalValidation.requireAuthentication',B,'App Service authentication required setting; excluded paths and app authorization remain separate')],suffix='/config/authsettingsV2',source_type=rt+'/config')
 for method in ('scm','ftp'):
  add(rt,'2023-12-01','FUNC',[
   ('I',method+'-basic-auth','allow',B,method.upper()+' basic publishing authentication allowed setting')],suffix='/basicPublishingCredentialsPolicies/'+method,source_type=rt+'/basicPublishingCredentialsPolicies')
add('Microsoft.Storage/storageAccounts','2023-05-01','ST',[
 ('B','blob-soft-delete','deleteRetentionPolicy.enabled',B,'Blob soft delete configuration'),
 ('B','container-soft-delete','containerDeleteRetentionPolicy.enabled',B,'Container soft delete configuration'),
 ('B','blob-versioning','isVersioningEnabled',B,'Blob versioning configuration; capability depends on account kind'),
 ('B','blob-restore','restorePolicy.enabled',B,'Blob point-in-time restore configuration; restore test remains separate')],suffix='/blobServices/default',source_type='Microsoft.Storage/storageAccounts/blobServices')
for rt, service, prefix in [('Microsoft.Compute/virtualMachines','VM',''),('Microsoft.Compute/virtualMachineScaleSets','VMSS','virtualMachineProfile.')]:
 add(rt,'2024-03-01',service,[
  ('I','linux-password-auth',prefix+'osProfile.linuxConfiguration.disablePasswordAuthentication',B,'Linux password authentication disabled configuration; missing/other OS unassessed'),
  ('C','secure-boot',prefix+'securityProfile.uefiSettings.secureBootEnabled',B,'Secure Boot configuration; unsupported security types unassessed'),
  ('C','vtpm',prefix+'securityProfile.uefiSettings.vTpmEnabled',B,'Virtual TPM configuration; workload attestation remains separate')])



def shared_tail(rt):
    """Distinguish several registered types of one service; a collision would silently rebind a check."""
    return ('-slot' if rt.endswith('/slots') else '-recovery' if rt == 'microsoft.recoveryservices/vaults'
            else '-database' if rt.endswith('/databases') else '')

# Explicit configuration scope only: no inference about event delivery or health.
for rt in sorted({c.resource_type for c in CHECKS.values()}):
 base = next(c for c in CHECKS.values() if c.resource_type == rt)
 service = base.catalog_ref.split('-')[0]
 cid = service + '-diagnostic-logs' + shared_tail(rt)
 if cid in CHECKS:
  raise ValueError('Duplicate configuration check')
 suffix = ('/blobServices/default' if service=='ST' else '') + '/providers/Microsoft.Insights/diagnosticSettings'
 CHECKS[cid] = Check(cid,rt,'2021-05-01-preview','logs[].category/categoryGroup',(),service+'-L',
     'Enabled diagnostic log categories/groups; configured destinations and ingestion health require separate evidence',
     'https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list?view=rest-monitor-2021-05-01-preview',
     suffix,'labels','diagnostics')



for _logs in list(CHECKS.values()):
    if _logs.operation=='diagnostics':
        _cid=_logs.id.replace('diagnostic-logs','diagnostic-routes')
        if _cid in CHECKS:
            raise ValueError('Duplicate configuration check')
        CHECKS[_cid]=Check(_cid,_logs.resource_type,_logs.api,'logs and destination IDs per diagnostic setting',(),_logs.catalog_ref,
            'Enabled audit categories bound to configured destinations; delivery and retention remain separate',
            _logs.source,_logs.suffix,'diagnostic_routes','diagnostic_routes')

PE_SOURCE='https://learn.microsoft.com/en-us/azure/templates/microsoft.network/2023-11-01/privateendpoints'
for key,path,kind,title in [
 ('targets','privateLinkServiceConnections/manualPrivateLinkServiceConnections.privateLinkServiceId','resource_ids','Declared private endpoint target IDs; reachability and public target restrictions remain separate'),
 ('approval','privateLinkServiceConnections/manualPrivateLinkServiceConnections.privateLinkServiceConnectionState.status','tokens','Returned private endpoint connection approval states'),
 ('subresources','privateLinkServiceConnections/manualPrivateLinkServiceConnections.groupIds','tokens','Declared private endpoint subresource group IDs')]:
 cid='PE-'+key
 CHECKS[cid]=Check(cid,'microsoft.network/privateendpoints','2023-11-01',path,(),'PE-N',title,PE_SOURCE,'',kind,'private_endpoint')
CHECKS['UAMI-federation-trust']=Check('UAMI-federation-trust','microsoft.managedidentity/userassignedidentities','2023-01-31',
 'federatedIdentityCredentials[].issuer/subject/audiences',(),'UAMI-I',
 'Exact federated issuer, subject and audience tuples compared with supplied approved trust configuration',
 'https://learn.microsoft.com/en-us/azure/templates/microsoft.managedidentity/2023-01-31/userassignedidentities/federatedidentitycredentials',
 '/federatedIdentityCredentials','federation','federation')

CHECKS['APPREG-audience'] = Check('APPREG-audience','graph.application','v1.0','signInAudience',
 ('AzureADMyOrg','AzureADMultipleOrgs','AzureADandPersonalMicrosoftAccount','PersonalMicrosoftAccount'),'APPREG-I',
 'Application sign-in audience configuration; actual consent and access remain separate',
 'https://learn.microsoft.com/en-us/graph/api/resources/application?view=graph-rest-1.0')
CHECKS['APPREG-owner-count'] = Check('APPREG-owner-count','graph.application','v1.0','owners.count',(),'APPREG-I',
 'Number of explicitly enumerated application owners; accountability review remains separate',
 'https://learn.microsoft.com/en-us/graph/api/application-list-owners?view=graph-rest-1.0', '/owners')
CHECKS['APPREG-expired-credentials'] = Check('APPREG-expired-credentials','graph.application','v1.0','credentials.expiredCount',(),'APPREG-K',
 'Expired application password/key credential metadata count; no credential values are collected',
 'https://learn.microsoft.com/en-us/graph/api/resources/application?view=graph-rest-1.0')
CHECKS['APPREG-sp-enabled'] = Check('APPREG-sp-enabled','graph.servicePrincipal','v1.0','accountEnabled',B,'APPREG-I',
 'Related service-principal enabled configuration',
 'https://learn.microsoft.com/en-us/graph/api/resources/serviceprincipal?view=graph-rest-1.0')
CHECKS['APPREG-role-grants'] = Check('APPREG-role-grants','graph.servicePrincipal','v1.0','appRoleAssignments.count',(),'APPREG-I',
 'Application role grant count; roles and target resource IDs remain preserved for owner review',
 'https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-approleassignments?view=graph-rest-1.0','/appRoleAssignments')



CHECKS['APPREG-approved-owners']=Check('APPREG-approved-owners','graph.application','v1.0','owners[].id',(),'APPREG-I',
 'Exact application owner ID set compared with supplied approved owners',
 'https://learn.microsoft.com/en-us/graph/api/application-list-owners?view=graph-rest-1.0','/owners','uuid_set')
CHECKS['APPREG-approved-role-grants']=Check('APPREG-approved-role-grants','graph.servicePrincipal','v1.0','appRoleAssignments[].principalId/resourceId/appRoleId',(),'APPREG-I',
 'Exact granted application role tuples compared with supplied approved grants; delegated consent and effective user access remain separate',
 'https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-approleassignments?view=graph-rest-1.0','/appRoleAssignments','role_grants')
CHECKS['APPREG-federation-trust']=Check('APPREG-federation-trust','graph.application','v1.0','federatedIdentityCredentials[].issuer/subject/audiences',(),'APPREG-I',
 'Exact application federated trust tuples compared with supplied approved trust configuration',
 'https://learn.microsoft.com/en-us/graph/api/federatedidentitycredential-list?view=graph-rest-1.0','/federatedIdentityCredentials','federation')


CHECKS['APPREG-delegated-grants']=Check('APPREG-delegated-grants','graph.servicePrincipal','v1.0',
 'oauth2PermissionGrants[].clientId/resourceId/consentType/principalId/scope',(),'APPREG-I',
 'Exact delegated consent grants and scope claims; effective user access and consent review remain separate',
 'https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-oauth2permissiongrants?view=graph-rest-1.0',
 '/oauth2PermissionGrants','delegated_grants')

# One declared-assignment comparison per supported ARM resource type.
from .authorization import API as AUTH_API, SOURCE as AUTH_SOURCE, SUFFIX as AUTH_SUFFIX
for _rt in sorted({c.resource_type for c in CHECKS.values() if not c.resource_type.startswith('graph.')}):
    _sample = next(c for c in CHECKS.values() if c.resource_type == _rt)
    _service = _sample.catalog_ref.split('-')[0]
    _cid = _service + '-approved-arm-grants' + shared_tail(_rt)
    if _cid in CHECKS:
        raise ValueError('Duplicate configuration check')
    CHECKS[_cid] = Check(_cid,_rt,AUTH_API,'assignments[].principalId/scope/roleDefinitionId/permissions/conditionSha256',(),_service+'-I',
        'Declared ARM assignments at or above this resource and resolved role permissions; effective access remains separate',
        AUTH_SOURCE,AUTH_SUFFIX,'arm_grants','authorization')

CHECKS['BV-backup-population']=Check('BV-backup-population','microsoft.dataprotection/backupvaults','2026-03-01',
 'backupInstances[].dataSourceInfo.resourceID/policyInfo.policyId/currentProtectionState/protectionStatus.status',(),'BV-B',
 'Backup instance source, policy and reported protection state; restore success remains separate',
 'https://learn.microsoft.com/en-us/rest/api/dataprotection/backup-instances/list?view=rest-dataprotection-2026-03-01',
 '/backupInstances','dp_population','backup_population')
CHECKS['BV-recovery-population']=Check('BV-recovery-population','microsoft.recoveryservices/vaults','2026-02-01',
 'backupProtectedItems[].sourceResourceId/policyId/protectionState/protectionStatus',(),'BV-B',
 'Recovery Services protected source, policy and reported protection state; restore success remains separate',
 'https://learn.microsoft.com/en-us/rest/api/backup/backup-protected-items/list?view=rest-backup-2026-02-01',
 '/backupProtectedItems','rs_population','backup_population')

CHECKS['VMSS-instance-models']=Check('VMSS-instance-models','microsoft.compute/virtualmachinescalesets','2026-03-01',
 'virtualMachines[].latestModelApplied',(),'VMSS-C',
 'Uniform scale-set instance population and latest model application; guest drift remains separate',
 'https://learn.microsoft.com/en-us/rest/api/compute/virtual-machine-scale-set-vms/list?view=rest-compute-2026-03-01',
 '/virtualMachines','vmss_instances','vmss_instances')

CHECKS['ACA-revision-images']=Check('ACA-revision-images','microsoft.app/containerapps','2026-01-01',
 'revisions[].active/template.containers[].image/template.initContainers[].image',(),'ACA-V',
 'Revision population, active state and declared app/init images; digest resolution and vulnerability scans remain separate',
 'https://learn.microsoft.com/en-us/rest/api/resource-manager/containerapps/container-apps-revisions/list-revisions?view=rest-resource-manager-containerapps-2026-01-01',
 '/revisions','container_revisions','container_revisions')

for _cid,_rt,_api,_source in (
 ('BV-backup-jobs','microsoft.dataprotection/backupvaults','2026-03-01','https://learn.microsoft.com/en-us/rest/api/dataprotection/jobs/list?view=rest-dataprotection-2026-03-01'),
 ('BV-recovery-jobs','microsoft.recoveryservices/vaults','2026-02-01','https://learn.microsoft.com/en-us/rest/api/backup/backup-jobs/list?view=rest-backup-2026-02-01')):
    CHECKS[_cid]=Check(_cid,_rt,_api,'backupJobs[].operation/status/startTime/endTime',(),'BV-B',
        'Backup and restore job outcomes and approved recency window; restore quality remains separate',
        _source,'/backupJobs','backup_jobs','backup_jobs')

CHECKS['ST-container-access']=Check('ST-container-access','microsoft.storage/storageaccounts','2023-05-01',
 'containers[].publicAccess',(),'ST-N','Container-level anonymous access declarations; account restrictions and actual reachability remain separate',
 'https://learn.microsoft.com/en-us/rest/api/storagerp/blob-containers/list?view=rest-storagerp-2023-05-01',
 '/blobServices/default/containers','container_access','blob_containers')

CHECKS['VMSS-instance-members']=Check('VMSS-instance-members','microsoft.compute/virtualmachinescalesets','2026-03-01',
 'instance_membership',(),'VMSS-C','Actual Uniform/Flexible VM membership in the selected collection scope',
 'https://learn.microsoft.com/en-us/azure/virtual-machine-scale-sets/virtual-machine-scale-sets-orchestration-modes',
 '/virtualMachines','vmss_members','vmss_members')

for _kind,_domain,_title in [('runbooks','C','Runbook publication, type, runtime reference and logging metadata'),('modules','V','Classic module population, declared versions and provisioning states')]:
    _id='AUTO-'+_kind+'-metadata'
    CHECKS[_id]=Check(_id,'microsoft.automation/automationaccounts','2024-10-23',_kind,(),'AUTO-'+_domain,_title,
        'https://learn.microsoft.com/en-us/rest/api/automation/'+('runbook' if _kind=='runbooks' else 'module')+'/list-by-automation-account?view=rest-automation-2024-10-23',
        '/'+_kind,'automation_assets','automation_assets')

CHECKS['AUTO-runtime-packages']=Check('AUTO-runtime-packages','microsoft.automation/automationaccounts','2024-10-23',
 'runtimeEnvironments[].runtime/defaultPackages/packages',(),'AUTO-V','Runtime environment language/version, default packages and imported package metadata',
 'https://learn.microsoft.com/en-us/rest/api/automation/runtime-environments/list-by-automation-account?view=rest-automation-2024-10-23',
 '/runtimeEnvironments','automation_runtimes','automation_runtimes')

CHECKS['LA-table-retention']=Check('LA-table-retention','microsoft.operationalinsights/workspaces','2025-07-01',
 'tables[].plan/retentionInDays/totalRetentionInDays',(),'LA-L','Table population, plans and retention configuration',
 'https://learn.microsoft.com/en-us/rest/api/loganalytics/tables/list-by-workspace?view=rest-loganalytics-2025-07-01',
 '/tables','log_tables','log_tables')

def for_type(rt):
    return [c for c in CHECKS.values() if c.resource_type.lower() == rt.lower()]


for _kind in ('keys','secrets','certificates'):
    _id='KV-'+_kind+'-lifecycle'
    CHECKS[_id]=Check(_id,'microsoft.keyvault/vaults','2025-07-01',_kind,(),'KV-K',
        'Listed '+_kind+' base-object expiration metadata',
        'https://learn.microsoft.com/en-us/rest/api/keyvault/'+_kind+'/get-'+_kind+'/get-'+_kind,
        '/'+_kind,'vault_objects','vault_metadata')


def valid_value(check, value):
    if check.kind=='log_tables':
        from .log_tables import valid
        return valid(value)
    if check.kind=='automation_runtimes':
        from .automation_assets import valid_runtimes
        return valid_runtimes(value)
    if check.kind=='automation_assets':
        from .automation_assets import valid_assets
        return valid_assets(value,check.path)
    if check.kind=='vmss_members':
        from .compute_instances import valid_members
        return valid_members(value)
    if check.kind=='vault_objects':
        from .vault_metadata import valid_objects
        return valid_objects(value,check.path)
    if check.kind=='container_access':
        from .blob_containers import valid_containers
        return valid_containers(value)
    if check.kind=='backup_jobs':
        from .backup_jobs import valid_jobs
        return valid_jobs(value)
    if check.kind=='container_revisions':
        from .container_revisions import valid_revisions
        return valid_revisions(value)
    if check.kind=='vmss_instances':
        from .compute_instances import valid_instances
        return valid_instances(value)
    if check.kind in ('dp_population','rs_population'):
        from .backup_population import valid_population
        return valid_population(value,'dataprotection' if check.kind=='dp_population' else 'recovery')
    if check.kind=='diagnostic_routes':
        from .diagnostic_routes import valid_routes
        return valid_routes(value)
    if check.kind=='delegated_grants':
        from .authorization import valid_delegated_grants
        return valid_delegated_grants(value)
    if check.kind=='arm_grants':
        from .authorization import valid_grants
        return valid_grants(value)
    if check.kind=='uuid_set':
        return isinstance(value,list) and len(value)<=10000 and all(isinstance(v,str) and subscription_id(v)==v for v in value) and value==sorted(set(value))
    if check.kind=='role_grants':
        if not isinstance(value,list) or len(value)>10000:return False
        if not all(isinstance(r,dict) and set(r)=={'principalId','resourceId','appRoleId'} and all(isinstance(v,str) and subscription_id(v)==v for v in r.values()) for r in value):return False
        return value==sorted(value,key=lambda r:json.dumps(r,sort_keys=True))
    if check.kind in ('tokens','resource_ids'):
        valid = lambda v: isinstance(v,str) and (resource_id(v) is not None and v==v.lower() if check.kind=='resource_ids' else re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',v) is not None)
        return isinstance(value,list) and len(value)<=512 and all(valid(v) for v in value) and len(value)==len(set(value)) and value==sorted(value)
    if check.kind == 'federation':
        if not isinstance(value,list) or len(value)>512:return False
        for row in value:
            if not isinstance(row,dict) or set(row)!={'issuer','subject','audiences'}:return False
            issuer,subject,audiences=row['issuer'],row['subject'],row['audiences']
            if not isinstance(issuer,str) or not re.fullmatch(r'https://[A-Za-z0-9.-]+(?::443)?(?:/[A-Za-z0-9._/-]*)?',issuer) or len(issuer)>2048:return False
            if not isinstance(subject,str) or not re.fullmatch(r'[A-Za-z0-9_.:/@-]{1,600}',subject):return False
            if not isinstance(audiences,list) or not 1<=len(audiences)<=16 or not all(isinstance(a,str) and re.fullmatch(r'[A-Za-z0-9_.:/-]{1,256}',a) for a in audiences) or audiences!=sorted(set(audiences)):return False
        return value==sorted(value,key=lambda r:json.dumps(r,sort_keys=True))
    if check.kind == 'labels':
        return isinstance(value, list) and len(value) <= 512 and all(isinstance(v,str) and re.fullmatch(r'(category|group):[A-Za-z0-9_.-]{1,128}',v) for v in value) and len(value)==len(set(value)) and value==sorted(value)
    if check.values:
        return any(type(value) is type(v) and value == v for v in check.values)
    return type(value) is int and 0 <= value <= 1000000000


def project(raw, rt, suffix=""):
    """Only bounded booleans, integers and exact enums can leave this adapter."""
    output = {}
    for check in for_type(rt):
        if check.suffix != suffix:
            continue
        if check.operation == 'private_endpoint':
            output.update(project_private_endpoint(raw))
            continue
        value = get(raw.get('properties', {}), check.path, MISSING)
        output[check.id] = {'state':'missing'} if value is MISSING or value is None else {
            'state':'observed' if valid_value(check, value) else 'invalid',
            **({'value':value} if valid_value(check, value) else {})}
    state = get(raw,'properties.provisioningState')
    if state is not None and (not isinstance(state,str) or state.lower() not in ('succeeded','running')):
        for observation in output.values():
            if observation['state']=='observed':observation['state']='partial'
    return output


def validate_observations(values, rt):
    if not isinstance(values, dict):
        raise ValueError('Invalid configuration evidence')
    allowed = {c.id:c for c in for_type(rt)}
    for cid, row in values.items():
        if cid not in allowed or not isinstance(row, dict) or row.get('state') not in ('missing','invalid','observed','error','partial'):
            raise ValueError('Invalid configuration evidence')
        metadata = row.get('collection')
        if metadata is not None:
            if allowed[cid].operation not in ('diagnostics','diagnostic_routes','federation','authorization','backup_population','vmss_instances','container_revisions','backup_jobs','blob_containers','vault_metadata','vmss_members','automation_assets','automation_runtimes','log_tables') or not isinstance(metadata,dict) or set(metadata)!={'complete','pages','items_received','malformed','errors'} or type(metadata['complete']) is not bool or type(metadata['malformed']) is not bool or any(type(metadata[k]) is not int or metadata[k]<0 for k in ('pages','items_received')) or not isinstance(metadata['errors'],list):
                raise ValueError('Invalid collection metadata')
            for error in metadata['errors']:
                if not isinstance(error,dict) or set(error)-{'role_id'}!={'code','http_status'} or error['code'] not in ('http_error','network_error','retry_exhausted','fixture_response_missing','malformed_response','response_size_limit','malformed_page','pagination_scope_changed','pagination_cycle','pagination_limit','invalid_next_link','invalid_url','unsafe_url','redirect_rejected','authentication_failed') or not (error['http_status'] is None or type(error['http_status']) is int and 100<=error['http_status']<=599):
                    raise ValueError('Invalid collection error')
                if 'role_id' in error:
                    from .authorization import role_id
                    if allowed[cid].operation!='authorization' or not role_id(error['role_id']):
                        raise ValueError('Invalid unresolved role identity')
            if row['state']=='observed' and (not metadata['complete'] or metadata['malformed'] or metadata['errors'] or metadata['pages']==0):
                raise ValueError('Incomplete observation marked complete')
        if row['state'] in ('observed','partial'):
            if set(row) - {'collection'} != {'state','value'} or not valid_value(allowed[cid], row['value']):
                raise ValueError('Invalid configuration value')
        elif row['state'] == 'error':
            if set(row) != {'state','code','http_status'} or row['code'] not in ('http_error','network_error','retry_exhausted','fixture_response_missing','malformed_response','response_size_limit','invalid_detail_identity_or_properties','invalid_url','unsafe_url','redirect_rejected','authentication_failed') or not (row['http_status'] is None or type(row['http_status']) is int and 100 <= row['http_status'] <= 599):
                raise ValueError('Invalid configuration read error')
        elif set(row) - {'collection'} != {'state'}:
            raise ValueError('Invalid configuration state')


def validate_policy(policy):
    if policy is None:
        return None
    if not isinstance(policy, dict) or set(policy) - {'overrides','max_observation_age_seconds'} != {'schema_version','id','version','status','checks'}:
        raise ValueError('Invalid assessment criteria')
    if policy['schema_version'] != '1.0' or policy['status'] not in ('draft','approved'):
        raise ValueError('Invalid criteria version/status')
    if any(not isinstance(policy[k], str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',policy[k]) for k in ('id','version')):
        raise ValueError('Invalid criteria identity')
    if not isinstance(policy['checks'], dict) or set(policy['checks']) - set(CHECKS):
        raise ValueError('Unknown criterion')
    if 'max_observation_age_seconds' in policy and (type(policy['max_observation_age_seconds']) is not int or not 1 <= policy['max_observation_age_seconds'] <= 31536000):
        raise ValueError('Invalid freshness criterion')
    overrides=policy.get('overrides',{})
    if not isinstance(overrides,dict) or len(overrides)>10000:
        raise ValueError('Invalid criteria overrides')
    for rid,criteria in overrides.items():
        graph_id=isinstance(rid,str) and re.fullmatch(r'graph://[0-9a-f-]{36}/(applications|serviceprincipals)/[0-9a-f-]{36}',rid)
        if not isinstance(rid,str) or rid!=rid.lower() or not (resource_id(rid) or graph_id) or not isinstance(criteria,dict) or set(criteria)-set(CHECKS):
            raise ValueError('Invalid resource criteria override')
    for cid, criterion in [*policy['checks'].items(), *(item for criteria in overrides.values() for item in criteria.items())]:
        if not isinstance(criterion, dict) or set(criterion) != {'operator','value'}:
            raise ValueError('Invalid criterion')
        op, value = criterion['operator'], criterion['value']
        if op=='table_retention':
            from .log_tables import valid_criterion
            good=CHECKS[cid].kind=='log_tables' and valid_criterion(value)
        elif op=='asset_baseline':
            from .automation_assets import valid_criterion
            good=CHECKS[cid].kind=='automation_assets' and valid_criterion(value,CHECKS[cid].path)
        elif op=='lifecycle':
            from .vault_metadata import valid_criterion
            good=CHECKS[cid].kind=='vault_objects' and valid_criterion(value)
        elif op=='allowed_access':
            good=CHECKS[cid].kind=='container_access' and isinstance(value,list) and 1<=len(value)<=3 and all(isinstance(v,str) and v in ('None','Blob','Container') for v in value) and value==sorted(set(value))
        elif op=='recent_jobs':
            from .backup_jobs import valid_criterion
            good=CHECKS[cid].kind=='backup_jobs' and valid_criterion(CHECKS[cid],value)
        elif op == 'equals':
            good = valid_value(CHECKS[cid], value)
        elif op == 'one_of':
            good = isinstance(value, list) and 1 <= len(value) <= 16 and all(valid_value(CHECKS[cid],v) for v in value)
        elif op == 'at_least':
            good = CHECKS[cid].kind == 'scalar' and not CHECKS[cid].values and valid_value(CHECKS[cid], value)
        elif op == 'contains_all':
            good = CHECKS[cid].kind in ('labels','tokens','resource_ids','uuid_set') and bool(value) and valid_value(CHECKS[cid], value)
        else:
            good = False
        if not good:
            raise ValueError('Invalid criterion value/operator')
    return policy


def evaluate(snapshot, policy=None):
    validate_policy(policy)
    results = []
    generated_at = now()
    for record in snapshot['resources'] + snapshot.get('identity_evidence',{}).get('resources',[]):
        observations = record.get('configuration', {})
        for check in for_type(record['type']):
            observation = observations.get(check.id, {'state':'missing'})
            criterion = criterion_for(policy,record['id'],check.id)
            row = {'resource_id':record['id'], 'check_id':check.id, 'catalog_ref':check.catalog_ref,
                   'domain':check.catalog_ref.rsplit('-',1)[1], 'title':check.title,
                   'control_refs':OBJECTIVES['checks'][check.catalog_ref]['controls'],
                   'observed_at':record['collected_at'], 'observation':observation,
                   'criterion':criterion, 'source':check.source, 'api_version':check.api,
                   'property':check.path, 'request_path':record.get('request_path',record['id']) + check.suffix, 'result':'UNKNOWN', 'reason':'Required observation is missing or invalid.'}
            if check.operation=='vmss_members' and observation.get('value',{}).get('orchestration')=='Flexible':
                scope='/subscriptions/'+record['subscription_id']
                if observation['value']['scope']=='resource_group':scope+='/resourceGroups/'+record['resource_group']
                row['request_path']=scope+'/providers/Microsoft.Compute/virtualMachines'
            if check.operation=='vault_metadata':row['request_path']='https://'+record['id'].rsplit('/',1)[1].lower()+'.vault.azure.net/'+check.path
            if (record['collection_status'] == 'error' and not check.suffix) or observation['state'] == 'error' or observation.get('collection',{}).get('errors'):
                row.update(result='ERROR',reason='Resource configuration read failed.')
            elif not criterion or policy['status'] != 'approved':
                row['reason'] = 'Approved criterion is not supplied; observation retained without a positive or negative assessment.'
            elif observation['state'] == 'observed':
                actual, expected, op = observation['value'], criterion['value'], criterion['operator']
                if op=='table_retention':
                    from .log_tables import meets
                    passed=meets(actual,expected)
                    row.update(result='PASS' if passed else 'FAIL',reason='Required tables, permitted plans and minimum retention match the approved criterion.' if passed else 'Required table population, plan or retention does not match the approved criterion.')
                elif op=='asset_baseline':
                    from .automation_assets import baseline
                    passed=baseline(actual)==expected
                    row.update(result='PASS' if passed else 'FAIL',reason='Returned asset population and selected metadata match the approved baseline.' if passed else 'Returned asset population or selected metadata differ from the approved baseline.')
                elif op=='lifecycle':
                    from .vault_metadata import assess as assess_lifecycle
                    result,reason,details=assess_lifecycle(actual,expected,generated_at)
                    row.update(result=result,reason=reason,lifecycle_evaluation=details)
                elif op=='allowed_access':
                    passed=all(item['public_access'] in expected for item in actual)
                    row.update(result='PASS' if passed else 'FAIL',reason='Returned containers use only approved anonymous-access declarations.' if passed else 'A returned container has an unapproved anonymous-access declaration.')
                elif op=='recent_jobs':
                    from .backup_jobs import assess as assess_jobs
                    result,reason,details=assess_jobs(actual,expected,generated_at)
                    row.update(result=result,reason=reason,job_evaluation=details)
                else:
                    passed = actual == expected if op == 'equals' else actual in expected if op == 'one_of' else set(expected) <= set(actual) if op == 'contains_all' else actual >= expected
                    row.update(result='PASS' if passed else 'FAIL', reason='Observed configuration matches the supplied criterion.' if passed else 'Observed configuration does not match the supplied criterion.')
            if policy and 'max_observation_age_seconds' in policy:
                age = (datetime.fromisoformat(generated_at) - datetime.fromisoformat(record['collected_at'])).total_seconds()
                state = 'future' if age < 0 else 'stale' if age > policy['max_observation_age_seconds'] else 'fresh'
                row['freshness'] = {'state':state, 'as_of':generated_at, 'max_age_seconds':policy['max_observation_age_seconds']}
                if state != 'fresh' and row['result'] != 'ERROR':
                    row.update(result='UNKNOWN', reason='Observation is future-dated.' if state == 'future' else 'Observation exceeds the supplied freshness window.')
            results.append(row)
    counts = {s:0 for s in ('PASS','FAIL','UNKNOWN','ERROR')}
    counts.update(Counter(r['result'] for r in results))
    return {'schema_version':'1.0','rule_version':VERSION,'generated_at':generated_at, 'policy':policy, 'identity_complete':snapshot.get('identity_evidence',{}).get('complete',True),
            'limits':'Selected configuration, identity and reported-job predicates. Criteria approval is an operator assertion, not independently authenticated. Catalog references do not close whole objectives, effective access, network reachability or operating effectiveness.',
            'summary':{'check_count':len(results),'counts':counts,
                       'conclusion':'FAILURES_FOUND' if counts['FAIL'] else 'INCOMPLETE' if not results or counts['UNKNOWN'] or counts['ERROR'] or not snapshot.get('identity_evidence',{}).get('complete',True) else 'SELECTED_CONFIGURATION_CRITERIA_SATISFIED'},
            'results':results}


def overall_summary(report):
    encryption = report['summary']
    config = report.get('configuration_assessment', {}).get('summary')
    failures = encryption['counts']['FAIL'] + (config['counts']['FAIL'] if config else 0)
    incomplete = encryption['coverage_incomplete'] or bool(config and (config['conclusion']=='INCOMPLETE' or config['counts']['UNKNOWN'] or config['counts']['ERROR']))
    incomplete = incomplete or not report.get('configuration_assessment', {}).get('identity_complete', True)
    incomplete = incomplete or any(row.get('lifecycle_evaluation',{}).get('coverage_incomplete',False) for row in report.get('configuration_assessment',{}).get('results',[]))
    incomplete = incomplete or any(row.get('job_evaluation',{}).get('coverage_incomplete',False) for row in report.get('configuration_assessment',{}).get('results',[]))
    return {'conclusion':'FAILURES_FOUND' if failures else 'INCOMPLETE' if incomplete else 'SUPPORTED_SCOPE_SATISFIED',
            'coverage_incomplete':bool(incomplete), 'failed_check_count':failures}


def project_private_endpoint(raw):
    props=raw.get('properties',{})
    keys=('PE-targets','PE-approval','PE-subresources')
    normal,manual=props.get('privateLinkServiceConnections'),props.get('manualPrivateLinkServiceConnections')
    if not isinstance(normal,list) or not isinstance(manual,list) or not normal+manual:
        return {k:{'state':'missing'} for k in keys}
    targets,states,groups=set(),set(),set()
    for row in normal+manual:
        p=row.get('properties',{}) if isinstance(row,dict) else {}
        target=p.get('privateLinkServiceId');state=get(p,'privateLinkServiceConnectionState.status');subresources=p.get('groupIds')
        if not resource_id(target) or state not in ('Approved','Pending','Rejected','Disconnected') or not isinstance(subresources,list) or not subresources or not all(isinstance(g,str) and re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',g) for g in subresources):
            return {k:{'state':'invalid'} for k in keys}
        targets.add(target.lower());states.add(state);groups.update(subresources)
    return {key:{'state':'observed','value':sorted(values)} if valid_value(CHECKS[key],sorted(values)) else {'state':'invalid'} for key,values in zip(keys,(targets,states,groups))}


def decode_policy(text):
    if not isinstance(text,str) or len(text.encode('utf-8'))>1048576:raise ValueError('Criteria input too large')
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('Duplicate criteria member')
            result[key]=value
        return result
    def invalid_constant(value):raise ValueError('Invalid JSON constant')
    return validate_policy(json.loads(text,object_pairs_hook=unique,parse_constant=invalid_constant))


def criterion_for(policy,resource_id,check_id):
    if not policy:return None
    return policy.get('overrides',{}).get(resource_id.lower(),{}).get(check_id,policy['checks'].get(check_id))
