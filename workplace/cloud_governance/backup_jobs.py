"""Read-only backup/restore job evidence and explicit recency criteria."""
from datetime import datetime
import re
from .safety import resource_id

STATUSES={'Started','InProgress','Completed','Failed','Cancelled','Canceled','CompletedWithWarnings','Cancelling','Paused'}
OPERATIONS={'Backup','Restore','Tiering','Management','ConfigureBackup','DeleteBackupData','DisableBackup',
            'EnableBackup','Undelete','Validate','Export','ConfigureProtection','UnConfigureProtection'}


def timestamp(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})',value):raise ValueError()
    result=datetime.fromisoformat(value)
    if result.tzinfo is None:raise ValueError()
    return result


def valid_jobs(value):
    if not isinstance(value,list) or len(value)>10000:return False
    seen=set()
    try:
        for row in value:
            if not isinstance(row,dict) or set(row)!={'job_id','source_id','operation','status','start_time','end_time'}:return False
            rid=row['job_id'];source=row['source_id']
            if not isinstance(rid,str) or rid!=rid.lower() or not resource_id(rid) or not re.fullmatch(r'.*/providers/microsoft\.(?:dataprotection/backupvaults|recoveryservices/vaults)/[^/]+/backupjobs/[^/]+',rid) or rid in seen:return False
            seen.add(rid)
            if source is not None and (not isinstance(source,str) or source!=source.lower() or not resource_id(source)):return False
            if row['operation'] not in OPERATIONS or row['status'] not in STATUSES:return False
            start=timestamp(row['start_time']);end=timestamp(row['end_time']) if row['end_time'] is not None else None
            if end is not None and end<start:return False
            if row['status'] in ('Completed','CompletedWithWarnings') and end is None:return False
        return value==sorted(value,key=lambda r:r['job_id'])
    except (ValueError,TypeError):return False


def collect(transport,rid,check,max_pages):
    from .collector import Collector,endpoint
    reader=Collector(transport,max_pages)
    rows,listing=reader.paged(endpoint(rid+check.suffix,check.api),rid,'backup_jobs')
    values=[];seen=set();malformed=False
    for raw in rows:
        try:
            p=raw['properties'];dp=check.resource_type=='microsoft.dataprotection/backupvaults'
            row={'job_id':raw['id'].lower(),'source_id':p['dataSourceId'].lower() if dp else None,
                 'operation':p['operationCategory'] if dp else p['operation'],'status':p['status'],
                 'start_time':p['startTime'],'end_time':p.get('endTime')}
            if not valid_jobs([row]) or row['job_id'].rsplit('/',2)[0]!=rid.lower() or row['job_id'] in seen:raise ValueError()
            seen.add(row['job_id']);values.append(row)
        except (ValueError,KeyError,TypeError,AttributeError):malformed=True
    values.sort(key=lambda r:r['job_id'])
    return {'state':'observed' if listing['complete'] and not malformed else 'partial','value':values,
            'collection':{**listing,'malformed':malformed,'errors':[{k:e[k] for k in ('code','http_status')} for e in reader.errors]}}


def valid_criterion(check,value):
    if not isinstance(value,dict) or set(value)!={'scope','source_ids','operation','max_age_seconds'}:return False
    if value['scope'] not in ('vault','sources') or value['operation'] not in ('Backup','Restore','BackupAndRestore'):return False
    if type(value['max_age_seconds']) is not int or not 1<=value['max_age_seconds']<=31536000:return False
    sources=value['source_ids']
    if not isinstance(sources,list) or len(sources)>10000 or not all(isinstance(s,str) and s==s.lower() and resource_id(s) for s in sources):return False
    if sources!=sorted(set(sources)) or bool(sources)!=(value['scope']=='sources'):return False
    return value['scope']=='vault' or check.resource_type=='microsoft.dataprotection/backupvaults'


def assess(jobs,criterion,as_of):
    reference=timestamp(as_of);outcomes=[]
    sources=criterion['source_ids'] if criterion['scope']=='sources' else [None]
    operations=('Backup','Restore') if criterion['operation']=='BackupAndRestore' else (criterion['operation'],)
    for source,operation in ((source,operation) for source in sources for operation in operations):
        matches=[j for j in jobs if j['operation']==operation and (source is None or j['source_id']==source)]
        latest=[]
        if not matches:state='missing'
        elif any(timestamp(j['start_time'])>reference or j['end_time'] is not None and timestamp(j['end_time'])>reference for j in matches):state='future'
        else:
            latest_time=max(timestamp(j['start_time']) for j in matches)
            latest=[j for j in matches if timestamp(j['start_time'])==latest_time]
            if any(j['status'] in ('Failed','Cancelled','Canceled','CompletedWithWarnings') for j in latest):state='unsuccessful'
            elif any(j['status']!='Completed' for j in latest):state='unfinished'
            else:state='current' if all((reference-timestamp(j['end_time'])).total_seconds()<=criterion['max_age_seconds'] for j in latest) else 'stale'
        outcomes.append({'source_id':source,'operation':operation,'state':state,'job_ids':sorted(j['job_id'] for j in (latest or matches))})
    states={row['state'] for row in outcomes}
    if states & {'missing','unsuccessful','stale'}:
        result,reason='FAIL','Required latest job evidence is missing, unsuccessful, or older than the supplied window.'
    elif states-{'current'}:result,reason='UNKNOWN','Latest job evidence is unfinished or future-dated.'
    else:result,reason='PASS','Latest jobs completed within the supplied window for the selected scope; recoverability and restore quality are not established.'
    return result,reason,{'as_of':as_of,'outcomes':outcomes,'coverage_incomplete':bool(states & {'future','unfinished','missing'})}
