"""Key Vault base-object LIST metadata only; never GET object values or versions."""
from datetime import datetime
import re
import time
from urllib.parse import urlsplit,parse_qs
from .collector import ArmTransport,CollectionError
from .wiz import require

API='2025-07-01'
KINDS=('keys','secrets','certificates')
ATTRS=('created','updated','nbf','exp')


def origin(value):
    if not isinstance(value,str) or not re.fullmatch(r'https://[a-z][a-z0-9-]{1,22}[a-z0-9]\.vault\.azure\.net/?',value):raise CollectionError('unsafe_url')
    return value.rstrip('/')


def valid_url(url,base,kind=None):
    try:
        require(isinstance(url,str) and len(url)<=16384 and not any(c in url for c in '\r\n\\'))
        p=urlsplit(url);host=urlsplit(origin(base)).hostname
        paths=('/'+kind,) if kind else tuple('/'+v for v in KINDS)
        require(p.scheme=='https' and p.hostname==host and p.netloc in (host,host+':443') and not p.fragment and p.path in paths)
        q=parse_qs(p.query,keep_blank_values=True,strict_parsing=True)
        require(q.get('api-version')==[API] and not set(q)-{'api-version','maxresults','$skiptoken'} and all(len(v)==1 for v in q.values()))
        if 'maxresults' in q:require(q['maxresults'][0].isdigit() and 1<=int(q['maxresults'][0])<=25)
        return p
    except (ValueError,TypeError,AttributeError):raise CollectionError('unsafe_url') from None


class Credential:
    def __init__(self,credential):self.credential=credential
    def get_token(self):
        try:
            token=self.credential.get_token('https://vault.azure.net/.default')
            require(isinstance(token.token,str) and token.token and not any(c in token.token for c in '\r\n') and token.expires_on>time.time())
            return token.token
        except Exception:raise CollectionError('authentication_failed') from None


class VaultTransport(ArmTransport):
    def __init__(self,base,credential,deadline,retries=2):
        self.base=origin(base);self.deadline=deadline
        super().__init__(Credential(credential),retries=retries,sleep=deadline.sleep)
        self.max_response_bytes=4*1024*1024
    def validate_url(self,url):return valid_url(url,self.base)
    def get(self,url):
        self.deadline.check();self.timeout=min(30,self.deadline.remaining())
        result=super().get(url);self.deadline.check();return result


class FixtureVaultTransport:
    def __init__(self,base,responses):self.base,self.responses=origin(base),responses
    def get(self,url):
        valid_url(url,self.base)
        if url not in self.responses:raise CollectionError('fixture_response_missing')
        result=self.responses[url]
        if 'fixture_error' in result:raise CollectionError('http_error',result['fixture_error'])
        return result


def project(item,base,kind):
    require(isinstance(item,dict));identifier=item.get('kid' if kind=='keys' else 'id');require(isinstance(identifier,str))
    require(re.fullmatch(re.escape(base)+'/'+kind+r'/[A-Za-z0-9-]{1,127}',identifier) is not None)
    attrs=item.get('attributes');require(isinstance(attrs,dict))
    value={'object_id':identifier,'enabled':attrs.get('enabled'),**{key:attrs.get(key) for key in ATTRS}}
    require(value['enabled'] is None or type(value['enabled']) is bool)
    for key in ATTRS:require(value[key] is None or type(value[key]) is int and 0<=value[key]<=253402300799)
    if value['created'] is not None and value['updated'] is not None:require(value['created']<=value['updated'])
    if value['nbf'] is not None and value['exp'] is not None:require(value['nbf']<=value['exp'])
    return value


