"""Read-only Uniform VMSS instance model evidence; no guest or secret projection."""
import json
import re
from .safety import resource_id


def valid_instances(value):
    if not isinstance(value,list) or len(value)>10000:return False
    seen=set()
    for row in value:
        if not isinstance(row,dict) or set(row)!={'instance_id','latest_model_applied'}:return False
        rid=row['instance_id']
        if not isinstance(rid,str) or rid!=rid.lower() or not resource_id(rid) or not re.fullmatch(r'.*/providers/microsoft.compute/virtualmachinescalesets/[^/]+/virtualmachines/[0-9]+',rid):return False
        if rid in seen or type(row['latest_model_applied']) is not bool:return False
        seen.add(rid)
    return value==sorted(value,key=lambda r:r['instance_id'])


def collect(transport,rid,check,max_pages,parent):
    from .collector import Collector,endpoint
    # Flexible instances are ordinary VM resources; do not mistake an empty Uniform listing for coverage.
    if not isinstance(parent,dict) or parent.get('properties',{}).get('orchestrationMode')!='Uniform':
        return {'state':'missing'}
    reader=Collector(transport,max_pages)
    rows,listing=reader.paged(endpoint(rid+check.suffix,check.api),rid,'vmss_instances')
    values=[];seen=set();malformed=False
    for raw in rows:
        try:
            row={'instance_id':raw['id'].lower(),'latest_model_applied':raw['properties']['latestModelApplied']}
            if not valid_instances([row]) or row['instance_id'].rsplit('/',2)[0]!=rid.lower() or row['instance_id'] in seen:raise ValueError()
            seen.add(row['instance_id']);values.append(row)
        except (KeyError,TypeError,AttributeError,ValueError):malformed=True
    values.sort(key=lambda r:r['instance_id'])
    return {'state':'observed' if listing['complete'] and not malformed else 'partial','value':values,
            'collection':{**listing,'malformed':malformed,'errors':[{k:e[k] for k in ('code','http_status')} for e in reader.errors]}}
