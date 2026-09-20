"""Refresh/check the packaged PDF scope outline after deliberate catalog changes."""
from pathlib import Path
import argparse
import hashlib
import json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    source=root/'docs/audit/catalog.json'
    data=json.loads(source.read_text())
    outline={k:data[k] for k in ['catalog_version','reviewed_on','status','domains','organization_parameters','nist_source']}
    outline['catalog_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    outline['services']=[{k:s[k] for k in ['id','name','resource_boundary','current_encryption_maturity','shared_context','domain_coverage']} for s in data['services']]
    outline['families']=[{k:f[k] for k in ['id','title','responsibility','review','candidate_controls']} for f in data['families']]
    outline['proposed_check_count']=len(data['checks'])
    expected=json.dumps(outline,indent=2)+'\n'
    target=root/'cloud_governance/program_scope.json'
    if args.check:
        if target.read_text()!=expected:
            raise SystemExit('Packaged applicability outline is stale; review and regenerate it.')
        print('Packaged applicability outline matches the research catalog.')
    else:
        target.write_text(expected)
        print('Updated packaged outline; existing archived run contexts are unchanged.')


if __name__=='__main__':main()
