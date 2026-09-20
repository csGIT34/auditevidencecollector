"""Typed guest/agent export assessments; vendor authentication is external."""
from collections import Counter
import json
from uuid import uuid4
from .archive import encode,digest,identity,load_run
from .controls import OBJECTIVES
from .safety import now
from .wiz import decode,fields,require,timestamp,token

MAX_BYTES=4*1024*1024
RULE_VERSION='2026.09.20.2'
CHECKS={'patch_age_seconds':'V','missing_critical_patches':'V','missing_security_patches':'V','reboot_pending':'V',
        'protection_age_seconds':'V','protection_enabled':'V','protection_healthy':'V',
        'scan_age_seconds':'V','critical_vulnerabilities':'V','high_vulnerabilities':'V'}
BOOL={'reboot_pending','protection_enabled','protection_healthy'}


def policy(value):
    if value is None:return None
    fields(value,'schema_version id version status checks')
    require(value['schema_version']=='1.0' and token(value['id']) and token(value['version']) and value['status'] in ('approved','draft'))
    checks=value['checks'];require(isinstance(checks,dict) and not set(checks)-set(CHECKS))
    for key,expected in checks.items():
        require(type(expected) is bool if key in BOOL else type(expected) is int and 0<=expected<=31536000)
    return value


def population(saved,selected):
    require(isinstance(selected,list) and selected and len(selected)<=1000 and all(isinstance(x,str) and x==x.lower() for x in selected) and len(set(selected))==len(selected))
    resources={r['id'].lower():r for r in saved['snapshot']['resources']};expected={};complete=True
    for rid in selected:
        require(rid in resources);resource=resources[rid];rt=resource['type'].lower()
        require(rt in ('microsoft.compute/virtualmachines','microsoft.compute/virtualmachinescalesets'))
        if rt.endswith('/virtualmachines'):expected.setdefault(rid,'VM')
        else:
            configuration=resource.get('configuration',{})
            membership=configuration.get('VMSS-instance-members',{})
            if membership.get('value',{}).get('orchestration')=='Flexible':
                complete=complete and membership.get('state')=='observed'
                members=membership['value']['members']
            else:
                observation=configuration.get('VMSS-instance-models',{})
                complete=complete and observation.get('state')=='observed'
                members=[item['instance_id'] for item in observation.get('value',[])]
            for member in members:expected[member]='VMSS'
            if not members:complete=False
    require(len(expected)<=10000)
    return expected,complete


def validate(document,saved):
    fields(document,'schema_version kind mode resource_ids records')
    require(document['schema_version']=='1.0' and document['kind']=='guest_export' and document['mode'] in ('synthetic','operator_export'))
    require((document['mode']=='synthetic')==(saved['snapshot']['mode']=='offline_fixture'))
    expected,complete=population(saved,document['resource_ids'])
    require(isinstance(document['records'],list) and len(document['records'])<=1000)
    seen=set()
    for row in document['records']:
        fields(row,'record_id resource_id source observed_at os patch protection vulnerabilities')
        require(token(row['record_id']) and token(row['source']) and row['resource_id'] in expected)
        key=(row['resource_id'],row['source']);require(key not in seen);seen.add(key)
        require(row['os'] in ('linux','windows','unknown'));observed=timestamp(row['observed_at'])
        for section,date_key,state_key,count_keys,bool_keys in [
            ('patch','assessed_at','state',('missing_critical','missing_security'),('reboot_pending',)),
            ('protection','reported_at',None,(),('enabled','healthy')),
            ('vulnerabilities','scanned_at','state',('critical','high'),())]:
            part=row[section]
            fields(part,' '.join((date_key,)+((state_key,) if state_key else ())+count_keys+bool_keys))
            if part[date_key] is not None:require(timestamp(part[date_key])<=observed)
            if state_key:require(part[state_key] in ('succeeded','failed','in_progress','unknown'))
            for key in count_keys:require(part[key] is None or type(part[key]) is int and 0<=part[key]<=100000000)
            for key in bool_keys:require(part[key] is None or type(part[key]) is bool)
    return expected,complete


