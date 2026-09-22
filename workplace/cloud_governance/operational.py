"""Immutable attributed operating records linked to an exact saved run."""
from collections import Counter
from io import BytesIO
import json
import math
import re
from uuid import uuid4
from xml.sax.saxutils import escape

from .archive import digest,encode,identity,load_run
from .controls import OBJECTIVES
from .safety import now
from .wiz import decode,fields,require,timestamp,token

MAX_BYTES=1024*1024
KINDS={'restore_test','access_review','change_record','incident_record','remediation_record',
       'vulnerability_report','patch_report','workload_review','provider_attestation','exception'}


def validate(document,saved):
    require(isinstance(document,dict))
    fields(document,'schema_version kind mode records'+(' requirements' if 'requirements' in document else ''))
    require(document['schema_version']=='1.0' and document['kind']=='operational_evidence')
    require(document['mode'] in ('synthetic','operator_supplied'))
    require((document['mode']=='synthetic')==(saved['snapshot']['mode']=='offline_fixture'))
    require(isinstance(document['records'],list) and len(document['records'])<=1000 and (document['records'] or document.get('requirements')))
    resources={r['id'].lower() for r in saved['snapshot']['resources']+saved['snapshot'].get('identity_evidence',{}).get('resources',[])}
    seen=set()
    for record in document['records']:
        fields(record,'record_id evidence_type objective_ids scope_kind resource_ids period_start period_end observed_at owner reviewer assertion summary reference_sha256')
        require(token(record['record_id']) and record['record_id'] not in seen);seen.add(record['record_id'])
        require(record['evidence_type'] in KINDS and token(record['owner']) and token(record['reviewer']))
        require(record['assertion'] in ('SATISFIED','NOT_SATISFIED','NOT_ASSESSED'))
        require(isinstance(record['objective_ids'],list) and record['objective_ids'] and all(isinstance(v,str) and v in OBJECTIVES['checks'] for v in record['objective_ids']) and len(set(record['objective_ids']))==len(record['objective_ids']))
        ids=record['resource_ids']
        require(isinstance(ids,list) and len(ids)<=10000 and all(isinstance(v,str) and v in resources for v in ids) and len(set(ids))==len(ids))
        require(record['scope_kind'] in ('run','resources') and bool(ids)==(record['scope_kind']=='resources'))
        start,end,observed=(timestamp(record[k]) for k in ('period_start','period_end','observed_at'))
        require(start<=end and start<=observed)
        if record['evidence_type']!='exception':require(end<=observed)
        summary=record['summary']
        require(isinstance(summary,str) and 1<=len(summary)<=8192 and all(c in '\n\t' or ord(c)>=32 and ord(c)!=127 for c in summary))
        ref=record['reference_sha256']
        require(ref is None or isinstance(ref,str) and re.fullmatch(r'[0-9a-f]{64}',ref))
    requirements=document.get('requirements',[])
    require(isinstance(requirements,list) and len(requirements)<=1000)
    seen=set()
    for item in requirements:
        fields(item,'requirement_id evidence_type objective_id scope_kind resource_ids period_start period_end')
        require(token(item['requirement_id']) and item['requirement_id'] not in seen);seen.add(item['requirement_id'])
        require(item['evidence_type'] in KINDS and isinstance(item['objective_id'],str) and item['objective_id'] in OBJECTIVES['checks'])
        ids=item['resource_ids']
        require(isinstance(ids,list) and all(isinstance(v,str) and v in resources for v in ids) and len(set(ids))==len(ids))
        require(item['scope_kind'] in ('run','resources') and bool(ids)==(item['scope_kind']=='resources'))
        require(timestamp(item['period_start'])<=timestamp(item['period_end']))
    return document


