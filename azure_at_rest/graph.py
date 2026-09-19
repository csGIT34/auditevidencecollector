"""Opt-in Microsoft Graph metadata collection, with tenant and URL boundaries."""
from datetime import datetime, timezone
import re
import json
from urllib.parse import urlsplit
from .collector import ArmTransport, CollectionError
from .safety import subscription_id, now
from .controls import CHECKS, valid_value, validate_observations

ORIGIN='https://graph.microsoft.com'
GUID=r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'


def valid_url(url):
    if not isinstance(url,str):raise CollectionError('invalid_url')
    try:p=urlsplit(url)
    except ValueError:raise CollectionError('invalid_url') from None
    if (p.scheme!='https' or p.netloc!='graph.microsoft.com' or p.fragment or '\\' in url
            or any(c in url for c in '\r\n') or not re.fullmatch(r'/v1.0/(organization|applications|servicePrincipals)(/'+GUID+r'(/(owners|appRoleAssignments|federatedIdentityCredentials))?)?',p.path)):
        raise CollectionError('unsafe_url')
    return p


class GraphTransport(ArmTransport):
    validate_url=staticmethod(valid_url)


class GraphCredential:
    def __init__(self,credential):self.credential=credential
    def get_token(self):
        import time
        try:
            token=self.credential.get_token(ORIGIN+'/.default')
            if not isinstance(token.token,str) or not token.token or any(c in token.token for c in '\r\n') or token.expires_on<=time.time():raise ValueError()
            return token.token
        except Exception:raise CollectionError('authentication_failed') from None


class BudgetGraphTransport(GraphTransport):
    def __init__(self,credential,deadline,retries=2):
        super().__init__(GraphCredential(credential),retries=retries,sleep=deadline.sleep)
        self.deadline=deadline
    def get(self,url):
        self.deadline.check(); self.timeout=min(30,self.deadline.remaining())
        result=super().get(url);self.deadline.check();return result


class FixtureGraphTransport:
    def __init__(self,responses):self.responses,self.calls=responses,[]
    def get(self,url):
        valid_url(url);self.calls.append(url)
        if url not in self.responses:raise CollectionError('fixture_response_missing')
        row=self.responses[url]
        if isinstance(row,dict) and 'fixture_error' in row:raise CollectionError('http_error',row['fixture_error'])
        return row


