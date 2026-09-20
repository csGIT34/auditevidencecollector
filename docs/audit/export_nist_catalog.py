"""Package the complete NIST SP 800-53 control list from the pinned OSCAL catalog.

The research index only ever held the controls the catalog referenced. Azure Policy maps
to many more, including enhancements, so evidence for them had nowhere to land. This
exporter reads the full OSCAL source, verifies it against the SHA-256 already pinned in
the program scope, and writes a slim label/title/family list.

The OSCAL catalog itself is ~10 MB and is not committed; it is fetched on demand and
checked against the pinned digest, so regenerating cannot silently adopt a different
revision of the standard.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
SOURCE_URL = ('https://raw.githubusercontent.com/usnistgov/oscal-content/{commit}'
              '/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json')


def pinned_source():
    return json.loads((ROOT / 'cloud_governance/program_scope.json').read_text())['nist_source']


def load_catalog(path=None):
    """Read the OSCAL catalog and refuse anything that is not the pinned revision."""
    source = pinned_source()
    raw = Path(path).read_bytes() if path else urlopen(
        SOURCE_URL.format(commit=source['git_commit']), timeout=180).read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != source['sha256']:
        raise SystemExit('OSCAL catalog digest ' + digest + ' does not match the pinned '
                         + source['sha256'] + '; refusing to package an unverified standard')
    return json.loads(raw), source


def label_of(control):
    """The unclassed label is the citable form: AC-1, AC-2(1)."""
    for prop in control.get('props', ()):
        if prop.get('name') == 'label' and 'class' not in prop:
            return prop['value']
    return None


def withdrawn(control):
    return any(prop.get('name') == 'status' and prop.get('value') == 'withdrawn'
               for prop in control.get('props', ()))


def walk(group, controls, family):
    for control in controls:
        label = label_of(control)
        if label:
            yield label, {'oscal_id': control['id'], 'title': control.get('title', ''),
                          'family': family, 'withdrawn': withdrawn(control)}
        yield from walk(group, control.get('controls', ()), family)


def payload(path=None):
    catalog, source = load_catalog(path)
    controls = {}
    families = {}
    for group in catalog['catalog']['groups']:
        families[group['id']] = group.get('title', '')
        for label, entry in walk(group, group.get('controls', ()), group['id']):
            controls[label] = entry
    return {'schema_version': '1.0', 'source': source, 'families': families,
            'control_count': len(controls), 'controls': dict(sorted(controls.items()))}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--source', help='Local copy of the pinned OSCAL catalog; downloaded when omitted.')
    args = parser.parse_args()
    target = ROOT / 'docs/audit/nist-control-catalog.json'
    if args.check:
        if not target.exists():
            raise SystemExit('Packaged NIST control catalog is missing')
        saved = json.loads(target.read_text())
        if saved.get('source') != pinned_source():
            raise SystemExit('Packaged NIST control catalog does not match the pinned source')
        print('Packaged NIST control catalog matches the pinned source: '
              + str(saved['control_count']) + ' controls.')
    else:
        data = json.dumps(payload(args.source), indent=2, sort_keys=True) + '\n'
        target.write_text(data)
        print('Wrote ' + str(json.loads(data)['control_count']) + ' controls from the verified OSCAL catalog.')