def assess(document,saved,criteria,as_of,max_age_seconds):
    expected,complete=validate(document,saved);policy(criteria);reference=timestamp(as_of)
    require(type(max_age_seconds) is int and 1<=max_age_seconds<=31536000)
    rows=[];counts=Counter()
    for rid,service in sorted(expected.items()):
        matches=[r for r in document['records'] if r['resource_id']==rid]
        if not matches:matches=[None]
        for source in matches:
            facts={k:None for k in CHECKS}
            state='missing'
            if source:
                age=(reference-timestamp(source['observed_at'])).total_seconds()
                state='future' if age<0 else 'stale' if age>max_age_seconds else 'current'
                def age_of(section,key):
                    value=source[section][key]
                    if value is None:return None
                    seconds=(reference-timestamp(value)).total_seconds()
                    return seconds if seconds>=0 else None
                patch_age=age_of('patch','assessed_at');protection_age=age_of('protection','reported_at');scan_age=age_of('vulnerabilities','scanned_at')
                facts.update(patch_age_seconds=patch_age if source['patch']['state']=='succeeded' else None,
                             protection_age_seconds=protection_age,scan_age_seconds=scan_age if source['vulnerabilities']['state']=='succeeded' else None)
                checks=criteria['checks'] if criteria and criteria['status']=='approved' else {}
                if source['patch']['state']=='succeeded' and patch_age is not None and patch_age<=checks.get('patch_age_seconds',-1):
                    facts.update(missing_critical_patches=source['patch']['missing_critical'],missing_security_patches=source['patch']['missing_security'],reboot_pending=source['patch']['reboot_pending'])
                if protection_age is not None and protection_age<=checks.get('protection_age_seconds',-1):
                    facts.update(protection_enabled=source['protection']['enabled'],protection_healthy=source['protection']['healthy'])
                if source['vulnerabilities']['state']=='succeeded' and scan_age is not None and scan_age<=checks.get('scan_age_seconds',-1):
                    facts.update(critical_vulnerabilities=source['vulnerabilities']['critical'],high_vulnerabilities=source['vulnerabilities']['high'])
            decisions={}
            for key,actual in facts.items():
                limit=criteria['checks'].get(key) if criteria else None
                result='UNKNOWN' if state!='current' or actual is None or limit is None or not criteria or criteria['status']!='approved' else 'PASS' if (actual==limit if key in BOOL else actual<=limit) else 'FAIL'
                counts[result]+=1;decisions[key]={'observed':actual,'expected':limit,'result':result,'objective_id':service+'-'+CHECKS[key]}
            rows.append({'record_id':'guest-'+digest(encode([rid,source['source'] if source else None]))[:24],'resource_id':rid,'source_record':source,'freshness':state,'checks':decisions,'objective_ids':sorted({service+'-'+v for v in CHECKS.values()})})
    incomplete=not complete or not rows or bool(counts['UNKNOWN'])
    return {'rule_version':RULE_VERSION,'records':rows,'criteria':criteria,'as_of':as_of,'max_age_hours':max_age_seconds/3600,
            'summary':{'counts':{k:counts[k] for k in ('PASS','FAIL','UNKNOWN')},'coverage_incomplete':incomplete,
                       'conclusion':'FAILURES_FOUND' if counts['FAIL'] else 'INCOMPLETE' if incomplete else 'SELECTED_EXPORTED_CRITERIA_SATISFIED'},
            'source_scope':{'resource_ids':document['resource_ids'],'expected_guest_ids':sorted(expected),'population_complete':complete}}


