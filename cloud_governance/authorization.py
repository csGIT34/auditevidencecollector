"""Read-only ARM assignment and role-definition projections. Not effective access."""
import hashlib
import json
import re
from urllib.parse import parse_qs, urlsplit
from .safety import resource_id, subscription_id

API = '2022-04-01'
SOURCE = 'https://learn.microsoft.com/en-us/rest/api/authorization/role-assignments/list-for-scope?view=rest-authorization-2022-04-01'
DEFINITION_SOURCE = 'https://learn.microsoft.com/en-us/rest/api/authorization/role-definitions/get?view=rest-authorization-2022-04-01'
SUFFIX = '/providers/Microsoft.Authorization/roleAssignments'
GUID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'


def scope(value):
    if not isinstance(value,str) or value != value.lower():return False
    return value == '/' or bool(re.fullmatch(r'/subscriptions/'+GUID+r'(/resourcegroups/[a-z0-9_.()-]{1,90})?',value)) or bool(re.fullmatch(r'/providers/microsoft.management/managementgroups/[a-z0-9_.()-]{1,90}',value)) or bool(resource_id(value))


def role_id(value):
    if not isinstance(value,str):return False
    match = re.fullmatch(r'(.*)/providers/microsoft.authorization/roledefinitions/('+GUID+r')',value)
    return bool(match and (not match[1] or scope(match[1])))


def permissions(value):
    if not isinstance(value,list) or not 1 <= len(value) <= 128:return False
    for block in value:
        if not isinstance(block,dict) or set(block) != {'actions','notActions','dataActions','notDataActions'}:return False
        for actions in block.values():
            if not isinstance(actions,list) or len(actions)>10000 or not all(isinstance(a,str) and re.fullmatch(r'[a-z0-9.*_/-]{1,512}',a) for a in actions) or actions != sorted(set(actions)):return False
    return value == sorted(value,key=lambda b:json.dumps(b,sort_keys=True))


def valid_grants(value):
    if not isinstance(value,list) or len(value)>10000:return False
    seen=set()
    for row in value:
        if not isinstance(row,dict) or set(row)!={'assignment_id','principal_id','principal_type','scope','role_id','role_type','permissions','condition_sha256','condition_version','delegated_identity'}:return False
        if not scope(row['scope']) or not role_id(row['role_id']) or (not isinstance(row['principal_id'],str) or subscription_id(row['principal_id']) != row['principal_id']) or row['principal_type'] not in ('User','Group','ServicePrincipal','ForeignGroup','Device'):return False
        prefix='' if row['scope']=='/' else row['scope']
        if not isinstance(row['assignment_id'],str) or not re.fullmatch(re.escape(prefix)+r'/providers/microsoft.authorization/roleassignments/'+GUID,row['assignment_id']) or row['assignment_id'] in seen:return False
        seen.add(row['assignment_id'])
        if row['role_type'] not in ('BuiltInRole','CustomRole') or not permissions(row['permissions']):return False
        if row['condition_sha256'] is not None and (not isinstance(row['condition_sha256'],str) or not re.fullmatch(r'[0-9a-f]{64}',row['condition_sha256'])):return False
        if row['condition_version'] not in (None,'1.0','2.0') or bool(row['condition_sha256']) != bool(row['condition_version']):return False
        if row['delegated_identity'] is not None and (not isinstance(row['delegated_identity'],str) or row['delegated_identity'] != row['delegated_identity'].lower() or not resource_id(row['delegated_identity'])):return False
    return value == sorted(value,key=lambda row:json.dumps(row,sort_keys=True))


