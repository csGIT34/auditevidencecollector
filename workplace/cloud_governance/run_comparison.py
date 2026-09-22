"""Compare exact saved observations. No collection, reassessment or deletion inference."""
from collections import Counter
import json
from uuid import uuid4

from . import report_model
from . import __version__
from .archive import digest, encode, identity, load_run
from .safety import now


def _scope(saved):
    snapshot = saved['snapshot']
    graph = snapshot.get('identity_evidence')
    provenance = saved['context'].get('execution_provenance', {})
    return {'mode': snapshot['mode'],
            'subscriptions': sorted((s['id'].lower(), (s.get('resource_group') or '').lower())
                                    for s in snapshot['inventory']['subscriptions']),
            'tenant': provenance.get('tenant_id'),
            'graph_tenant': graph.get('tenant_id') if graph else None,
            'graph_enabled': graph is not None}


def _rows(saved):
    rows = {}
    resources = {r['id']: r for r in saved['snapshot']['resources']}
    for row in report_model.resource_results(saved['assessment']):
        rows[(row['id'].lower(), 'encryption')] = {
            'observation': {'evidence': row['evidence'], 'collection_status': row['collection_status'],
                            'errors': row['errors'], 'gaps': row['gaps'],
                            'children': resources[row['id']]['children']},
            'result': row['result'], 'observed_at': row['collected_at'],
            'criterion': {'rule_id': row['rule_id'], 'rule_version': row['rule_version'],
                          'criteria': saved['context']['criteria_by_mode'].get(
                              (saved['context']['rule_catalog'].get(row['type'].lower()) or {}).get('mode')),
                          'catalog': saved['context']['rule_catalog'].get(row['type'].lower())}}
    assessment = report_model.configuration(saved['assessment']) or {}
    for row in assessment.get('results', []):
        rows[(row['resource_id'].lower(), row['check_id'])] = {
            'observation': row['observation'], 'result': row['result'], 'observed_at': row['observed_at'],
            'criterion': {'criterion': row['criterion'], 'rule_version': assessment['rule_version'],
                          'rule': saved['context'].get('configuration_rules', {}).get(row['check_id']),
                          'policy_status': (assessment.get('policy') or {}).get('status'),
                          'max_observation_age_seconds': (assessment.get('policy') or {}).get('max_observation_age_seconds')}}
    return rows


def compare(before, after):
    old, new = _rows(before), _rows(after)
    same_scope = _scope(before) == _scope(after)
    rows = []
    for key in sorted(set(old) | set(new)):
        left, right = old.get(key), new.get(key)
        if left is None:
            changes = ['NEW_OBSERVATION']
        elif right is None:
            changes = ['MISSING_OBSERVATION']
        else:
            changes = []
            if left['observation'] != right['observation']:
                changes.append('OBSERVATION_CHANGED')
            if left['criterion'] != right['criterion']:
                changes.append('CRITERIA_OR_RULE_CHANGED')
            if left['result'] != right['result']:
                changes.append('RESULT_CHANGED')
            if left['result'] in ('PASS', 'FAIL') and right['result'] in ('UNKNOWN', 'ERROR', 'UNSUPPORTED'):
                changes.append('EVIDENCE_LOST')
            if not changes:
                changes.append('UNCHANGED')
        rows.append({'resource_id': key[0], 'check_id': key[1], 'changes': changes,
                     'before': left, 'after': right})
    counts = Counter(change for row in rows for change in row['changes'])
    resources_before = {key[0] for key in old}
    resources_after = {key[0] for key in new}
    return {'schema_version': '1.0', 'kind': 'saved_run_comparison', 'generator_version': __version__,
            'before_run_id': before['manifest']['run_id'], 'after_run_id': after['manifest']['run_id'],
            'before_manifest_sha256': before['manifest_sha256'], 'after_manifest_sha256': after['manifest_sha256'],
            'same_declared_scope': same_scope, 'before_scope': _scope(before), 'after_scope': _scope(after),
            'before_inventory_complete': before['snapshot']['inventory']['complete'],
            'after_inventory_complete': after['snapshot']['inventory']['complete'],
            'newly_observed_resources': sorted(resources_after - resources_before),
            'no_longer_observed_resources': sorted(resources_before - resources_after),
            'counts': dict(sorted(counts.items())), 'checks': rows,
            'limitations': ['A missing observation does not establish resource deletion or remediation.',
                           'Scope, permissions, pagination, collectors and timing can change observed populations.',
                           'Changed results with changed criteria or rules do not establish resource drift.',
                           'Neither run is reassessed; timestamps alone do not count as configuration changes.',
                           'Configuration metadata is not proof of period-wide control effectiveness.']}


