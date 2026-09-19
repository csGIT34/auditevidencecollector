"""Complete synthetic Azure/Wiz import, comparison and verified replay; no cloud calls."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New private directory outside the checkout.')
    args = parser.parse_args(argv)
    target = args.output.resolve()
    if target.exists() or target == ROOT or ROOT in target.parents:
        parser.error('Use a new output directory outside the checkout.')
    os.umask(0o077)
    from azure_at_rest.archive import encode, digest, load_run
    from azure_at_rest.catalog import RULES
    from azure_at_rest.collector import FixtureTransport, endpoint, INVENTORY_API
    from azure_at_rest.storage import FileStore
    from azure_at_rest.workflow import collect_run
    from azure_at_rest.wiz import import_export
    from azure_at_rest.reconciliation import publish_comparison, load_comparison
    exported = json.loads((ROOT/'examples/wiz/normalized-export.json').read_text())
    sub = exported['source']['scope']['subscription_ids'][0]
    kind = 'Microsoft.Storage/storageAccounts'
    rows = [{'id':f'/subscriptions/{sub}/resourceGroups/audit-demo/providers/{kind}/{name}',
             'type':kind, 'name':name, 'location':'eastus', 'properties':{}} for name in ('matched','azure-only')]
    responses = {endpoint(f'/subscriptions/{sub}/resources',INVENTORY_API):{'value':rows}}
    responses.update({endpoint(row['id'],RULES[kind.lower()].api):row for row in rows})
    store = FileStore(target/'archive')
    run = collect_run(store, FixtureTransport(responses), [sub], mode='offline_fixture')
    saved = load_run(store, run['run_id'])
    observed = saved['snapshot']['completed_at']
    # Synthetic demo timestamps only. A workplace mapper must retain actual source observations.
    exported['source']['exported_at'] = observed
    for row in exported['resources'] + exported['findings']:
        row['observed_at'] = observed
    imported = import_export(store, encode(exported))
    originals = {k:digest(store.read(k)) for k in store.keys('runs/') + store.keys('external/')}
    comparison = publish_comparison(store, run['run_id'], imported['wiz_import_id'], as_of=observed, max_age_hours=24, max_skew_hours=1)
    replay = load_comparison(store, comparison['comparison_id'])
    assert originals == {k:digest(store.read(k)) for k in originals}
    assert replay['report']['presence_counts'] == {'BOTH':1,'AZURE_ONLY':1,'WIZ_ONLY':1}
    FileStore(target).put_new('comparison.md', replay['markdown'].encode())
    FileStore(target).put_new('comparison.json', encode(replay['report']))
    result = {'synthetic':True,'azure_calls':0,'wiz_calls':0,'run_id':run['run_id'],
              'wiz_import_id':imported['wiz_import_id'],'comparison_id':comparison['comparison_id'],
              'comparison_state':comparison['comparison_state'],'originals_preserved':True,
              'markdown':str(target/'comparison.md')}
    FileStore(target).put_new('result.json', encode(result))
    print(json.dumps(result,indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