def valid_objects(value,kind):
    if not isinstance(value,list) or len(value)>10000:return False
    try:
        seen=set()
        for item in value:
            require(isinstance(item,dict) and set(item)=={'object_id','enabled',*ATTRS})
            identifier=item['object_id'];require(isinstance(identifier,str));base='https://'+urlsplit(identifier).netloc;origin(base)
            require(identifier not in seen);seen.add(identifier)
            require(project({'kid' if kind=='keys' else 'id':identifier,'attributes':{k:item[k] for k in ('enabled',)+ATTRS}},base,kind)==item)
        return value==sorted(value,key=lambda v:v['object_id'])
    except (ValueError,TypeError,KeyError,CollectionError):return False


def collect(arm,rid,check,max_pages,parent):
    factory=getattr(arm,'vault_transport_factory',None)
    if factory is None:return {'state':'missing'}
    try:
        if parent['properties'].get('provisioningState') not in (None,'Succeeded'):return {'state':'missing'}
        base=origin(parent['properties']['vaultUri'])
        if base!='https://'+rid.rsplit('/',1)[1].lower()+'.vault.azure.net':raise CollectionError('unsafe_url')
        transport=factory(base)
    except (KeyError,TypeError,AttributeError,CollectionError):return {'state':'invalid'}
    kind=check.path;url=base+'/'+kind+'?api-version='+API+'&maxresults=25'
    seen=set();ids=set();values=[];pages=0;received=0;malformed=False;errors=[];complete=False
    try:
        while url:
            valid_url(url,base,kind)
            if url in seen:raise CollectionError('pagination_cycle')
            if pages>=min(max_pages,400):raise CollectionError('pagination_limit')
            seen.add(url);data=transport.get(url)
            if not isinstance(data,dict) or not isinstance(data.get('value'),list):raise CollectionError('malformed_page')
            pages+=1;received+=len(data['value'])
            if received>10000:raise CollectionError('pagination_limit')
            for item in data['value']:
                try:
                    value=project(item,base,kind)
                    if value['object_id'] in ids:raise ValueError()
                    ids.add(value['object_id']);values.append(value)
                except (ValueError,TypeError,KeyError):malformed=True
            url=data.get('nextLink')
            if url is not None and (not isinstance(url,str) or not url):raise CollectionError('invalid_next_link')
        complete=True
    except CollectionError as error:errors.append({'code':error.code,'http_status':error.status})
    return {'state':'observed' if complete and not malformed else 'partial','value':sorted(values,key=lambda v:v['object_id']),
            'collection':{'complete':complete,'pages':pages,'items_received':received,'malformed':malformed,'errors':errors}}


def valid_criterion(value):
    return isinstance(value,dict) and set(value)=={'enabled_only','require_expiration','min_remaining_seconds'} and type(value['enabled_only']) is bool and type(value['require_expiration']) is bool and type(value['min_remaining_seconds']) is int and 0<=value['min_remaining_seconds']<=31536000


def assess(values,criterion,as_of):
    reference=datetime.fromisoformat(as_of).timestamp();outcomes=[]
    for value in values:
        state=None
        if criterion['enabled_only']:
            if value['enabled'] is None:state='UNKNOWN'
            elif not value['enabled']:state='EXCLUDED_DISABLED'
        if state is None:
            if any(value[key] is not None and value[key]>reference for key in ('created','updated')):state='UNKNOWN'
            else:
                expiry=value['exp']
                state='FAIL' if expiry is None and criterion['require_expiration'] or expiry is not None and (expiry<=reference or expiry-reference<criterion['min_remaining_seconds']) else 'PASS'
        outcomes.append({'object_id':value['object_id'],'state':state})
    states=[o['state'] for o in outcomes if o['state']!='EXCLUDED_DISABLED']
    incomplete='UNKNOWN' in states or not states
    result='FAIL' if 'FAIL' in states else 'UNKNOWN' if incomplete else 'PASS'
    return result,'Listed base-object expiration metadata evaluated at '+as_of+'; versions, rotation execution and effective usability are not established.',{'as_of':as_of,'outcomes':outcomes,'coverage_incomplete':incomplete}
