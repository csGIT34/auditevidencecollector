"""Package control labels, titles and families for the control-indexed evidence register."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def payload():
    raw = (ROOT / 'docs/audit/nist-control-index.json').read_bytes()
    index = json.loads(raw)
    scope = json.loads((ROOT / 'azure_at_rest/program_scope.json').read_text())
    family = {control: entry['id'] for entry in scope['families'] for control in entry['candidate_controls']}
    candidates = set(family)
    return {'schema_version': '1.0', 'source': index['source'], 'index_sha256': hashlib.sha256(raw).hexdigest(),
            'families': {entry['id']: {'title': entry['title'], 'responsibility': entry['responsibility']}
                         for entry in scope['families']},
            'controls': {control['label']: {'oscal_id': key, 'title': control['title'],
                                            'family': family.get(key, key.split('-')[0]),
                                            'candidate': key in candidates}
                         for key, control in sorted(index['controls'].items())}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    target = ROOT / 'azure_at_rest/control_index.json'
    data = json.dumps(payload(), sort_keys=True, indent=2) + '\n'
    if args.check:
        if not target.exists() or target.read_text() != data:
            raise SystemExit('Packaged control index differs from the reviewed NIST index')
        print('Packaged control index matches the reviewed NIST catalog.')
    else:
        target.write_text(data)
        print('Updated packaged control index; existing archived run contexts are unchanged.')
