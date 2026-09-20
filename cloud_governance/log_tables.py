"""Safe Log Analytics table plans/retention, excluding schema and query bodies."""
import re
from .safety import resource_id
from .wiz import require

PLANS=('Analytics','Basic','Auxiliary')
STATES=('Updating','InProgress','Succeeded','Deleting')
FIELDS={'plan':'plan','retention_days':'retentionInDays','total_retention_days':'totalRetentionInDays',
        'archive_retention_days':'archiveRetentionInDays','retention_inherited':'retentionInDaysAsDefault',
        'total_retention_inherited':'totalRetentionInDaysAsDefault','provisioning_state':'provisioningState'}


def table_id(value):
    return isinstance(value,str) and value==value.lower() and resource_id(value) and bool(re.fullmatch(r'/subscriptions/[^/]+/resourcegroups/[^/]+/providers/microsoft.operationalinsights/workspaces/[^/]+/tables/[^/]+',value))


def project(raw):
    require(isinstance(raw,dict) and isinstance(raw.get('id'),str) and isinstance(raw.get('properties'),dict))
    return {'table_id':raw['id'].lower(),**{key:raw['properties'].get(field) for key,field in FIELDS.items()}}


def valid(value):
    if not isinstance(value,list) or len(value)>10000:return False
    try:
        ids=[]
        for row in value:
            require(isinstance(row,dict) and set(row)=={'table_id'}|set(FIELDS))
            require(table_id(row['table_id']));ids.append(row['table_id'])
            require(row['plan'] is None or row['plan'] in PLANS)
            require(row['provisioning_state'] is None or row['provisioning_state'] in STATES)
            for key,maximum in [('retention_days',730),('total_retention_days',4383),('archive_retention_days',4383)]:
                value=row[key];require(value is None or type(value) is int and (value==-1 and key!='archive_retention_days' or (0 if key=='archive_retention_days' else 4)<=value<=maximum))
            for key in ('retention_inherited','total_retention_inherited'):require(row[key] is None or type(row[key]) is bool)
        return ids==sorted(set(ids))
    except (KeyError,ValueError,TypeError):return False


def collect(transport,rid,check,max_pages):
    from .collector import Collector,endpoint
    reader=Collector(transport,max_pages);rows,listing=reader.paged(endpoint(rid+check.suffix,check.api),rid,'log_tables')
    if len(rows)>10000:return {'state':'invalid'}
    values=[];seen=set();malformed=False
    for raw in rows:
        try:
            row=project(raw);require(valid([row]) and row['table_id'].rsplit('/',2)[0]==rid.lower() and row['table_id'] not in seen)
            seen.add(row['table_id']);values.append(row)
            if (any(v is None for v in row.values()) or row['provisioning_state']!='Succeeded'
                    or row['retention_days']<0 or row['total_retention_days']<0
                    or row['total_retention_days']<row['retention_days']
                    or row['total_retention_inherited'] is True and row['total_retention_days']!=row['retention_days']
                    or row['archive_retention_days']!=row['total_retention_days']-row['retention_days']):malformed=True
        except (KeyError,ValueError,TypeError,AttributeError):malformed=True
    return {'state':'observed' if listing['complete'] and not malformed else 'partial','value':sorted(values,key=lambda r:r['table_id']),
            'collection':{**listing,'malformed':malformed,'errors':[{k:e[k] for k in ('code','http_status')} for e in reader.errors]}}


def valid_criterion(value):
    try:
        require(isinstance(value,dict) and set(value)=={'tables','allow_unlisted'} and type(value['allow_unlisted']) is bool)
        require(isinstance(value['tables'],list) and 1<=len(value['tables'])<=10000)
        ids=[]
        for row in value['tables']:
            require(isinstance(row,dict) and set(row)=={'table_id','allowed_plans','minimum_retention_days','minimum_total_days'})
            require(table_id(row['table_id']));ids.append(row['table_id'])
            plans=row['allowed_plans'];require(isinstance(plans,list) and plans and all(p in PLANS for p in plans) and len(set(plans))==len(plans))
            require(type(row['minimum_retention_days']) is int and 0<=row['minimum_retention_days']<=730)
            require(type(row['minimum_total_days']) is int and row['minimum_retention_days']<=row['minimum_total_days']<=4383)
        require(len(set(ids))==len(ids));return True
    except (KeyError,ValueError,TypeError):return False


def meets(value,criterion):
    actual={r['table_id']:r for r in value};expected={r['table_id']:r for r in criterion['tables']}
    return (criterion['allow_unlisted'] or set(actual)==set(expected)) and all(
        tid in actual and actual[tid]['plan'] in row['allowed_plans']
        and actual[tid]['retention_days']>=row['minimum_retention_days']
        and actual[tid]['total_retention_days']>=row['minimum_total_days']
        for tid,row in expected.items())