def markdown(report):
    def cell(value):
        return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '\\|').replace('\n', ' ')
    lines = ['# Saved run comparison', '', f"Before: {report['before_run_id']}",
             f"After: {report['after_run_id']}", f"Same declared scope: {report['same_declared_scope']}", '',
             '## Limitations', ''] + ['- ' + line for line in report['limitations']]
    lines += ['', '## Changed observations', '', '| Resource | Check | Changes | Before | After |',
              '| --- | --- | --- | --- | --- |']
    for row in report['checks']:
        if row['changes'] == ['UNCHANGED']:
            continue
        values = [row['resource_id'], row['check_id'], ', '.join(row['changes']),
                  (row['before'] or {}).get('result', 'No observation'),
                  (row['after'] or {}).get('result', 'No observation')]
        lines.append('| ' + ' | '.join(cell(value) for value in values) + ' |')
    lines += ['', 'Full saved values, criteria and timestamps are retained in comparison.json.', '',
              'Before manifest SHA-256: ' + report['before_manifest_sha256'],
              'After manifest SHA-256: ' + report['after_manifest_sha256']]
    return '\n'.join(lines) + '\n'


def publish(store, before_run_id, after_run_id):
    report = compare(load_run(store, before_run_id), load_run(store, after_run_id))
    comparison_id = 'd-' + uuid4().hex
    prefix = 'run-comparisons/' + comparison_id
    report.update(comparison_id=comparison_id, generated_at=now())
    store.put_new(prefix + '/intent.json', encode({'comparison_id': comparison_id, 'generated_at': report['generated_at']}))
    objects = {}
    for name, data in [('comparison.json', encode(report)), ('comparison.md', markdown(report).encode())]:
        key = prefix + '/' + name
        store.put_new(key, data)
        objects[name] = {'key': key, 'sha256': digest(data), 'bytes': len(data)}
    manifest = {'schema_version': '1.0', 'kind': 'saved_run_comparison', 'state': 'complete',
                **{k: report[k] for k in ('comparison_id', 'generated_at', 'before_run_id', 'after_run_id',
                                          'before_manifest_sha256', 'after_manifest_sha256')}, 'objects': objects}
    store.put_new(prefix + '/manifest.json', encode(manifest))
    return manifest


def load(store, comparison_id):
    prefix = 'run-comparisons/' + identity(comparison_id, 'd')
    manifest = json.loads(store.read(prefix + '/manifest.json'))
    if (manifest.get('schema_version'), manifest.get('kind'), manifest.get('state'), manifest.get('comparison_id')) != (
            '1.0', 'saved_run_comparison', 'complete', comparison_id):
        raise ValueError('Invalid saved run comparison')
    if set(manifest['objects']) != {'comparison.json', 'comparison.md'}:
        raise ValueError('Invalid comparison objects')
    objects = {}
    for name, descriptor in manifest['objects'].items():
        if descriptor['key'] != prefix + '/' + name:
            raise ValueError('Invalid comparison path')
        data = store.read(descriptor['key'])
        if len(data) != descriptor['bytes'] or digest(data) != descriptor['sha256']:
            raise ValueError('Comparison integrity mismatch')
        objects[name] = data
    report = json.loads(objects['comparison.json'])
    for field in ('schema_version', 'kind', 'comparison_id', 'generated_at', 'before_run_id', 'after_run_id',
                  'before_manifest_sha256', 'after_manifest_sha256'):
        if report[field] != manifest[field]:
            raise ValueError('Comparison identity mismatch')
    for side in ('before', 'after'):
        saved = load_run(store, report[side + '_run_id'])
        if saved['manifest_sha256'] != report[side + '_manifest_sha256']:
            raise ValueError('Comparison source mismatch')
    return {'manifest': manifest, 'report': report, 'markdown': objects['comparison.md'].decode()}