class GraphCollector:
    def __init__(self,transport,tenant_id,max_pages=1000):
        if subscription_id(tenant_id)!=tenant_id or type(max_pages) is not int or max_pages<1:raise ValueError('Invalid Graph scope')
        self.transport,self.tenant,self.max_pages=transport,tenant_id,max_pages
        self.errors=[]
    def listing(self,path,select):
        url=ORIGIN+'/v1.0/'+path+'?$select='+select
        expected=valid_url(url).path
        rows,seen,pages,complete=[],set(),0,False
        try:
            while url:
                if valid_url(url).path!=expected:raise CollectionError('pagination_scope_changed')
                if url in seen:raise CollectionError('pagination_cycle')
                if pages>=self.max_pages:raise CollectionError('pagination_limit')
                seen.add(url);page=self.transport.get(url)
                if not isinstance(page,dict) or not isinstance(page.get('value'),list):raise CollectionError('malformed_page')
                rows.extend(page['value']);pages+=1
                url=page.get('@odata.nextLink')
                if url is not None and (not isinstance(url,str) or not url):raise CollectionError('invalid_next_link')
                if url is None:complete=True
        except CollectionError as exc:
            self.errors.append({'path':expected,'code':exc.code,'http_status':exc.status,'observed_at':now()})
        return rows,{'complete':complete,'pages':pages,'items_received':len(rows)}

    def collect(self):
        started=now();records=[];listings={}
        org,listing=self.listing('organization','id');listings['organization']=listing
        verified=listing['complete'] and len(org)==1 and isinstance(org[0],dict) and subscription_id(org[0].get('id'))==self.tenant
        if verified:
            for collection,select in [('applications','id,appId,signInAudience,passwordCredentials,keyCredentials'),('servicePrincipals','id,appId,accountEnabled')]:
                rows,listing=self.listing(collection,select);listings[collection]=listing
                seen=set()
                for raw in rows:
                    if (not isinstance(raw,dict) or not subscription_id(raw.get('id')) or not subscription_id(raw.get('appId')) or raw['id'].lower() in seen):
                        listing['complete']=False
                        continue
                    oid,appid=raw['id'].lower(),raw['appId'].lower();seen.add(oid)
                    is_app=collection=='applications'
                    record={'id':f'graph://{self.tenant}/{collection}/{oid}','object_id':oid,'app_id':appid,
                            'type':'graph.application' if is_app else 'graph.servicePrincipal',
                            'request_path':'/v1.0/'+collection+'/'+oid,'collected_at':now(),
                            'collection_status':'ok','configuration':{},'metadata':{}}
                    cid='APPREG-audience' if is_app else 'APPREG-sp-enabled'
                    value=raw.get('signInAudience' if is_app else 'accountEnabled')
                    record['configuration'][cid]={'state':'observed','value':value} if valid_value(CHECKS[cid],value) else {'state':'missing' if value is None else 'invalid'}
                    child='owners' if is_app else 'appRoleAssignments'
                    children,child_listing=self.listing(collection+'/'+oid+'/'+child,'id' if is_app else 'id,principalId,resourceId,appRoleId')
                    listings[collection+'/'+oid+'/'+child]=child_listing
                    safe=[];child_seen=set()
                    for item in children:
                        if not isinstance(item,dict):
                            child_listing['complete']=False;continue
                        ident=item.get('id')
                        if is_app:
                            key=subscription_id(ident)
                        else:
                            key=(subscription_id(ident) or ident) if isinstance(ident,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,256}',ident) else None
                        if not key or key in child_seen:
                            child_listing['complete']=False;continue
                        child_seen.add(key)
                        if is_app:safe.append({'object_id':item['id'].lower()})
                        elif all(subscription_id(item.get(k)) for k in ('principalId','resourceId','appRoleId')) and item['principalId'].lower()==oid:
                            safe.append({k:item[k].lower() for k in ('principalId','resourceId','appRoleId')})
                        else:child_listing['complete']=False
                    safe.sort(key=lambda r:json.dumps(r,sort_keys=True))
                    record['metadata'][child]=safe
                    set_id='APPREG-approved-owners' if is_app else 'APPREG-approved-role-grants'
                    set_value=sorted({r['object_id'] for r in safe}) if is_app else safe
                    record['configuration'][set_id]={'state':'observed' if child_listing['complete'] else 'partial','value':set_value}
                    count_id='APPREG-owner-count' if is_app else 'APPREG-role-grants'
                    record['configuration'][count_id]={'state':'observed' if child_listing['complete'] else 'partial','value':len(safe)}
                    if is_app:
                        federation,fed_listing=self.listing('applications/'+oid+'/federatedIdentityCredentials','id,issuer,subject,audiences')
                        listings['applications/'+oid+'/federatedIdentityCredentials']=fed_listing
                        trusts=[];seen_federation=set()
                        for item in federation:
                            if not isinstance(item,dict) or not subscription_id(item.get('id')) or item['id'].lower() in seen_federation:
                                fed_listing['complete']=False;continue
                            seen_federation.add(item['id'].lower())
                            trust={k:item.get(k) for k in ('issuer','subject','audiences')}
                            if isinstance(trust['audiences'],list) and all(isinstance(a,str) for a in trust['audiences']):trust['audiences']=sorted(set(trust['audiences']))
                            if not valid_value(CHECKS['APPREG-federation-trust'],[trust]):fed_listing['complete']=False;continue
                            trusts.append(trust)
                        trusts.sort(key=lambda r:json.dumps(r,sort_keys=True))
                        record['configuration']['APPREG-federation-trust']={'state':'observed' if fed_listing['complete'] else 'partial','value':trusts} if valid_value(CHECKS['APPREG-federation-trust'],trusts) else {'state':'invalid'}
                        credentials=[];valid=True;expired=0
                        for kind in ('passwordCredentials','keyCredentials'):
                            items=raw.get(kind)
                            if not isinstance(items,list):valid=False;continue
                            for item in items:
                                try:
                                    if not isinstance(item,dict) or not subscription_id(item.get('keyId')):raise ValueError()
                                    start=datetime.fromisoformat(item['startDateTime']);end=datetime.fromisoformat(item['endDateTime'])
                                    if start.tzinfo is None or end.tzinfo is None or end<start:raise ValueError()
                                    credentials.append({'kind':kind,'key_id':item['keyId'].lower(),'start':start.isoformat(),'end':end.isoformat()})
                                    expired+=int(end<=datetime.fromisoformat(record['collected_at']))
                                except (ValueError,TypeError,KeyError):valid=False
                        record['metadata']['credentials']=credentials
                        record['configuration']['APPREG-expired-credentials']={'state':'observed' if valid else 'partial','value':expired}
                    record['collected_at']=now()
                    if is_app:
                        record['configuration']['APPREG-expired-credentials']['value']=sum(datetime.fromisoformat(c['end'])<=datetime.fromisoformat(record['collected_at']) for c in record['metadata']['credentials'])
                    records.append(record)
        if listing['complete'] and not verified and not self.errors:
            self.errors.append({'path':'/v1.0/organization','code':'tenant_mismatch','http_status':None,'observed_at':now()})
        complete=verified and bool(listings) and all(v['complete'] for v in listings.values()) and not self.errors
        return {'schema_version':'1.0','tenant_id':self.tenant,'verified_tenant':bool(verified),'started_at':started,'completed_at':now(),
                'complete':bool(complete),'listings':listings,'resources':records,'errors':self.errors}


