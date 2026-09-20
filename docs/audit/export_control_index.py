"""Package control labels, titles and families for the control-indexed evidence register."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def payload():
    # The full standard, verified against the pinned digest by export_nist_catalog.py.
    raw = (ROOT / 'docs/audit/nist-control-catalog.json').read_bytes()
    index = json.loads(raw)
    scope = json.loads((ROOT / 'cloud_governance/program_scope.json').read_text())
    catalog = json.loads((ROOT / 'docs/audit/catalog.json').read_text())
    family = {control: entry['id'] for entry in scope['families'] for control in entry['candidate_controls']}
    candidates = set(family)
    # Controls implicated by the deployed Azure resource types, separate from organization-wide candidates.
    service = {reference['label'] for check in catalog['checks'] if check['service_id'] != 'shared'
               for reference in check['nist']}
    return {'schema_version': '1.0', 'source': index['source'], 'index_sha256': hashlib.sha256(raw).hexdigest(),
            'control_count': len(index['controls']),
            'families': {entry['id']: {'title': entry['title'], 'responsibility': entry['responsibility']}
                         for entry in scope['families']},
            'references': [{'id': 'sp800-53r5', 'label': 'NIST SP 800-53 Rev. 5',
                            'role': 'Control catalog and assessment procedures for every control status in this register.',
                            'url': 'https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final'},
                           {'id': 'sp800-144', 'label': 'NIST SP 800-144',
                            'title': 'Guidelines on Security and Privacy in Public Cloud Computing',
                            'published': '2011-12', 'reviewed_on': '2026-09-20',
                            'role': 'Public-cloud outsourcing guidance. It publishes recommendations, not assessable control identifiers, so it produces no status here; its nine key issue areas index the same evidence.',
                            'areas': {'4.1': 'Governance', '4.2': 'Compliance', '4.3': 'Trust', '4.4': 'Architecture',
                                      '4.5': 'Identity and Access Management', '4.6': 'Software Isolation',
                                      '4.7': 'Data Protection', '4.8': 'Availability', '4.9': 'Incident Response'},
                            'url': 'https://csrc.nist.gov/pubs/sp/800/144/final'}],
            'controls': {label: {'oscal_id': control['oscal_id'], 'title': control['title'],
                                 'family': control['family'], 'withdrawn': control['withdrawn'],
                                 'candidate': control['oscal_id'] in candidates,
                                 'service_applicable': label in service}
                         for label, control in sorted(index['controls'].items())}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    target = ROOT / 'cloud_governance/control_index.json'
    data = json.dumps(payload(), sort_keys=True, indent=2) + '\n'
    if args.check:
        if not target.exists() or target.read_text() != data:
            raise SystemExit('Packaged control index differs from the reviewed NIST index')
        print('Packaged control index matches the reviewed NIST catalog.')
    else:
        target.write_text(data)
        print('Updated packaged control index; existing archived run contexts are unchanged.')