def publish(store,run_id,data,*,criteria,as_of,max_age_seconds,deadline=None,provenance=None):
    require(isinstance(data,bytes) and len(data)<=MAX_BYTES);document=decode(data);saved=load_run(store,run_id)
    try:report=assess(document,saved,criteria,as_of,max_age_seconds)
    except (KeyError,TypeError,AttributeError,RecursionError):raise ValueError('invalid_guest_export') from None
    evidence_id='g-'+uuid4().hex;prefix='guests/'+evidence_id
    report.update(schema_version='1.0',kind='guest_assessment',evidence_id=evidence_id,source_run_id=run_id,
        source_manifest_sha256=saved['manifest_sha256'],source_input_sha256=digest(data),generated_at=now(),mode=document['mode'],
        objective_definitions={key:OBJECTIVES['checks'][key] for row in report['records'] for key in row['objective_ids']},
        limitations=['Typed operator export; vendor authentication, source identity, measurements and normalization are not independently verified.',
        'Only the selected saved VM population is assessed. VMSS instances come from saved Uniform instance evidence or Flexible membership evidence; missing/partial populations remain incomplete. Individual VM selection is also supported.',
        'No guest commands, agent installation, remediation, package paths, usernames or raw vendor payloads are collected.',
        'Patch and vulnerability counts need succeeded, current source assessments. Endpoint protection values need a current report. Missing criteria or facts remain UNKNOWN.',
        'Multiple source reports are assessed separately. A passing source never suppresses another source failure or missing evidence.',
        'These measurements do not establish complete scanner coverage, patch installation success, agent tamper protection or whole NIST control effectiveness.'])
    if provenance is not None:
        from .provenance import validate_provenance
        report['execution_provenance']=validate_provenance(provenance)
        tenant=saved['context'].get('execution_provenance',{}).get('tenant_id');require(tenant is None or tenant.lower()==provenance['tenant_id'].lower())
    if deadline:deadline.check()
    store.put_new(prefix+'/intent.json',encode({'evidence_id':evidence_id,'source_run_id':run_id}));objects={}
    for filename,payload in [('input.json',data),('assessment.json',encode(report)),('report.md',('# Guest and agent evidence\n\n```json\n'+json.dumps(report,indent=2,sort_keys=True)+'\n```\n').encode())]:
        key=prefix+'/'+filename;store.put_new(key,payload);objects[filename]={'key':key,'bytes':len(payload),'sha256':digest(payload)}
    manifest={'schema_version':'1.0','kind':'guest_evidence','state':'complete','evidence_id':evidence_id,'source_run_id':run_id,
              'source_manifest_sha256':saved['manifest_sha256'],'generated_at':report['generated_at'],'summary':report['summary'],'objects':objects}
    store.put_new(prefix+'/manifest.json',encode(manifest));return manifest


def load(store,evidence_id):
    prefix='guests/'+identity(evidence_id,'g');raw=store.read(prefix+'/manifest.json');manifest=decode(raw)
    require(manifest['schema_version']=='1.0' and manifest['kind']=='guest_evidence' and manifest['state']=='complete' and manifest['evidence_id']==evidence_id)
    require(set(manifest['objects'])=={'input.json','assessment.json','report.md'});objects={}
    for name,descriptor in manifest['objects'].items():
        require(descriptor['key']==prefix+'/'+name);data=store.read(descriptor['key'])
        require(digest(data)==descriptor['sha256'] and len(data)==descriptor['bytes']);objects[name]=data
    saved=load_run(store,manifest['source_run_id']);require(saved['manifest_sha256']==manifest['source_manifest_sha256'])
    report=decode(objects['assessment.json']);document=decode(objects['input.json'])
    # Frozen decisions are verified by hashes and linkage, never re-evaluated on read.
    for key in ('evidence_id','source_run_id','source_manifest_sha256','generated_at','summary'):require(report[key]==manifest[key])
    require(report['source_input_sha256']==digest(objects['input.json']) and report['mode']==document['mode'])
    require(report['source_scope']['resource_ids']==document['resource_ids'])
    require([row['source_record'] for row in report['records'] if row['source_record']] == sorted(document['records'],key=lambda r:r['resource_id']))
    return {'manifest':manifest,'manifest_sha256':digest(raw),'report':report,'markdown':objects['report.md'].decode()}


def publish_pdf(store,evidence_id,*,deadline=None):
    from .operational import render_pdf
    saved=load(store,evidence_id);data=render_pdf({**saved['report'],'title':'Guest and agent evidence'})
    if deadline:deadline.check()
    report_id='p-'+uuid4().hex;prefix='guest-reports/'+report_id
    store.put_new(prefix+'/intent.json',encode({'report_id':report_id,'evidence_id':evidence_id}));store.put_new(prefix+'/report.pdf',data)
    manifest={'schema_version':'1.0','kind':'guest_pdf','state':'complete','report_id':report_id,'evidence_id':evidence_id,
              'evidence_manifest_sha256':saved['manifest_sha256'],'generated_at':now(),'pdf':{'key':prefix+'/report.pdf','bytes':len(data),'sha256':digest(data)}}
    store.put_new(prefix+'/manifest.json',encode(manifest));return manifest