def validate_identity_evidence(value):
    if not isinstance(value,dict) or set(value)!={'schema_version','tenant_id','verified_tenant','started_at','completed_at','complete','listings','resources','errors'}:raise ValueError('Invalid Graph evidence')
    if value['schema_version']!='1.0' or subscription_id(value['tenant_id'])!=value['tenant_id'] or type(value['verified_tenant']) is not bool or type(value['complete']) is not bool:raise ValueError('Invalid Graph identity')
    for k in ('started_at','completed_at'):
        if datetime.fromisoformat(value[k]).tzinfo is None:raise ValueError('Invalid Graph timestamp')
    if not isinstance(value['resources'],list) or not isinstance(value['listings'],dict) or not isinstance(value['errors'],list):raise ValueError('Invalid Graph population')
    seen=set()
    for row in value['resources']:
        if not isinstance(row,dict) or set(row)!={'id','object_id','app_id','type','request_path','collected_at','collection_status','configuration','metadata'}:raise ValueError('Invalid Graph record')
        collection='applications' if row['type']=='graph.application' else 'servicePrincipals' if row['type']=='graph.servicePrincipal' else None
        if not collection or subscription_id(row['object_id'])!=row['object_id'] or subscription_id(row['app_id'])!=row['app_id']:raise ValueError('Invalid Graph object identity')
        if row['id']!=f"graph://{value['tenant_id']}/{collection}/{row['object_id']}" or row['id'] in seen or row['request_path']!='/v1.0/'+collection+'/'+row['object_id'] or row['collection_status']!='ok':raise ValueError('Graph identity mismatch')
        if datetime.fromisoformat(row['collected_at']).tzinfo is None:raise ValueError('Invalid observation time')
        seen.add(row['id']);validate_observations(row['configuration'],row['type'])
        metadata=row['metadata']
        allowed={'owners','credentials'} if collection=='applications' else {'appRoleAssignments'}
        if not isinstance(metadata,dict) or set(metadata)!=allowed:raise ValueError('Invalid Graph metadata')
        for kind,rows in metadata.items():
            if not isinstance(rows,list):raise ValueError('Invalid Graph metadata population')
            for item in rows:
                fields={'object_id'} if kind=='owners' else {'kind','key_id','start','end'} if kind=='credentials' else {'principalId','resourceId','appRoleId'}
                if not isinstance(item,dict) or set(item)!=fields:raise ValueError('Invalid Graph safe projection')
                for k,v in item.items():
                    if k in ('start','end'):
                        if datetime.fromisoformat(v).tzinfo is None:raise ValueError('Invalid credential metadata time')
                    elif k=='kind':
                        if v not in ('passwordCredentials','keyCredentials'):raise ValueError('Invalid credential kind')
                    elif subscription_id(v)!=v:raise ValueError('Invalid projected identity')
        config=row['configuration']
        if collection=='applications':
            owners=sorted({r['object_id'] for r in metadata['owners']})
            if len(owners)!=len(metadata['owners']):raise ValueError('Duplicate saved owner')
            if config['APPREG-owner-count'].get('value')!=len(owners) or config['APPREG-approved-owners'].get('value')!=owners:raise ValueError('Owner evidence mismatch')
            if any(datetime.fromisoformat(c['end'])<datetime.fromisoformat(c['start']) for c in metadata['credentials']):raise ValueError('Invalid credential interval')
            expired=sum(datetime.fromisoformat(c['end'])<=datetime.fromisoformat(row['collected_at']) for c in metadata['credentials'])
            if config['APPREG-expired-credentials'].get('value')!=expired:raise ValueError('Credential evidence mismatch')
        else:
            grants=metadata['appRoleAssignments']
            if any(g['principalId']!=row['object_id'] for g in grants) or config['APPREG-role-grants'].get('value')!=len(grants) or config['APPREG-approved-role-grants'].get('value')!=grants:raise ValueError('Grant evidence mismatch')
    for name,listing in value['listings'].items():
        valid_url(ORIGIN+'/v1.0/'+name)
        if not isinstance(listing,dict) or set(listing)!={'complete','pages','items_received'} or type(listing['complete']) is not bool or any(type(listing[k]) is not int or listing[k]<0 for k in ('pages','items_received')) or listing['complete'] and listing['pages']==0:raise ValueError('Invalid Graph listing')
    for error in value['errors']:
        if not isinstance(error,dict) or set(error)!={'path','code','http_status','observed_at'}:raise ValueError('Invalid Graph error')
        valid_url(ORIGIN+error['path'])
        if error['code'] not in ('tenant_mismatch','http_error','network_error','authentication_failed','retry_exhausted','fixture_response_missing','malformed_response','malformed_page','pagination_scope_changed','pagination_cycle','pagination_limit','invalid_next_link','invalid_url','unsafe_url','redirect_rejected') or not (error['http_status'] is None or type(error['http_status']) is int and 100<=error['http_status']<=599) or datetime.fromisoformat(error['observed_at']).tzinfo is None:raise ValueError('Invalid Graph safe error')
    if value['verified_tenant'] and ('organization' not in value['listings'] or not value['listings']['organization']['complete'] or value['listings']['organization']['items_received']!=1):raise ValueError('Missing verified tenant listing')
    if value['verified_tenant']:
        if not {'organization','applications','servicePrincipals'} <= set(value['listings']):
            raise ValueError('Missing Graph population listings')
        for collection, resource_type in (('applications','graph.application'),('servicePrincipals','graph.servicePrincipal')):
            population = sum(row['type']==resource_type for row in value['resources'])
            listing = value['listings'][collection]
            if population > listing['items_received'] or listing['complete'] and population != listing['items_received']:
                raise ValueError('Graph population completeness mismatch')
        for row in value['resources']:
            collection = 'applications' if row['type']=='graph.application' else 'servicePrincipals'
            children = [('owners',('APPREG-owner-count','APPREG-approved-owners')), ('federatedIdentityCredentials',('APPREG-federation-trust',))] if collection=='applications' else [('appRoleAssignments',('APPREG-role-grants','APPREG-approved-role-grants'))]
            for child, checks in children:
                listing = value['listings'].get(collection+'/'+row['object_id']+'/'+child)
                if listing is None or not listing['complete'] and any(row['configuration'].get(check,{}).get('state')=='observed' for check in checks):
                    raise ValueError('Graph child completeness mismatch')
    expected=value['verified_tenant'] and bool(value['listings']) and all(v['complete'] for v in value['listings'].values()) and not value['errors']
    if value['complete']!=expected or not value['verified_tenant'] and value['resources']:raise ValueError('Invalid Graph completeness')
