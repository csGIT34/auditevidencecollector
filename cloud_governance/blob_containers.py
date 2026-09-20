"""Container-level anonymous access declarations; no data-plane or metadata content."""
import re
from .safety import resource_id

LEVELS={'None','Blob','Container'}


def container_id(value):
    if not isinstance(value,str) or value!=value.lower():return False
    match=re.fullmatch(r'(.*/providers/microsoft.storage/storageaccounts/[^/]+)/blobservices/default/containers/(?:\$[a-z0-9-]+|[a-z0-9][a-z0-9-]{1,61}[a-z0-9])',value)
    return bool(match and resource_id(match[1]))


def valid_containers(value):
    if not isinstance(value,list) or len(value)>10000:return False
    seen=set()
    for row in value:
        if not isinstance(row,dict) or set(row)!={'container_id','public_access'} or not container_id(row['container_id']):return False
        if not isinstance(row['public_access'],str) or row['public_access'] not in LEVELS or row['container_id'] in seen:return False
        seen.add(row['container_id'])
    return value==sorted(value,key=lambda r:r['container_id'])


def collect(transport,rid,check,max_pages):
    from .collector import Collector,endpoint
    reader=Collector(transport,max_pages)
    rows,listing=reader.paged(endpoint(rid+check.suffix,check.api),rid,'blob_containers')
    values=[];seen=set();malformed=False
    for raw in rows:
        try:
            row={'container_id':raw['id'].lower(),'public_access':raw['properties']['publicAccess']}
            if not valid_containers([row]) or row['container_id'].rsplit('/blobservices/',1)[0]!=rid.lower() or row['container_id'] in seen:raise ValueError()
            seen.add(row['container_id']);values.append(row)
        except (TypeError,KeyError,ValueError,AttributeError):malformed=True
    values.sort(key=lambda r:r['container_id'])
    if len(values)>10000:values=values[:10000];malformed=True
    return {'state':'observed' if listing['complete'] and not malformed else 'partial','value':values,
            'collection':{**listing,'malformed':malformed,'errors':[{k:e[k] for k in ('code','http_status')} for e in reader.errors]}}
