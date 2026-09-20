"""Bind enabled diagnostic log categories to their configured destinations."""
import json
import re
from .safety import resource_id

DESTINATIONS={'workspace_id':'workspaceId','storage_id':'storageAccountId',
              'eventhub_rule_id':'eventHubAuthorizationRuleId','partner_id':'marketplacePartnerId'}


def valid_routes(value):
    if not isinstance(value,list) or len(value)>512:return False
    seen=set()
    for row in value:
        if not isinstance(row,dict) or set(row)!={'setting_id','logs','eventhub_name','workspace_table_mode',*DESTINATIONS}:return False
        if not resource_id(row['setting_id']) or row['setting_id']!=row['setting_id'].lower() or '/providers/microsoft.insights/diagnosticsettings/' not in row['setting_id'] or row['setting_id'] in seen:return False
        seen.add(row['setting_id'])
        logs=row['logs']
        if not isinstance(logs,list) or not logs or len(logs)>512 or not all(isinstance(v,str) and re.fullmatch(r'(category|group):[A-Za-z0-9_.-]{1,128}',v) for v in logs) or logs!=sorted(set(logs)):return False
        if not any(row[k] for k in DESTINATIONS):return False
        for key in DESTINATIONS:
            v=row[key]
            if v is not None and (not resource_id(v) or v!=v.lower()):return False
        for key,pattern in {'workspace_id':r'/providers/microsoft.operationalinsights/workspaces/[^/]+$', 'storage_id':r'/providers/microsoft.storage/storageaccounts/[^/]+$', 'eventhub_rule_id':r'/providers/microsoft.eventhub/namespaces/[^/]+/authorizationrules/[^/]+$'}.items():
            if row[key] is not None and not re.search(pattern,row[key]):return False
        if row['eventhub_name'] is not None and (not row['eventhub_rule_id'] or not isinstance(row['eventhub_name'],str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,256}',row['eventhub_name'])):return False
        if row['workspace_table_mode'] not in (None,'Dedicated','AzureDiagnostics'):return False
        if row['workspace_table_mode'] is not None and row['workspace_id'] is None:return False
    return value==sorted(value,key=lambda r:json.dumps(r,sort_keys=True))


def project(settings,path,listing,errors):
    routes=[];seen=set();malformed=False
    for raw in settings:
        try:
            if not isinstance(raw,dict) or not isinstance(raw.get('id'),str) or raw['id'].lower().rsplit('/',1)[0]!=path.lower() or raw['id'].lower() in seen or not isinstance(raw.get('properties'),dict):raise ValueError()
            seen.add(raw['id'].lower());props=raw['properties'];logs=props.get('logs')
            if not isinstance(logs,list):raise ValueError()
            enabled=[]
            for log in logs:
                if not isinstance(log,dict) or type(log.get('enabled')) is not bool:raise ValueError()
                if not log['enabled']:continue
                if bool(log.get('category'))==bool(log.get('categoryGroup')):raise ValueError()
                enabled.append('category:'+str(log['category']) if log.get('category') else 'group:'+str(log['categoryGroup']))
            if not enabled:continue
            row={'setting_id':raw['id'].lower(),'logs':sorted(set(enabled)),
                 'eventhub_name':None if props.get('eventHubName') in (None,'') else props['eventHubName'],
                 'workspace_table_mode':None if props.get('logAnalyticsDestinationType') in (None,'') else props['logAnalyticsDestinationType']}
            for key,api_key in DESTINATIONS.items():
                v=props.get(api_key)
                row[key]=v.lower() if isinstance(v,str) and v else None if v is None or v=='' else v
            if not valid_routes([row]):raise ValueError()
            routes.append(row)
        except (ValueError,TypeError,KeyError,AttributeError):malformed=True
    routes.sort(key=lambda r:json.dumps(r,sort_keys=True))
    return {'state':'observed' if listing['complete'] and not malformed and not errors else 'partial','value':routes,
            'collection':{**listing,'malformed':malformed,'errors':[{k:e[k] for k in ('code','http_status')} for e in errors]}}
