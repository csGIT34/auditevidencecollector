"""Trace all research objectives to executable support without declaring objectives complete."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from azure_at_rest.controls import CHECKS
from azure_at_rest.catalog import RULES

def register():
    research=json.loads((ROOT/'docs/audit/catalog.json').read_text())
    rows=[]
    for proposed in research['checks']:
        from azure_at_rest.kubernetes_evidence import CHECKS as KUBE_CHECKS
        workload_predicates=sorted(key for key,objective in KUBE_CHECKS.items() if objective==proposed['id'])
        predicates=sorted(c.id for c in CHECKS.values() if c.catalog_ref==proposed['id'])
        service_types={c.resource_type for c in CHECKS.values() if c.catalog_ref.split('-')[0]==proposed['service_id']}
        encryption=sorted({RULES[t].key for t in service_types if t in RULES and RULES[t].mode!='na'}) if proposed['domain']=='R' else []
        rows.append({'id':proposed['id'],'service_id':proposed['service_id'],'domain':proposed['domain'],'title':proposed['title'],
                     'state':'PARTIAL_EXECUTABLE_SUPPORT' if predicates or encryption else 'NOT_IMPLEMENTED',
                     'configuration_predicates':predicates,'workload_import_predicates':workload_predicates,'existing_encryption_rules':encryption,
                     'whole_objective_complete':False,'new_configuration_live_validation':'NOT_VERIFIED',
                     'remaining_acceptance_boundary':proposed['acceptance_candidate']})
    return {'catalog_version':research['catalog_version'],'objective_count':len(rows),'configuration_predicate_count':len(CHECKS),
            'complete_objectives':0,'limits':'Predicate counts are not completed research objectives. Shared/process, workload and native integration gaps remain open.', 'checks':rows}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    path=ROOT/'docs/audit/delivery-register.json';data=json.dumps(register(),indent=2,sort_keys=True)+'\n'
    if args.check:
        if not path.exists() or path.read_text()!=data:raise SystemExit('Delivery register differs from implementation')
        print('Delivery register matches executable support; whole objectives remain open.')
    else:path.write_text(data)
