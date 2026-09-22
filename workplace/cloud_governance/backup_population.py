"""Safe backup population/status evidence. No restore, backup or credential actions."""
import json
import re
from .safety import resource_id

DP_STATES={'Invalid','NotProtected','ConfiguringProtection','ProtectionConfigured','BackupSchedulesSuspended',
           'RetentionSchedulesSuspended','ProtectionStopped','ProtectionError','ConfiguringProtectionFailed',
           'SoftDeleting','SoftDeleted','UpdatingProtection'}
RS_STATES={'Invalid','IRPending','Protected','ProtectionError','ProtectionStopped','ProtectionPaused','BackupsSuspended'}
RS_STATUS={'Healthy','Unhealthy','Warning','Critical','Invalid','IRPending'}


def valid_population(value, family):
    if not isinstance(value,list) or len(value)>10000:return False
    seen=set()
    for row in value:
        if not isinstance(row,dict) or set(row)!={'item_id','source_id','policy_id','state','status'}:return False
        if not all(isinstance(row[k],str) and row[k]==row[k].lower() for k in ('item_id','source_id','policy_id')):return False
        if row['item_id'] in seen or not resource_id(row['source_id']) or not resource_id(row['policy_id']):return False
        seen.add(row['item_id'])
        if not isinstance(row['state'],str) or not isinstance(row['status'],str):return False
        if family=='dataprotection':
            match=re.fullmatch(r'(.*/providers/microsoft.dataprotection/backupvaults/[^/]+)/backupinstances/([a-z0-9_.()-]+)',row['item_id'])
            good=row['state'] in DP_STATES and row['status'] in DP_STATES
        else:
            match=re.fullmatch(r'(.*/providers/microsoft.recoveryservices/vaults/[^/]+)/backupfabrics/[a-z0-9_.()-]+/protectioncontainers/[a-z0-9_.(); -]+/protecteditems/[a-z0-9_.(); -]+',row['item_id'])
            good=row['state'] in RS_STATES and row['status'] in RS_STATUS
        if not match or not resource_id(match[1]) or not good or row['policy_id'].rsplit('/',2)[0]!=match[1] or row['policy_id'].rsplit('/',2)[1]!='backuppolicies':return False
    return value==sorted(value,key=lambda r:json.dumps(r,sort_keys=True))


def collect(transport,rid,check,max_pages):
    from .collector import Collector, endpoint
    reader=Collector(transport,max_pages)
    raw,listing=reader.paged(endpoint(rid+check.suffix,check.api),rid,'backup_population')
    family='dataprotection' if check.kind=='dp_population' else 'recovery'
    values=[];seen=set();malformed=False
    for item in raw:
        try:
            if not isinstance(item,dict) or not isinstance(item.get('id'),str) or not item['id'].lower().startswith(rid.lower()+'/') or item['id'].lower() in seen or not isinstance(item.get('properties'),dict):raise ValueError()
            seen.add(item['id'].lower());p=item['properties']
            if family=='dataprotection':
                row={'item_id':item['id'].lower(),'source_id':p['dataSourceInfo']['resourceID'].lower(),
                     'policy_id':p['policyInfo']['policyId'].lower(),'state':p['currentProtectionState'],'status':p['protectionStatus']['status']}
            else:
                row={'item_id':item['id'].lower(),'source_id':p['sourceResourceId'].lower(),
                     'policy_id':p['policyId'].lower(),'state':p['protectionState'],'status':p['protectionStatus']}
            if not valid_population([row],family):raise ValueError()
            values.append(row)
        except (ValueError,KeyError,TypeError,AttributeError):malformed=True
    values.sort(key=lambda r:json.dumps(r,sort_keys=True))
    return {'state':'observed' if listing['complete'] and not malformed else 'partial','value':values,
            'collection':{**listing,'malformed':malformed,'errors':[{k:e[k] for k in ('code','http_status')} for e in reader.errors]}}
