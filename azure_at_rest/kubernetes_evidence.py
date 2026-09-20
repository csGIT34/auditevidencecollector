"""Restricted Kubernetes PodList projection and exact-run workload supplements.

This imports operator-supplied API exports; it does not authenticate the exporter,
fetch Kubernetes credentials, or retain raw pod/environment/secret documents.
"""
from collections import Counter
import re
import json
from uuid import uuid4
from .archive import encode,digest,identity,load_run
from .controls import OBJECTIVES
from .safety import now
from .wiz import decode,fields,require,timestamp,token

RULE_VERSION='2026.09.20.1'
MAX_BYTES=4*1024*1024
CHECKS={'host_namespaces':'AKS-N','privileged':'AKS-C','allow_escalation':'AKS-C',
        'run_as_non_root':'AKS-C','readonly_root':'AKS-C','declared_digest':'AKS-V',
        'runtime_digest_known':'AKS-V','declared_runtime_digest_match':'AKS-V'}
LINUX={'privileged','allow_escalation','run_as_non_root','readonly_root'}
SOURCE='https://kubernetes.io/docs/reference/kubernetes-api/core/pod-v1/'


def name(value):
    require(isinstance(value,str) and len(value)<=253 and re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?',value))
    return value


def boolean(obj,key,default=None):
    value=obj.get(key,default);require(value is None or type(value) is bool);return value


def image(value):
    require(isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,511}(?:@sha256:[a-f0-9]{64})?',value))
    return value


def image_digest(value):
    if not isinstance(value,str):return None
    match=re.search(r'(?:@|://|^)sha256:([a-f0-9]{64})$',value)
    return match[1] if match else None


def project(document,saved,*,authenticated=False):
    fields(document,'schema_version kind mode cluster_id collected_at scope pods nodes')
    require(document['schema_version']=='1.0' and document['kind']=='kubernetes_export')
    require(document['mode'] in (('azure_live',) if authenticated else ('synthetic','operator_export')))
    require((document['mode']=='synthetic')==(saved['snapshot']['mode']=='offline_fixture'))
    cluster=document['cluster_id']
    require(isinstance(cluster,str) and cluster==cluster.lower())
    require(any(r['id'].lower()==cluster and r['type'].lower()=='microsoft.containerservice/managedclusters' for r in saved['snapshot']['resources']))
    timestamp(document['collected_at']);scope=document['scope'];fields(scope,'namespace pods_complete')
    require(type(scope['pods_complete']) is bool)
    if scope['namespace'] is not None:name(scope['namespace'])
    pods=document['pods'];nodes=document['nodes']
    require(isinstance(pods,dict) and pods.get('apiVersion')=='v1' and pods.get('kind')=='PodList' and isinstance(pods.get('metadata'),dict) and isinstance(pods.get('items'),list) and len(pods['items'])<=1000)
    require(isinstance(nodes,dict) and nodes.get('apiVersion')=='v1' and nodes.get('kind')=='NodeList' and isinstance(nodes.get('items'),list) and len(nodes['items'])<=10000)
    operating_systems={}
    for node in nodes['items']:
        node_name=name(node['metadata']['name']);require(node_name not in operating_systems)
        os=node.get('status',{}).get('nodeInfo',{}).get('operatingSystem')
        require(os in ('linux','windows',None));operating_systems[node_name]=os
    require(isinstance(pods['metadata'].get('continue',''),str))
    remaining=pods['metadata'].get('remainingItemCount',0);require(type(remaining) is int and remaining>=0)
    complete=scope['pods_complete'] and not bool(pods['metadata'].get('continue')) and pods['metadata'].get('remainingItemCount',0)==0
    rows=[];uids=set();identities=set();pod_ids=[]
    for pod in pods['items']:
        require(isinstance(pod,dict) and pod.get('apiVersion')=='v1' and pod.get('kind')=='Pod')
        meta=pod['metadata'];uid=meta['uid'];require(token(uid) and uid not in uids);uids.add(uid)
        namespace=name(meta['namespace']);pod_name=name(meta['name'])
        require((namespace,pod_name) not in identities);identities.add((namespace,pod_name))
        require(scope['namespace'] is None or namespace==scope['namespace'])
        spec=pod['spec'];require(isinstance(spec,dict));pod_security=spec.get('securityContext',{});require(isinstance(pod_security,dict))
        declared_os=spec.get('os',{}).get('name');node_os=operating_systems.get(spec.get('nodeName'))
        os=None if declared_os and node_os and declared_os!=node_os else declared_os or node_os
        require(os in ('linux','windows',None))
        host=[boolean(spec,key,False) for key in ('hostNetwork','hostPID','hostIPC')]
        host_access=True if True in host else None if None in host else False
        status=pod.get('status',{});require(isinstance(status,dict))
        seen_names=set();pod_ids.append({'uid':uid,'namespace':namespace,'name':pod_name})
        require(isinstance(spec.get('containers'),list) and spec['containers'])
        for key,status_key,kind in [('containers','containerStatuses','app'),('initContainers','initContainerStatuses','init'),('ephemeralContainers','ephemeralContainerStatuses','ephemeral')]:
            containers=spec.get(key,[]);require(isinstance(containers,list) and len(containers)<=100)
            declared_names=[name(c['name']) for c in containers];require(len(set(declared_names))==len(declared_names))
            statuses=status.get(status_key,[]);require(isinstance(statuses,list));digests={}
            for state in statuses:
                status_name=name(state['name']);require(status_name in declared_names and status_name not in digests)
                digests[status_name]=image_digest(state.get('imageID'))
            for container in containers:
                container_name=name(container['name']);require(container_name not in seen_names);seen_names.add(container_name)
                security=container.get('securityContext',{});require(isinstance(security,dict))
                declared=image(container['image']);declared_digest=image_digest(declared) if '@sha256:' in declared else None;runtime_digest=digests.get(container_name)
                privileged=boolean(security,'privileged',False)
                escalation=boolean(security,'allowPrivilegeEscalation',True)
                caps=security.get('capabilities',{});require(isinstance(caps,dict))
                added=caps.get('add',[]);require(isinstance(added,list) and all(isinstance(v,str) and re.fullmatch(r'[A-Z_]+',v) for v in added))
                if privileged is True or any(v in ('ALL','SYS_ADMIN','CAP_SYS_ADMIN') for v in added):escalation=True
                non_root=boolean(security,'runAsNonRoot',boolean(pod_security,'runAsNonRoot'))
                uid_value=security.get('runAsUser',pod_security.get('runAsUser'))
                require(uid_value is None or type(uid_value) is int and uid_value>=0)
                if uid_value==0:non_root=False
                facts={'host_namespaces':host_access,'privileged':privileged,'allow_escalation':escalation,
                       'run_as_non_root':non_root,'readonly_root':boolean(security,'readOnlyRootFilesystem',False),
                       'declared_digest':declared_digest is not None,'runtime_digest_known':True if runtime_digest else None,
                       'declared_runtime_digest_match':declared_digest==runtime_digest if declared_digest and runtime_digest else None}
                if os!='linux':
                    for check in LINUX:facts[check]=None
                rows.append({'record_id':uid+'--'+container_name,'pod_uid':uid,'namespace':namespace,'pod_name':pod_name,
                    'container_name':container_name,'container_kind':kind,'os':os,'declared_image':declared,
                    'runtime_sha256':runtime_digest,'observations':facts})
                require(len(rows)<=1000)
    return {'schema_version':'1.0','projection_version':RULE_VERSION,'kind':'kubernetes_projection','cluster_id':cluster,'mode':document['mode'],
            'collected_at':document['collected_at'],'scope':scope,'listing_complete':bool(complete),
            'pods':pod_ids,'containers':rows,'source':SOURCE}


def policy(value):
    if value is None:return None
    fields(value,'schema_version id version status checks')
    require(value['schema_version']=='1.0' and token(value['id']) and token(value['version']) and value['status'] in ('draft','approved'))
    require(isinstance(value['checks'],dict) and not set(value['checks'])-set(CHECKS) and all(type(v) is bool for v in value['checks'].values()))
    return value


def assess(projection,criteria,as_of,max_age_seconds):
    policy(criteria);reference=timestamp(as_of)
    require(type(max_age_seconds) is int and 1<=max_age_seconds<=31536000)
    age=(reference-timestamp(projection['collected_at'])).total_seconds()
    freshness='future' if age<0 else 'stale' if age>max_age_seconds else 'current'
    records=[];counts=Counter()
    for raw in projection['containers']:
        results={}
        for check,actual in raw['observations'].items():
            expected=criteria['checks'].get(check) if criteria else None
            result='UNKNOWN' if freshness!='current' or not criteria or criteria['status']!='approved' or expected is None or actual is None else 'PASS' if actual==expected else 'FAIL'
            counts[result]+=1;results[check]={'observed':actual,'expected':expected,'result':result,'objective_id':CHECKS[check]}
        records.append({**raw,'objective_ids':sorted(set(CHECKS.values())),'checks':results})
    incomplete=not projection['listing_complete'] or not records or bool(counts['UNKNOWN'])
    return {'rule_version':RULE_VERSION,'records':records,'criteria':criteria,'as_of':as_of,'max_age_seconds':max_age_seconds,'freshness':freshness,
            'summary':{'counts':{k:counts[k] for k in ('PASS','FAIL','UNKNOWN')},'coverage_incomplete':incomplete,
                       'conclusion':'FAILURES_FOUND' if counts['FAIL'] else 'INCOMPLETE' if incomplete else 'SELECTED_EXPORTED_CRITERIA_SATISFIED'}}


def markdown(report):
    # Serialize only projected fields; raw exports are never retained.
    return '# Kubernetes workload evidence\n\n```json\n'+json.dumps(report,indent=2,sort_keys=True)+'\n```\n'


def publish(store,run_id,data,*,criteria,as_of,max_age_seconds,deadline=None,provenance=None,collection_source=None):
    require(isinstance(data,bytes) and len(data)<=MAX_BYTES)
    saved=load_run(store,run_id)
    try:projection=project(decode(data),saved,authenticated=collection_source is not None)
    except (AttributeError,KeyError,TypeError,RecursionError):raise ValueError('invalid_kubernetes_export') from None
    report=assess(projection,criteria,as_of,max_age_seconds)
    evidence_id='k-'+uuid4().hex;prefix='workloads/'+evidence_id
    report.update(schema_version='1.0',kind='kubernetes_assessment',evidence_id=evidence_id,generated_at=now(),
        source_run_id=run_id,source_manifest_sha256=saved['manifest_sha256'],source_input_sha256=digest(data),
        source_scope={'cluster_id':projection['cluster_id'],'export_scope':projection['scope'],'listing_complete':projection['listing_complete']},
        mode=projection['mode'],source=SOURCE,max_age_hours=max_age_seconds/3600,
        objective_definitions={key:OBJECTIVES['checks'][key] for key in set(CHECKS.values())},
        limitations=['Operator-supplied Kubernetes export; exporter identity, selected cluster, time and completeness are not independently authenticated.',
        'Only projected pod/container security settings and image identities are archived. Raw environment, arguments, commands, annotations, addresses and secret contents are excluded.',
        'Results apply only to the supplied population. Unknown OS leaves Linux security checks unassessed; Windows controls require separate evidence.',
        'Container status may lag actual runtime. Image digests do not establish scan freshness, signatures or absence of vulnerabilities.',
        'These scoped predicates do not certify Kubernetes Pod Security Standards or close whole NIST objectives.'])
    if collection_source is not None:
        require(provenance is not None)
        report['collection_source']=collection_source
        report['limitations'][0]='Collected using the configured host identity against an ARM-verified AKS endpoint. Pod and node lists are separate snapshots; permissions, pagination limits and collection errors remain explicit.'
    if provenance is not None:
        from .provenance import validate_provenance
        report['execution_provenance']=validate_provenance(provenance)
        tenant=saved['context'].get('execution_provenance',{}).get('tenant_id')
        require(tenant is None or tenant.lower()==provenance['tenant_id'].lower())
    if deadline:deadline.check()
    store.put_new(prefix+'/intent.json',encode({'evidence_id':evidence_id,'source_run_id':run_id}))
    objects={}
    for name,data in [('projection.json',encode(projection)),('assessment.json',encode(report)),('report.md',markdown(report).encode())]:
        key=prefix+'/'+name;store.put_new(key,data);objects[name]={'key':key,'bytes':len(data),'sha256':digest(data)}
    manifest={'schema_version':'1.0','kind':'kubernetes_evidence','state':'complete','evidence_id':evidence_id,
              'source_run_id':run_id,'source_manifest_sha256':saved['manifest_sha256'],'generated_at':report['generated_at'],'summary':report['summary'],'objects':objects}
    store.put_new(prefix+'/manifest.json',encode(manifest));return manifest


def load(store,evidence_id):
    prefix='workloads/'+identity(evidence_id,'k');raw=store.read(prefix+'/manifest.json');manifest=decode(raw)
    require(manifest['schema_version']=='1.0' and manifest['kind']=='kubernetes_evidence' and manifest['state']=='complete' and manifest['evidence_id']==evidence_id)
    require(set(manifest['objects'])=={'projection.json','assessment.json','report.md'});objects={}
    for name,descriptor in manifest['objects'].items():
        require(descriptor['key']==prefix+'/'+name);data=store.read(descriptor['key'])
        require(digest(data)==descriptor['sha256'] and len(data)==descriptor['bytes']);objects[name]=data
    report=decode(objects['assessment.json']);projection=decode(objects['projection.json'])
    require(report['summary']==manifest['summary'])
    for key in ('source_run_id','source_manifest_sha256','evidence_id','generated_at'):require(report[key]==manifest[key])
    saved=load_run(store,manifest['source_run_id']);require(saved['manifest_sha256']==manifest['source_manifest_sha256'])
    require(report['source_scope']['cluster_id']==projection['cluster_id'] and len(report['records'])==len(projection['containers']))
    for record,projected in zip(report['records'],projection['containers']):require({k:record[k] for k in projected}==projected)
    return {'manifest':manifest,'manifest_sha256':digest(raw),'report':report,'projection':projection,'markdown':objects['report.md'].decode()}


def publish_pdf(store,evidence_id,*,deadline=None):
    from .operational import render_pdf
    saved=load(store,evidence_id);data=render_pdf({**saved['report'],'title':'Kubernetes workload evidence'})
    if deadline:deadline.check()
    report_id='p-'+uuid4().hex;prefix='workload-reports/'+report_id
    store.put_new(prefix+'/intent.json',encode({'report_id':report_id,'evidence_id':evidence_id}))
    store.put_new(prefix+'/report.pdf',data)
    manifest={'schema_version':'1.0','kind':'kubernetes_pdf','state':'complete','report_id':report_id,'evidence_id':evidence_id,
              'evidence_manifest_sha256':saved['manifest_sha256'],'generated_at':now(),'pdf':{'key':prefix+'/report.pdf','sha256':digest(data),'bytes':len(data)}}
    store.put_new(prefix+'/manifest.json',encode(manifest));return manifest