def collect(transport, rid, max_pages, cache):
    from .collector import Collector, CollectionError, endpoint
    class FilteredTransport:
        def get(self,url):
            query=parse_qs(urlsplit(url).query)
            if query.get('$filter', ['atScope()']) != ['atScope()'] or query.get('api-version') != [API] or set(query)-{'$filter','api-version','$skipToken','$skiptoken'}:
                raise CollectionError('pagination_scope_changed')
            return transport.get(url)
    reader=Collector(FilteredTransport(),max_pages)
    path=rid+SUFFIX
    raw,listing=reader.paged(endpoint(path,API)+'&$filter=atScope%28%29',rid,'authorization_assignments')
    safe=[];seen=set();malformed=False;errors=[]
    sid=rid.lower().split('/')[2]
    for item in raw:
        try:
            if not isinstance(item,dict) or not isinstance(item.get('properties'),dict):raise ValueError()
            props=item['properties'];assignment_id=item['id'].lower();assigned_scope=props['scope'].lower()
            if assignment_id in seen:raise ValueError()
            seen.add(assignment_id)
            if not scope(assigned_scope):raise ValueError()
            # atScope() admits declared ancestor assignments; unrelated subscription/resource scopes cannot escape it.
            if assigned_scope.startswith('/subscriptions/') and not (rid.lower()==assigned_scope or rid.lower().startswith(assigned_scope+'/')):raise ValueError()
            definition_id=props['roleDefinitionId'].lower()
            if not role_id(definition_id):raise ValueError()
            definition_guid=definition_id.rsplit('/',1)[1]
            lookup=rid+'/providers/Microsoft.Authorization/roleDefinitions/'+definition_guid
            cache_key=(sid,definition_id)
            if cache_key not in cache:
                try:
                    definition=transport.get(endpoint(lookup,API))
                    if not isinstance(definition,dict) or not isinstance(definition.get('id'),str) or not role_id(definition['id'].lower()) or definition['id'].lower() not in (definition_id,lookup.lower()) or not isinstance(definition.get('properties'),dict):raise ValueError()
                    body=definition['properties'];blocks=[]
                    if not isinstance(body.get('permissions'),list):raise ValueError()
                    for block in body['permissions']:
                        if not isinstance(block,dict):raise ValueError()
                        copied={}
                        for key in ('actions','notActions','dataActions','notDataActions'):
                            actions=block.get(key)
                            if not isinstance(actions,list) or not all(isinstance(a,str) for a in actions):raise ValueError()
                            copied[key]=sorted(set(a.lower() for a in actions))
                        blocks.append(copied)
                    blocks.sort(key=lambda b:json.dumps(b,sort_keys=True))
                    if body.get('type') not in ('BuiltInRole','CustomRole') or not permissions(blocks):raise ValueError()
                    cache[cache_key]={'role_type':body['type'],'permissions':blocks}
                except CollectionError as exc:
                    cache[cache_key]={'error':{'code':exc.code,'http_status':exc.status}}
                except (ValueError,KeyError,TypeError,AttributeError):
                    cache[cache_key]={'error':{'code':'malformed_response','http_status':None}}
            definition=cache[cache_key]
            if 'error' in definition:
                errors.append({**definition['error'],'role_id':definition_id});continue
            condition=props.get('condition');version=props.get('conditionVersion')
            if condition is not None and (not isinstance(condition,str) or len(condition)>16384):raise ValueError()
            if not condition:condition=None;version=None
            delegated=props.get('delegatedManagedIdentityResourceId')
            row={'assignment_id':assignment_id,'principal_id':props['principalId'].lower(),
                 'principal_type':props.get('principalType'),'scope':assigned_scope,'role_id':definition_id,
                 **definition,'condition_sha256':hashlib.sha256(condition.encode()).hexdigest() if condition else None,
                 'condition_version':version,'delegated_identity':delegated.lower() if isinstance(delegated,str) else delegated}
            if not valid_grants([row]):raise ValueError()
            safe.append(row)
        except (ValueError,KeyError,TypeError,AttributeError):malformed=True
    safe.sort(key=lambda row:json.dumps(row,sort_keys=True))
    errors += [{k:e[k] for k in ('code','http_status')} for e in reader.errors]
    metadata={**listing,'malformed':malformed,'errors':errors}
    return {'state':'observed' if listing['complete'] and not malformed and not errors else 'partial',
            'value':safe,'collection':metadata}


def valid_delegated_grants(value):
    if not isinstance(value,list) or len(value)>10000:return False
    for row in value:
        if not isinstance(row,dict) or set(row)!={'clientId','resourceId','consentType','principalId','scopes'}:return False
        if any(not isinstance(row[k],str) or subscription_id(row[k])!=row[k] for k in ('clientId','resourceId')):return False
        if row['consentType']=='AllPrincipals':
            if row['principalId'] is not None:return False
        elif row['consentType']=='Principal':
            if not isinstance(row['principalId'],str) or subscription_id(row['principalId'])!=row['principalId']:return False
        else:return False
        scopes=row['scopes']
        if not isinstance(scopes,list) or len(scopes)>512 or not all(isinstance(s,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,256}',s) for s in scopes) or scopes != sorted(set(scopes)):return False
    return value==sorted(value,key=lambda row:json.dumps(row,sort_keys=True)) and len({json.dumps(row,sort_keys=True) for row in value})==len(value)
