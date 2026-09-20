"""Bounded, read-only AKS API collection using the host's explicit identity."""
import re
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener
from .archive import encode, load_run
from .collector import CollectionError, NoRedirect, endpoint
from .kubernetes_evidence import MAX_BYTES, name, policy, publish
from .safety import now
from .workflow import DeadlineExceeded
from .wiz import decode, fields, require

AUDIENCE='6dae42f8-4368-4678-94ff-3960e28e3630/.default'
AKS_API='2024-10-01'


def target(value):
    fields(value,'cluster_id endpoint ca_pem namespace criteria max_age_seconds')
    cluster=value['cluster_id']
    require(isinstance(cluster,str) and cluster==cluster.lower() and re.fullmatch(r'/subscriptions/[a-f0-9-]{36}/resourcegroups/[^/]+/providers/microsoft.containerservice/managedclusters/[a-z0-9_-]+',cluster))
    url=value['endpoint'];require(isinstance(url,str))
    parsed=urlsplit(url)
    require(parsed.scheme=='https' and parsed.netloc==parsed.hostname and parsed.path in ('','/') and not parsed.query and not parsed.fragment)
    require(bool(re.fullmatch(r'[a-z0-9]+(?:[a-z0-9.-]*[a-z0-9])?',parsed.hostname or '')) and '.' in parsed.hostname)
    ca=value['ca_pem'];require(isinstance(ca,str) and len(ca)<=65536 and ca.startswith('-----BEGIN CERTIFICATE-----') and 'PRIVATE KEY' not in ca)
    if value['namespace'] is not None:name(value['namespace'])
    policy(value['criteria']);require(type(value['max_age_seconds']) is int and 1<=value['max_age_seconds']<=31536000)
    return value


class KubernetesTransport:
    def __init__(self, configuration, credential, deadline, retries=2, opener=None):
        target(configuration)
        self.base=configuration['endpoint'].rstrip('/');self.credential=credential;self.deadline=deadline
        require(type(retries) is int and 0<=retries<=3);self.retries=retries
        # Explicit CA, certificate and hostname verification; no proxy or redirect token forwarding.
        context=ssl.create_default_context(cadata=configuration['ca_pem'])
        self.opener=opener or build_opener(ProxyHandler({}),HTTPSHandler(context=context),NoRedirect())
        ns=configuration['namespace']
        self.paths={'/api/v1/nodes','/api/v1/pods' if ns is None else '/api/v1/namespaces/'+ns+'/pods'}

    def get(self,path,continuation):
        require(path in self.paths and isinstance(continuation,str) and len(continuation)<=16384)
        url=self.base+path+'?'+urlencode({'limit':100,**({'continue':continuation} if continuation else {})})
        for attempt in range(self.retries+1):
            self.deadline.check()
            try:
                token=self.credential.get_token(AUDIENCE)
                require(isinstance(token.token,str) and token.token and not any(c in token.token for c in '\r\n') and token.expires_on>time.time())
            except Exception:raise CollectionError('authentication_failed') from None
            self.deadline.check()
            request=Request(url,headers={'Authorization':'Bearer '+token.token,'Accept':'application/json'},method='GET')
            try:
                with self.opener.open(request,timeout=min(30,self.deadline.remaining())) as response:
                    raw=response.read(MAX_BYTES+1)
                self.deadline.check()
                if len(raw)>MAX_BYTES:raise CollectionError('response_size_limit')
                result=decode(raw)
                if not isinstance(result,dict):raise ValueError()
                return result
            except HTTPError as error:
                status=error.code;error.close()
                if status in (429,500,502,503,504) and attempt<self.retries:
                    self.deadline.sleep(2**attempt);continue
                raise CollectionError('http_error',status) from None
            except DeadlineExceeded:raise
            except (URLError,TimeoutError,OSError):
                if attempt<self.retries:self.deadline.sleep(2**attempt);continue
                raise CollectionError('network_error') from None
            except (ValueError,UnicodeError,RecursionError):raise CollectionError('malformed_response') from None


def listing(transport,path,kind,*,max_pages,max_items):
    items=[];version=None;continuation='';seen=set();size=0
    def finish(code,status=None):
        return {'apiVersion':'v1','kind':kind,'metadata':{'continue':'' if code=='complete' else 'incomplete'},'items':items}, {'state':code,'http_status':status,'pages':len(seen)}
    for _ in range(max_pages):
        try:
            page=transport.get(path,continuation);metadata=page.get('metadata',{})
            require(page.get('apiVersion')=='v1' and page.get('kind')==kind and isinstance(metadata,dict) and isinstance(page.get('items'),list))
            current=metadata.get('resourceVersion');require(isinstance(current,str) and current and len(current)<=256)
            if version is not None and version!=current:return finish('resource_version_changed')
            next_token=metadata.get('continue','');require(isinstance(next_token,str) and len(next_token)<=16384)
            remaining=metadata.get('remainingItemCount',0);require(type(remaining) is int and remaining>=0)
            if not next_token and remaining:return finish('malformed_response')
            size+=len(encode(page))
            if size>MAX_BYTES or len(items)+len(page['items'])>max_items:return finish('population_limit')
            version=current;items.extend(page['items']);seen.add(continuation)
            if not next_token:return finish('complete')
            if next_token in seen:return finish('pagination_cycle')
            continuation=next_token
        except CollectionError as error:return finish(error.code,error.status)
        except (ValueError,TypeError,AttributeError,RecursionError):return finish('malformed_response')
    return finish('page_limit')


def collect(store,run_id,configuration,arm,credential,deadline,*,provenance,max_pages=100,retries=2,transport_factory=KubernetesTransport):
    target(configuration);require(type(max_pages) is int and 1<=max_pages<=10000)
    saved=load_run(store,run_id);cluster=configuration['cluster_id']
    require(saved['snapshot']['mode']=='azure_live')
    require(any(r['id'].lower()==cluster and r['type'].lower()=='microsoft.containerservice/managedclusters' for r in saved['snapshot']['resources']))
    started=now()
    data=arm.get(endpoint(cluster,AKS_API));properties=data.get('properties',{})
    host=urlsplit(configuration['endpoint']).hostname
    require(str(data.get('id','')).lower()==cluster and isinstance(properties,dict))
    require(host in (properties.get('fqdn'),properties.get('privateFQDN')))
    # Require managed Entra integration for the fixed AKS audience.
    require(properties.get('aadProfile',{}).get('managed') is True)
    transport=transport_factory(configuration,credential,deadline,retries)
    ns=configuration['namespace'];path='/api/v1/pods' if ns is None else '/api/v1/namespaces/'+ns+'/pods'
    pods,pod_state=listing(transport,path,'PodList',max_pages=min(max_pages,100),max_items=1000)
    nodes,node_state=listing(transport,'/api/v1/nodes','NodeList',max_pages=min(max_pages,100),max_items=10000)
    doc={'schema_version':'1.0','kind':'kubernetes_export','mode':'azure_live','cluster_id':cluster,'collected_at':started,
         'scope':{'namespace':ns,'pods_complete':pod_state['state']==node_state['state']=='complete'},'pods':pods,'nodes':nodes}
    source={'authentication':'host_identity_aks_audience','endpoint_validation':'fresh_arm_cluster_fqdn',
            'tls':'configured_ca_and_hostname','pods':pod_state,'nodes':node_state,'started_at':started,'finished_at':now()}
    return publish(store,run_id,encode(doc),criteria=configuration['criteria'],as_of=now(),max_age_seconds=configuration['max_age_seconds'],deadline=deadline,provenance=provenance,collection_source=source)
