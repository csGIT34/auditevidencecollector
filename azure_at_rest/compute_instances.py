"""Read-only Uniform model and Uniform/Flexible membership evidence; no guest secrets."""
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


def valid_members(value):
    if not isinstance(value,dict) or set(value)!={'orchestration','scope','members'}:return False
    mode=value['orchestration'];scope=value['scope'];members=value['members']
    if mode not in ('Uniform','Flexible') or scope not in ('scale_set','subscription','resource_group'):return False
    if (mode=='Uniform')!=(scope=='scale_set'):return False
    if not isinstance(members,list) or len(members)>10000 or not all(isinstance(v,str) and v==v.lower() and resource_id(v) for v in members):return False
    pattern=r'.*/providers/microsoft.compute/virtualmachinescalesets/[^/]+/virtualmachines/[0-9]+' if mode=='Uniform' else r'.*/providers/microsoft.compute/virtualmachines/[^/]+'
    return members==sorted(set(members)) and all(re.fullmatch(pattern,v) for v in members)


def collect_members(transport,rid,check,max_pages,parent,models,resource_group=None):
    """Uniform IDs reuse the actual-instance read; Flexible VMs use their declared parent."""
    from .collector import Collector,endpoint
    mode=parent.get('properties',{}).get('orchestrationMode') if isinstance(parent,dict) else None
    if mode=='Uniform':
        if models.get('state') not in ('observed','partial'):return {'state':'missing'},[]
        return {**models,'value':{'orchestration':mode,'scope':'scale_set','members':[v['instance_id'] for v in models['value']]}},[]
    if mode!='Flexible':return {'state':'missing'},[]
    sid=rid.split('/')[2].lower();scope='/subscriptions/'+sid
    if resource_group:scope+='/resourceGroups/'+resource_group
    scope+='/providers/Microsoft.Compute/virtualMachines'
    reader=Collector(transport,max_pages);rows,listing=reader.paged(endpoint(scope,check.api),rid,'flexible_members')
    members=[];seen=set();malformed=False;matched=[]
    for raw in rows:
        try:
            vm=raw['id'].lower();properties=raw['properties']
            if not isinstance(properties,dict) or not resource_id(vm) or not re.fullmatch(r'/subscriptions/'+re.escape(sid)+r'/resourcegroups/[^/]+/providers/microsoft.compute/virtualmachines/[^/]+',vm):raise ValueError()
            if resource_group and vm.split('/')[4]!=resource_group.lower():raise ValueError()
            if vm in seen:raise ValueError()
            seen.add(vm)
            association=properties.get('virtualMachineScaleSet')
            if association is None:continue
            if not isinstance(association,dict) or not isinstance(association.get('id'),str):raise ValueError()
            parent_id=association['id'].lower()
            if not resource_id(parent_id) or not re.fullmatch(r'.*/providers/microsoft.compute/virtualmachinescalesets/[^/]+',parent_id):raise ValueError()
            if parent_id==rid.lower():members.append(vm);matched.append(raw)
        except (KeyError,TypeError,AttributeError,ValueError):malformed=True
    value={'orchestration':mode,'scope':'resource_group' if resource_group else 'subscription','members':sorted(members)}
    if not valid_members(value):return {'state':'invalid'},[]
    return {'state':'observed' if listing['complete'] and not malformed else 'partial','value':value,
            'collection':{**listing,'malformed':malformed,'errors':[{k:e[k] for k in ('code','http_status')} for e in reader.errors]}},matched