def review(document,saved,as_of,max_age_hours):
    reference=timestamp(as_of)
    require(type(max_age_hours) in (int,float) and math.isfinite(max_age_hours) and 0<max_age_hours<=87600)
    records=[]
    for raw in document['records']:
        age=(reference-timestamp(raw['observed_at'])).total_seconds()
        state='FUTURE' if age<0 else 'STALE' if age>max_age_hours*3600 else 'CURRENT'
        if raw['evidence_type']=='exception' and timestamp(raw['period_end'])<reference:state='EXPIRED_EXCEPTION'
        records.append({**raw,'freshness':state})
    requirements=[]
    for expected in document.get('requirements',[]):
        # Evaluate each required resource separately. A run statement cannot silently satisfy resource evidence.
        population=expected['resource_ids'] if expected['scope_kind']=='resources' else [None]
        for resource in population:
            matched=[row for row in records if row['evidence_type']==expected['evidence_type']
                     and expected['objective_id'] in row['objective_ids'] and row['scope_kind']==expected['scope_kind']
                     and (resource is None or resource in row['resource_ids'])
                     and timestamp(row['period_start'])<=timestamp(expected['period_start'])
                     and timestamp(row['period_end'])>=timestamp(expected['period_end'])]
            current=[row for row in matched if row['freshness']=='CURRENT']
            assertions={row['assertion'] for row in current}
            state=('MISSING' if not matched else 'NO_CURRENT_EVIDENCE' if not current else
                   'CONFLICTING_ASSERTIONS' if 'SATISFIED' in assertions and 'NOT_SATISFIED' in assertions else
                   'ASSERTED_NOT_SATISFIED' if 'NOT_SATISFIED' in assertions else
                   'ASSERTED_SATISFIED' if assertions=={'SATISFIED'} else 'NOT_ASSESSED')
            requirements.append({'requirement_id':expected['requirement_id'],'resource_id':resource,
                                 'state':state,'record_ids':sorted(row['record_id'] for row in matched)})
    objectives={key:OBJECTIVES['checks'][key] for record in records for key in record['objective_ids']}
    objectives.update({item['objective_id']:OBJECTIVES['checks'][item['objective_id']] for item in document.get('requirements',[])})
    return {'schema_version':'1.0','kind':'operational_evidence_review','source_run_id':saved['manifest']['run_id'],
            'source_manifest_sha256':saved['manifest_sha256'],'source_scope':saved['manifest']['scope'],'as_of':as_of,'max_age_hours':max_age_hours,
            'mode':document['mode'],'records':records,'freshness_counts':dict(Counter(r['freshness'] for r in records)),
            'objective_definitions':objectives,'requirements':document.get('requirements',[]),'requirement_results':requirements,
            'requirement_counts':dict(Counter(row['state'] for row in requirements)),
            'limitations':['Records are operator-supplied statements, not independently authenticated observations.',
                          'Owner, reviewer, assertion and document hash are declared by the importer; referenced documents are not fetched or verified.',
                          'CURRENT means within the selected age window, not that the assertion or control is satisfied.',
                          'Human/provider assertions do not overwrite automated findings or close research objectives.',
                          'A run-scoped statement refers only to the exact saved run scope; it does not establish full tenant coverage.',
                          'Exceptions do not suppress findings. Expired exceptions remain visible.']}


def markdown(report):
    def text(value):return str(value).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    lines=['# Operational evidence supplement','',f"Source run: {report['source_run_id']}",
           f"Source manifest SHA-256: {report['source_manifest_sha256']}",f"As of: {report['as_of']}",
           f"Maximum evidence age: {report['max_age_hours']} hours",f"Mode: {report['mode']}",'',
           '## Interpretation','']+['- '+text(v) for v in report['limitations']]
    for item in report.get('requirements',[]):lines+=['','Required evidence: '+text(json.dumps(item,sort_keys=True))]
    for item in report.get('requirement_results',[]):lines+=['','Requirement outcome: '+text(json.dumps(item,sort_keys=True))]
    for row in report['records']:
        lines+=['','## '+text(row['record_id']),'']
        for key,value in row.items():
            lines.append(text(key)+': '+text(json.dumps(value,ensure_ascii=True) if isinstance(value,list) else value)+'\n')
        for key in row['objective_ids']:
            lines+=['Objective '+text(key)+': '+text(report['objective_definitions'][key]['title'])]
    return '\n'.join(lines)+'\n'


def publish(store,run_id,data,*,as_of,max_age_hours,provenance=None,deadline=None):
    require(isinstance(data,bytes) and len(data)<=MAX_BYTES)
    saved=load_run(store,run_id)
    document=validate(decode(data),saved)
    report=review(document,saved,as_of,max_age_hours)
    if provenance is not None:
        from .provenance import validate_provenance
        report['execution_provenance']=validate_provenance(provenance)
        source_tenant=saved['context'].get('execution_provenance',{}).get('tenant_id')
        require(source_tenant is None or source_tenant.lower()==provenance['tenant_id'].lower())
    if deadline:deadline.check()
    evidence_id='o-'+uuid4().hex;prefix='operational/'+evidence_id
    report.update(evidence_id=evidence_id,generated_at=now())
    store.put_new(prefix+'/intent.json',encode({'evidence_id':evidence_id,'source_run_id':run_id}))
    objects={}
    for name,content in [('input.json',data),('review.json',encode(report)),('review.md',markdown(report).encode())]:
        key=prefix+'/'+name;store.put_new(key,content)
        objects[name]={'key':key,'sha256':digest(content),'bytes':len(content)}
    manifest={'schema_version':'1.0','kind':'operational_evidence','state':'complete',
              **{key:report[key] for key in ('evidence_id','source_run_id','source_manifest_sha256','generated_at')},'objects':objects}
    store.put_new(prefix+'/manifest.json',encode(manifest))
    return manifest


