"""Runbook and module LIST metadata; content, links, parameters and jobs excluded."""
import re
from .safety import resource_id,now
from .wiz import require,timestamp

RUNBOOK_TYPES=('Script','Graph','PowerShellWorkflow','PowerShell','GraphPowerShellWorkflow','GraphPowerShell','Python2','Python3','Python','PowerShell72')
MODULE_STATES=('Created','Creating','StartingImportModuleRunbook','RunningImportModuleRunbook','ContentRetrieved','ContentDownloaded','ContentValidated','ConnectionTypeImported','ContentStored','ModuleDataStored','ActivitiesStored','ModuleImportRunbookComplete','Succeeded','Failed','Canceled','Updating')


def project(raw,kind):
    require(isinstance(raw,dict));rid=raw['id'].lower();p=raw['properties']
    require(resource_id(rid) and re.fullmatch(r'.*/providers/microsoft.automation/automationaccounts/[^/]+/'+kind+r'/[^/]+',rid) and isinstance(p,dict))
    modified=p.get('lastModifiedTime');require(modified is not None);timestamp(modified)
    if kind=='runbooks':
        row={'asset_id':rid,'runbook_type':p.get('runbookType'),'state':p.get('state'),'runtime_environment':p.get('runtimeEnvironment'),
             'log_progress':p.get('logProgress'),'log_verbose':p.get('logVerbose'),'last_modified':modified}
        require(row['runbook_type'] in RUNBOOK_TYPES and row['state'] in ('New','Edit','Published'))
        require(row['runtime_environment'] is None or isinstance(row['runtime_environment'],str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',row['runtime_environment']))
        require(type(row['log_progress']) is bool and type(row['log_verbose']) is bool)
    else:
        row={'asset_id':rid,'version':p.get('version'),'provisioning_state':p.get('provisioningState'),'last_modified':modified}
        require(row['version'] is None or isinstance(row['version'],str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.+-]{0,127}',row['version']))
        require(row['provisioning_state'] in MODULE_STATES)
    return row


def valid_assets(value,kind):
    if not isinstance(value,list) or len(value)>10000:return False
    seen=set()
    try:
        for row in value:
            required={'asset_id','last_modified'}|({'runbook_type','state','runtime_environment','log_progress','log_verbose'} if kind=='runbooks' else {'version','provisioning_state'})
            require(isinstance(row,dict) and set(row)==required and isinstance(row['asset_id'],str) and row['asset_id']==row['asset_id'].lower() and row['asset_id'] not in seen)
            seen.add(row['asset_id'])
            mapping={'runbook_type':'runbookType','state':'state','runtime_environment':'runtimeEnvironment','log_progress':'logProgress','log_verbose':'logVerbose','last_modified':'lastModifiedTime','version':'version','provisioning_state':'provisioningState'}
            require(project({'id':row['asset_id'],'properties':{v:row[k] for k,v in mapping.items() if k in row}},kind)==row)
        return value==sorted(value,key=lambda r:r['asset_id'])
    except (KeyError,ValueError,TypeError,AttributeError):return False


def baseline(value):return [{k:v for k,v in row.items() if k!='last_modified'} for row in value]


def valid_criterion(value,kind):
    if not isinstance(value,list):return False
    try:
        if any('last_modified' in row for row in value):return False
        return valid_assets([{**row,'last_modified':'2000-01-01T00:00:00Z'} for row in value],kind) and (kind!='modules' or all(row['version'] is not None for row in value))
    except (TypeError,KeyError):return False


def collect(transport,rid,check,max_pages):
    from .collector import Collector,endpoint
    kind=check.path;reader=Collector(transport,max_pages)
    rows,listing=reader.paged(endpoint(rid+check.suffix,check.api),rid,'automation_'+kind)
    values=[];seen=set();malformed=False
    if len(rows)>10000:return {'state':'invalid'}
    for raw in rows:
        try:
            row=project(raw,kind)
            if row['asset_id'].rsplit('/',2)[0]!=rid.lower() or row['asset_id'] in seen:raise ValueError()
            seen.add(row['asset_id']);values.append(row)
            if kind=='modules' and row['version'] is None:malformed=True
            if timestamp(row['last_modified'])>timestamp(now()):malformed=True
        except (KeyError,ValueError,TypeError,AttributeError):malformed=True
    return {'state':'observed' if listing['complete'] and not malformed else 'partial','value':sorted(values,key=lambda r:r['asset_id']),
            'collection':{**listing,'malformed':malformed,'errors':[{k:e[k] for k in ('code','http_status')} for e in reader.errors]}}


def version_token(value):return isinstance(value,str) and bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.+-]{0,127}',value))


def valid_runtimes(value):
    if not isinstance(value,list) or len(value)>100:return False
    try:
        seen=set();total=0
        for row in value:
            require(isinstance(row,dict) and set(row)=={'environment_id','language','version','default_packages','packages'})
            rid=row['environment_id'];require(isinstance(rid,str) and rid==rid.lower() and resource_id(rid) and re.fullmatch(r'.*/providers/microsoft.automation/automationaccounts/[^/]+/runtimeenvironments/[^/]+',rid) and rid not in seen);seen.add(rid)
            for key in ('language','version'):require(row[key] is None or version_token(row[key]))
            defaults=row['default_packages'];require(defaults is None or isinstance(defaults,list) and len(defaults)<=1000)
            if defaults is not None:
                require(all(isinstance(p,dict) and set(p)=={'name','version'} and version_token(p['name']) and version_token(p['version']) for p in defaults))
                require([p['name'] for p in defaults]==sorted({p['name'] for p in defaults}))
            packages=row['packages'];require(isinstance(packages,list) and len(packages)<=1000);total+=len(packages);require(total<=10000)
            ids=[]
            for package in packages:
                require(isinstance(package,dict) and set(package)=={'package_id','version','provisioning_state'})
                pid=package['package_id'];require(isinstance(pid,str) and pid==pid.lower() and resource_id(pid) and pid.rsplit('/',2)[0]==rid and '/packages/' in pid);ids.append(pid)
                require(package['version'] is None or version_token(package['version']));require(package['provisioning_state'] in MODULE_STATES)
            require(ids==sorted(set(ids)))
        return value==sorted(value,key=lambda r:r['environment_id'])
    except (KeyError,ValueError,TypeError,AttributeError):return False


def collect_runtimes(transport,rid,check,max_pages):
    from .collector import Collector,endpoint
    reader=Collector(transport,max_pages);rows,listing=reader.paged(endpoint(rid+check.suffix,check.api),rid,'automation_runtimes')
    if len(rows)>100:return {'state':'invalid'}
    values=[];seen=set();malformed=False;complete=listing['complete'];pages=listing['pages'];received=listing['items_received'];total=0
    for raw in rows:
        try:
            eid=raw['id'].lower();p=raw['properties'];runtime=p.get('runtime',{})
            if not resource_id(eid) or eid.rsplit('/',2)[0]!=rid.lower() or eid in seen:raise ValueError()
            seen.add(eid)
            defaults=p.get('defaultPackages');require(defaults is None or isinstance(defaults,dict))
            row={'environment_id':eid,'language':runtime.get('language'),'version':runtime.get('version'),
                 'default_packages':None if defaults is None else [{'name':k,'version':v} for k,v in sorted(defaults.items())],'packages':[]}
            require(valid_runtimes([row]))
            packages,state=reader.paged(endpoint(eid+'/packages',check.api),eid,'automation_packages')
            pages+=state['pages'];received+=state['items_received'];complete=complete and state['complete']
            total+=len(packages)
            if len(packages)>1000 or total>10000:return {'state':'invalid'}
            for package in packages:
                props=package['properties'];row['packages'].append({'package_id':package['id'].lower(),'version':props.get('version'),'provisioning_state':props.get('provisioningState')})
            row['packages'].sort(key=lambda x:x['package_id']);require(valid_runtimes([row]))
            if row['language'] is None or row['version'] is None or defaults is None or any(p['version'] is None for p in row['packages']):malformed=True
            values.append(row)
        except (KeyError,ValueError,TypeError,AttributeError):malformed=True
    return {'state':'observed' if complete and not malformed else 'partial','value':sorted(values,key=lambda r:r['environment_id']),
            'collection':{'complete':complete,'pages':pages,'items_received':received,'malformed':malformed,'errors':[{k:e[k] for k in ('code','http_status')} for e in reader.errors]}}
