"""Safe Container Apps revision image declarations, including init containers."""
import re
from .safety import resource_id


def valid_revisions(value):
    if not isinstance(value,list) or len(value)>10000:return False
    seen=set()
    for row in value:
        if not isinstance(row,dict) or set(row)!={'revision_id','active','containers'}:return False
        rid=row['revision_id']
        if not isinstance(rid,str) or rid!=rid.lower() or not resource_id(rid) or not re.fullmatch(r'.*/providers/microsoft.app/containerapps/[^/]+/revisions/[^/]+',rid):return False
        if rid in seen or type(row['active']) is not bool:return False
        seen.add(rid);containers=row['containers'];names=set()
        if not isinstance(containers,list) or not containers or len(containers)>1000:return False
        for container in containers:
            if not isinstance(container,dict) or set(container)!={'name','image','kind'}:return False
            name,image,kind=(container[k] for k in ('name','image','kind'))
            if not isinstance(name,str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,62}',name) or kind not in ('app','init'):return False
            if name in names:return False
            names.add(name)
            if not isinstance(image,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,511}(?:@sha256:[a-f0-9]{64})?',image):return False
        if not any(c['kind']=='app' for c in containers) or containers!=sorted(containers,key=lambda c:(c['kind'],c['name'])):return False
    return value==sorted(value,key=lambda r:r['revision_id'])


def collect(transport,rid,check,max_pages):
    from .collector import Collector,endpoint
    reader=Collector(transport,max_pages)
    rows,listing=reader.paged(endpoint(rid+check.suffix,check.api),rid,'container_revisions')
    values=[];seen=set();malformed=False
    for raw in rows:
        try:
            properties=raw['properties'];template=properties['template'];containers=[]
            for key,kind in (('containers','app'),('initContainers','init')):
                source=template[key] if key=='containers' else template.get(key,[])
                if not isinstance(source,list):raise ValueError()
                containers.extend({'name':c['name'],'image':c['image'],'kind':kind} for c in source)
            containers.sort(key=lambda c:(c['kind'],c['name']))
            row={'revision_id':raw['id'].lower(),'active':properties['active'],'containers':containers}
            if not valid_revisions([row]) or row['revision_id'].rsplit('/',2)[0]!=rid.lower() or row['revision_id'] in seen:raise ValueError()
            seen.add(row['revision_id']);values.append(row)
        except (ValueError,TypeError,AttributeError,KeyError):malformed=True
    values.sort(key=lambda r:r['revision_id'])
    return {'state':'observed' if listing['complete'] and not malformed else 'partial','value':values,
            'collection':{**listing,'malformed':malformed,'errors':[{k:e[k] for k in ('code','http_status')} for e in reader.errors]}}