def load(store,evidence_id):
    prefix='operational/'+identity(evidence_id,'o')
    data=store.read(prefix+'/manifest.json');manifest=json.loads(data)
    require((manifest.get('schema_version'),manifest.get('kind'),manifest.get('state'),manifest.get('evidence_id'))==('1.0','operational_evidence','complete',evidence_id))
    require(set(manifest['objects'])=={'input.json','review.json','review.md'})
    objects={}
    for name,descriptor in manifest['objects'].items():
        require(descriptor['key']==prefix+'/'+name)
        content=store.read(descriptor['key'])
        require(len(content)==descriptor['bytes'] and digest(content)==descriptor['sha256']);objects[name]=content
    report=json.loads(objects['review.json'])
    require(report['schema_version']=='1.0' and report['kind']=='operational_evidence_review')
    for key in ('evidence_id','source_run_id','source_manifest_sha256','generated_at'):require(report[key]==manifest[key])
    saved=load_run(store,manifest['source_run_id'])
    require(saved['manifest_sha256']==manifest['source_manifest_sha256'])
    # Validate linkage against the stored input; do not recompute historical freshness or current objective mappings.
    original=json.loads(objects['input.json'])
    require(original.get('requirements',[])==report.get('requirements',[]))
    require(original['mode']==report['mode'] and len(original['records'])==len(report['records']))
    for before,after in zip(original['records'],report['records']):require({k:v for k,v in after.items() if k!='freshness'}==before)
    return {'manifest':manifest,'manifest_sha256':digest(data),'report':report,'markdown':objects['review.md'].decode()}


def render_pdf(report):
    from .pdf_report import renderer_dependencies,serialized_render
    renderer_dependencies()
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import reportlab
    from pathlib import Path
    @serialized_render
    def render():
        fonts=Path(reportlab.__file__).with_name('fonts')
        pdfmetrics.registerFont(TTFont('OperationalVera',str(fonts/'Vera.ttf')))
        styles=getSampleStyleSheet()
        for name in ('Normal','Heading1','Heading2'):
            styles[name].fontName='OperationalVera';styles[name].wordWrap='CJK'
        stream=BytesIO();story=[]
        def add(label,value):
            text=json.dumps(value,ensure_ascii=True) if isinstance(value,(list,dict)) else str(value)
            story.extend([Paragraph(escape(label)+': '+escape(text.encode('ascii','backslashreplace').decode()).replace('\n','<br/>'),styles['Normal']),Spacer(1,6)])
        story.append(Paragraph(escape(report.get('title','Operational evidence supplement')),styles['Heading1']))
        for key in ('evidence_id','source_run_id','source_manifest_sha256','source_scope','mode','as_of','max_age_hours'):add(key,report[key])
        if 'execution_provenance' in report:add('Execution provenance',report['execution_provenance'])
        if 'collection_source' in report:add('Collection results',report['collection_source'])
        for limit in report['limitations']:add('Limit',limit)
        if report.get('requirements'):
            story.append(PageBreak());story.append(Paragraph('Required operational evidence',styles['Heading1']))
            for item in report['requirements']:add('Requirement',item)
            for item in report['requirement_results']:add('Outcome',item)
        if 'summary' in report:add('Assessment summary',report['summary'])
        if 'criteria' in report:add('Supplied criteria',report['criteria'])
        if 'freshness' in report:add('Evidence freshness',report['freshness'])
        for row in report['records']:
            story.append(PageBreak());story.append(Paragraph(escape(row['record_id']),styles['Heading2']))
            for key,value in row.items():add(key,value)
            for objective in row['objective_ids']:add(objective,report['objective_definitions'][objective])
        SimpleDocTemplate(stream,title=report.get('title','Operational evidence supplement'),author='Cloud governance',leftMargin=42,rightMargin=42).build(story)
        return stream.getvalue()
    return render()


def publish_pdf(store,evidence_id,*,deadline=None):
    saved=load(store,evidence_id);data=render_pdf(saved['report'])
    if deadline:deadline.check()
    report_id='p-'+uuid4().hex;prefix='operational-reports/'+report_id
    store.put_new(prefix+'/intent.json',encode({'report_id':report_id,'evidence_id':evidence_id}))
    store.put_new(prefix+'/report.pdf',data)
    manifest={'schema_version':'1.0','kind':'operational_evidence_pdf','state':'complete','report_id':report_id,
              'evidence_id':evidence_id,'evidence_manifest_sha256':saved['manifest_sha256'],'generated_at':now(),
              'pdf':{'key':prefix+'/report.pdf','sha256':digest(data),'bytes':len(data)}}
    store.put_new(prefix+'/manifest.json',encode(manifest));return manifest
