"""Rehearse all-service collection, Policy/Wiz/operating evidence and selected reports offline."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def demonstrate(target):
    from cloud_governance.archive import digest, encode, load_run
    from cloud_governance.collector import FixtureTransport, endpoint, INVENTORY_API
    from cloud_governance.controls import decode_policy
    from cloud_governance.evidence_report import ENCRYPTION, load, publish
    from cloud_governance.graph import FixtureGraphTransport
    from cloud_governance.operational import publish as import_operational
    from cloud_governance.policy_query import FixturePolicyTransport, assignment_id, assignment_url, set_definition_url
    from cloud_governance.safety import now
    from cloud_governance.storage import FileStore
    from cloud_governance.wiz import import_export
    from cloud_governance.workflow import collect_run

    target = Path(target).resolve()
    if target.exists() or target == ROOT or ROOT in target.parents:
        raise ValueError('Use a new output directory outside the checkout')
    os.umask(0o077)
    store, exports = FileStore(target / 'archive'), FileStore(target)
    suite = ROOT / 'examples/control-suite'
    arm = json.loads((suite / 'arm-fixture.json').read_text())['responses']
    graph = json.loads((suite / 'graph-fixture.json').read_text())['responses']
    criteria = decode_policy((suite / 'criteria.json').read_text())
    wiz = json.loads((ROOT / 'examples/wiz/observations-export.json').read_text())
    subscription = wiz['source']['scope']['subscription_ids'][0]
    resource = next(row['id'] for row in arm[endpoint('/subscriptions/' + subscription + '/resources', INVENTORY_API)]['value']
                    if row['type'].lower() == 'microsoft.storage/storageaccounts')
    for row in wiz['resources'] + wiz['findings'] + wiz['observations'] + wiz['evaluations']:
        row['resource_id'] = resource
    assignment = assignment_id(subscription, 'synthetic-audit')
    initiative = '/providers/Microsoft.Authorization/policySetDefinitions/synthetic-audit'
    observed = now()
    definitions = [('synthetic-encryption', 'SC-28'), ('synthetic-logging', 'AU-2'), ('synthetic-manual', 'PM-1')]
    metadata = {
        assignment_url(subscription, assignment): {'id': assignment, 'properties': {'policyDefinitionId': initiative}},
        set_definition_url(initiative): {'id': initiative, 'properties': {'policyDefinitions': [
            {'policyDefinitionReferenceId': ref, 'groupNames': ['NIST_SP_800-53_R5_' + control]}
            for ref, control in definitions]}}}
    states = [{'policyAssignmentId': assignment, 'policyAssignmentName': 'synthetic-audit',
               'policyDefinitionReferenceId': ref, 'policyDefinitionAction': effect, 'resourceId': resource,
               'complianceState': state, 'timestamp': observed}
              for ref, effect, state in [('synthetic-encryption', 'audit', 'NonCompliant'),
                  ('synthetic-logging', 'audit', 'Compliant'), ('synthetic-manual', 'manual', 'Compliant')]]
    run = collect_run(store, FixtureTransport(arm), [subscription], criteria=criteria,
        graph_transport=FixtureGraphTransport(graph), tenant_id=wiz['source']['tenant_id'],
        policy_transport=FixturePolicyTransport({subscription: states}, metadata), policy_assignment=assignment)
    saved = load_run(store, run['run_id'])
    # These are synthetic timestamps only. A native mapper must never refresh source timestamps.
    wiz['source']['exported_at'] = observed
    for row in wiz['resources'] + wiz['findings'] + wiz['observations'] + wiz['evaluations']:
        row['observed_at'] = observed
    for row in wiz['scans']:
        row.update(started_at=observed, completed_at=observed)
    imported = import_export(store, encode(wiz))
    operating = json.loads((ROOT / 'examples/operational-evidence.json').read_text())
    row = operating['records'][0]
    row.update(record_id='synthetic-encryption-exception', evidence_type='exception', objective_ids=['ST-R'],
               period_start=observed, period_end=observed, observed_at=observed, assertion='NOT_SATISFIED',
               summary='Synthetic exception awaiting remediation. This statement does not suppress the Policy finding.')
    operating['requirements'][0].update(requirement_id='synthetic-encryption-review', evidence_type='exception',
        objective_id='ST-R', period_start=observed, period_end=observed)
    supplement = import_operational(store, run['run_id'], encode(operating), as_of=observed, max_age_hours=24)
    originals = {key: digest(store.read(key)) for prefix in ('runs/', 'external/', 'operational/') for key in store.keys(prefix)}
    topic = {**deepcopy(ENCRYPTION), 'id': 'synthetic-encryption-review', 'version': '1',
        'policy_references': [{'assignment': assignment, 'reference': 'synthetic-encryption'}],
        'wiz_rules': ['synthetic-encryption'], 'objective_ids': ['ST-R']}
    exports.put_new('topic-profile.json', encode(topic))
    attachments = {'wiz_import_id': imported['wiz_import_id'], 'operational_ids': [supplement['evidence_id']]}
    views = {}
    for name, options in [('full', {}), ('encryption', {'topic': topic, 'resource_ids': [resource], 'pdf': True}),
                          ('SC-family', {'families': ['SC']}), ('SC-28-control', {'controls': ['SC-28']})]:
        manifest = publish(store, run['run_id'], **attachments, **options)
        replay = load(store, manifest['report_id'])
        for filename, descriptor in manifest['objects'].items():
            exports.put_new(name + '.' + filename.rsplit('.', 1)[1], store.read(descriptor['key']))
        views[name] = {'report_id': manifest['report_id'], 'summary': replay['report']['summary']}
        if name == 'full':
            assert len({c['control'].split('-')[0] for c in replay['report']['control_coverage']}) == 20
            assert {'PASS', 'FAIL', 'UNKNOWN', 'ATTRIBUTED_NOT_SATISFIED'} <= set(replay['report']['summary']['counts'])
        if name == 'encryption':
            assert any(r['kind'] == 'wiz_evaluation' and r['result'] == 'PASS' for r in replay['report']['records'])
            assert any(r['kind'] == 'policy_compliance' and r['result'] == 'FAIL' for r in replay['report']['records'])
    assert originals == {key: digest(store.read(key)) for key in originals}
    result = {'synthetic': True, 'network_calls': 0, 'run_id': run['run_id'],
        'wiz_import_id': imported['wiz_import_id'], 'operational_id': supplement['evidence_id'],
        'service_entries': len({r['catalog_ref'].split('-')[0] for r in saved['assessment']['evidence']['configuration']['results']}),
        'nist_families_indexed': 20, 'original_objects_preserved': len(originals),
        'views': views, 'pdf': str(target / 'encryption.pdf')}
    exports.put_new('result.json', encode(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New private directory outside the checkout')
    print(json.dumps(demonstrate(parser.parse_args().output), indent=2))
