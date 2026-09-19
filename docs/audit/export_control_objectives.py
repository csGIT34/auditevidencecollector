"""Package provisional research objective references for executable predicate reports."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def payload():
    raw=(ROOT/'docs/audit/catalog.json').read_bytes();catalog=json.loads(raw)
    return {'schema_version':'1.0','catalog_version':catalog['catalog_version'],'catalog_sha256':hashlib.sha256(raw).hexdigest(),
            'checks':{c['id']:{'title':c['title'],'domain':c['domain'],'service_id':c['service_id'],
                              'controls':[n['label'] for n in c['nist']],'candidate_criterion':c['acceptance_candidate'],
                              'limits':'Supporting technical evidence only; this predicate does not determine the complete objective or NIST control.'} for c in catalog['checks']}}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    target=ROOT/'azure_at_rest/control_objectives.json'
    data=json.dumps(payload(),sort_keys=True,indent=2)+'\n'
    if args.check:
        if not target.exists() or target.read_text()!=data:raise SystemExit('Control objective package differs from research catalog')
        print('Packaged control objectives match the research catalog.')
    else:target.write_text(data)
