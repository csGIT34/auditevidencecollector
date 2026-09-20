"""Trace all research objectives to executable support without declaring objectives complete."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from cloud_governance.controls import CHECKS
from cloud_governance.catalog import RULES

# Explicit routing makes new collector operations fail the register gate until documented.
ADAPTERS={
    'get':('collector','test_controls'),
    'log_tables':('log_tables','test_log_tables'),
    'private_endpoint':('controls','test_controls'),
    'diagnostics':('collector','test_controls'),
    'diagnostic_routes':('diagnostic_routes','test_diagnostic_routes'),
    'federation':('collector','test_controls'),
    'authorization':('authorization','test_authorization'),
    'backup_population':('backup_population','test_backup_population'),
    'vmss_instances':('compute_instances','test_compute_instances'),
    'vmss_members':('compute_instances','test_compute_instances'),
    'container_revisions':('container_revisions','test_container_revisions'),
    'backup_jobs':('backup_jobs','test_backup_jobs'),
    'blob_containers':('blob_containers','test_blob_containers'),
    'vault_metadata':('vault_metadata','test_vault_metadata'),
    'automation_assets':('automation_assets','test_automation_assets'),
    'automation_runtimes':('automation_assets','test_automation_assets'),
}


def configuration_capability(check):
    graph=check.resource_type.startswith('graph.')
    module,test=('graph','test_graph') if graph else ADAPTERS[check.operation]
    plane='MICROSOFT_GRAPH' if graph else 'KEY_VAULT_DATA_METADATA' if check.operation=='vault_metadata' else 'ARM'
    return {
        'kind':'configuration_predicate','catalog_objectives':[check.catalog_ref],
        'implementation_state':'IMPLEMENTED_OFFLINE_TESTED','live_validation':'NOT_VERIFIED',
        'collection_plane':plane,'resource_type':check.resource_type,
        'api_version':check.api,'operation':check.operation,'suffix':check.suffix,'property':check.path,
        'implementation_files':sorted({'cloud_governance/'+module+'.py','cloud_governance/controls.py','cloud_governance/collector.py'}),
        'test_files':sorted({'tests/'+test+'.py','tests/test_controls.py','tests/test_archive.py','tests/test_pdf_pipeline.py'}),
        'criteria':{'source':'approved policy overrides[resource_id]['+check.id+'] with fallback to checks['+check.id+']',
                    'missing_or_draft':'UNKNOWN','validation':'cloud_governance/controls.py:validate_policy'},
        'permissions_guide':'docs/CONFIGURATION_ASSESSMENTS.md',
        'permission_boundary':'Existing authorized reads only; confirm endpoint-specific permissions and scope. No grants are created.',
        'reporting':['saved JSON assessment','Markdown','exact-run PDF','saved-run comparison'],
        'report_files':['cloud_governance/archive.py','cloud_governance/report.py','cloud_governance/pdf_report.py','cloud_governance/run_comparison.py'],
        'source_definition':check.source,
        'remaining_dependencies':['Approved scoped criteria and population','Live API, permission and variant acceptance','Whole-objective acceptance boundary'],
    }


def supplement_capability(name,predicate,objectives):
    module='kubernetes_evidence' if name=='workload' else 'guest_evidence'
    guide='docs/KUBERNETES_EVIDENCE.md' if name=='workload' else 'docs/GUEST_EVIDENCE.md'
    return {
        'kind':name+'_predicate','catalog_objectives':sorted(objectives),
        'implementation_state':'IMPLEMENTED_OFFLINE_TESTED','live_validation':'NOT_VERIFIED',
        'collection_plane':'KUBERNETES_METADATA' if name=='workload' else 'NORMALIZED_GUEST_EXPORT',
        'implementation_files':['cloud_governance/'+module+'.py']+(['cloud_governance/kubernetes_collect.py'] if name=='workload' else []),
        'test_files':['tests/test_'+module+'.py']+(['tests/test_kubernetes_collect.py'] if name=='workload' else []),
        'criteria':{'source':guide,'predicate':predicate,'missing_or_draft':'UNKNOWN'},
        'permissions_guide':guide,'reporting':['separate immutable supplement','Markdown','exact-supplement PDF'],
        'remaining_dependencies':['Approved scope, criteria and freshness','Live source/identity acceptance']+
            (['Guest vendor-native contract and adapter'] if name=='guest' else ['Cluster network, CA and authorized Kubernetes RBAC']),
    }


def register():
    research=json.loads((ROOT/'docs/audit/catalog.json').read_text())
    from cloud_governance.kubernetes_evidence import CHECKS as KUBE_CHECKS
    from cloud_governance.guest_evidence import CHECKS as GUEST_CHECKS
    capabilities={'configuration:'+c.id:configuration_capability(c) for c in CHECKS.values()}
    capabilities.update({'workload:'+key:supplement_capability('workload',key,[objective]) for key,objective in KUBE_CHECKS.items()})
    capabilities.update({'guest:'+key:supplement_capability('guest',key,['VM-'+domain,'VMSS-'+domain]) for key,domain in GUEST_CHECKS.items()})
    rows=[]
    for proposed in research['checks']:
        guest_predicates=sorted(key for key,domain in GUEST_CHECKS.items() if proposed['id'] in ('VM-'+domain,'VMSS-'+domain))
        workload_predicates=sorted(key for key,objective in KUBE_CHECKS.items() if objective==proposed['id'])
        predicates=sorted(c.id for c in CHECKS.values() if c.catalog_ref==proposed['id'])
        service_types={c.resource_type for c in CHECKS.values() if c.catalog_ref.split('-')[0]==proposed['service_id']}
        encryption=sorted({RULES[t].key for t in service_types if t in RULES and RULES[t].mode!='na'}) if proposed['domain']=='R' else []
        rows.append({'id':proposed['id'],'service_id':proposed['service_id'],'domain':proposed['domain'],'title':proposed['title'],
                     'state':'PARTIAL_EXECUTABLE_SUPPORT' if predicates or encryption or workload_predicates or guest_predicates else 'NOT_IMPLEMENTED',
                     'configuration_predicates':predicates,'guest_import_predicates':guest_predicates,'workload_import_predicates':workload_predicates,'existing_resource_rules':encryption,
                     'implementation_refs':['configuration:'+key for key in predicates]+['workload:'+key for key in workload_predicates]+['guest:'+key for key in guest_predicates],
                     'required_collection_planes':[research['permission_profiles'][key]['plane'] for key in proposed['permission_profiles']],
                     'proposed_permission_profiles':proposed['permission_profiles'],
                     'criteria_requirements':research['organization_parameters'][proposed['organization_parameters']],
                     'required_evidence':proposed['evidence'],'owner_requirement':proposed['owner'],
                     'disposition':{'exclusion':None,'manual_or_inherited_acceptance':'NOT_ASSESSED','live_acceptance':'NOT_VERIFIED'},
                     'encryption_support':{'implementation_files':['cloud_governance/catalog.py','cloud_governance/assessment.py','cloud_governance/collector.py'],
                                           'test_files':['tests/test_rules.py','tests/test_collection.py','tests/test_archive.py','tests/test_pdf_pipeline.py']+(['tests/test_additional_encryption.py'] if set(encryption)&{'grafana-storage','prometheus-storage','automation-secure-assets'} else [])+(['tests/test_managed_redis.py'] if set(encryption)&{'managed-redis','managed-redis-database'} else []),
                                           'reporting':['saved JSON assessment','Markdown','exact-run PDF'],
                                           'criteria':'Pinned scoped encryption rules; no blanket CMK requirement',
                                           'live_validation':'See exact-version records in docs/STATUS.md; no whole-objective live acceptance'} if encryption else None,
                     'operational_evidence_path':{'guide':'docs/OPERATIONAL_EVIDENCE.md','kind':'Attributed records/attestations only; does not implement or satisfy this objective'},
                     'whole_objective_complete':False,'new_configuration_live_validation':'NOT_VERIFIED',
                     'remaining_acceptance_boundary':proposed['acceptance_candidate']})
    return {'register_schema_version':'2.0','capabilities':capabilities,'proposed_permission_profiles':research['permission_profiles'],
            'validation_record':'docs/STATUS.md','catalog_version':research['catalog_version'],'objective_count':len(rows),'configuration_predicate_count':len(CHECKS),
            'complete_objectives':0,'limits':'Predicate counts are not completed research objectives. Shared/process, workload and native integration gaps remain open.', 'checks':rows}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group();group.add_argument('--check',action='store_true');group.add_argument('--objective',help='Print one objective and its linked implementations');args=parser.parse_args()
    path=ROOT/'docs/audit/delivery-register.json';data=json.dumps(register(),indent=2,sort_keys=True)+'\n'
    if args.objective:
        full=register();row=next((r for r in full['checks'] if r['id']==args.objective),None)
        if row is None:raise SystemExit('Unknown objective ID')
        print(json.dumps({'objective':row,'capabilities':{k:full['capabilities'][k] for k in row['implementation_refs']}},indent=2,sort_keys=True))
    elif args.check:
        if not path.exists() or path.read_text()!=data:raise SystemExit('Delivery register differs from implementation')
        print('Delivery register matches executable support; whole objectives remain open.')
    else:path.write_text(data)
