"""Project-defined Wiz v2 observations. No assertion about a native Wiz API schema."""
from copy import deepcopy
import re

from .wiz import fields, require, timestamp, token

# Deliberately explicit: native mappers must project safe values, never raw properties.
OBSERVATIONS = {
    'encryption_at_rest_enabled': (bool,), 'logging_enabled': (bool,),
    'key_source': ('provider_managed', 'customer_managed', 'unknown'),
    'public_network_access': ('enabled', 'disabled', 'restricted', 'unknown'),
    'minimum_tls_version': ('1.0', '1.1', '1.2', '1.3', 'unknown'),
    'identity_type': ('system_assigned', 'user_assigned', 'none', 'unknown'),
    'backup_status': ('protected', 'unprotected', 'unknown'),
    'vulnerability_count': (int,), 'missing_patch_count': (int,),
}
RESULTS = {'PASS', 'FAIL', 'UNKNOWN', 'NOT_APPLICABLE', 'EXEMPT'}


def safe_text(value, limit=1000):
    return isinstance(value, str) and 0 < len(value) <= limit and all(ord(c) >= 32 for c in value)


def observation(value):
    require(isinstance(value, dict) and not set(value) - set(OBSERVATIONS))
    for key, actual in value.items():
        allowed = OBSERVATIONS[key]
        require(type(actual) in allowed if allowed[0] in (bool, int) else actual in allowed)
        if type(actual) is int:
            require(0 <= actual <= 1000000000)


def validate(document):
    from .wiz import validate_export
    fields(document, 'schema_version kind source resources findings observations evaluations scans evaluations_complete')
    require(document['schema_version'] == '2.0')
    require(isinstance(document['source'], dict))
    require(document['source'].get('mapping_version') == '2.0')
    base = deepcopy({k: document[k] for k in ('kind', 'source', 'resources', 'findings')})
    base['schema_version'] = '1.0'
    base['source']['mapping_version'] = '1.0'
    validate_export(base)
    require(type(document['evaluations_complete']) is bool)
    resources = {r['resource_id'].lower() for r in document['resources']}
    exported_at = timestamp(document['source']['exported_at'])
    for key in ('observations', 'evaluations', 'scans'):
        require(isinstance(document[key], list) and len(document[key]) <= 100000)
    seen = set()
    for row in document['observations']:
        fields(row, 'observation_id resource_id observed_at values')
        require(token(row['observation_id']) and row['observation_id'] not in seen)
        seen.add(row['observation_id'])
        require(isinstance(row['resource_id'], str) and row['resource_id'].lower() in resources and timestamp(row['observed_at']) <= exported_at)
        observation(row['values'])
        require(bool(row['values']))
    seen = set()
    for row in document['evaluations']:
        fields(row, 'evaluation_id resource_id rule_id result observed_at observed expected criterion controls')
        require(token(row['evaluation_id']) and row['evaluation_id'] not in seen and token(row['rule_id']))
        seen.add(row['evaluation_id'])
        require(isinstance(row['resource_id'], str) and row['resource_id'].lower() in resources and timestamp(row['observed_at']) <= exported_at)
        require(isinstance(row['result'], str) and row['result'] in RESULTS)
        observation(row['observed'])
        observation(row['expected'])
        require(safe_text(row['criterion']))
        require(isinstance(row['controls'], list) and len(row['controls']) <= 100)
        require(all(isinstance(c, str) and re.fullmatch(r'[A-Z]{2}-\d{1,2}(?:\(\d{1,2}\))?', c) for c in row['controls']))
    seen = set()
    for row in document['scans']:
        fields(row, 'scan_id target_kind target_id status started_at completed_at tool_version policy_id evaluated_rules results_complete result_counts')
        require(token(row['scan_id']) and row['scan_id'] not in seen)
        seen.add(row['scan_id'])
        require(row['target_kind'] in ('arm_resource', 'container_image', 'repository_commit'))
        target = row['target_id']
        require(isinstance(target, str))
        if row['target_kind'] == 'arm_resource':
            require(target.lower() in resources)
        elif row['target_kind'] == 'container_image':
            require(re.fullmatch(r'sha256:[0-9a-f]{64}', target) is not None)
        else:
            require(re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', target) is not None)
        require(row['status'] in ('complete', 'partial', 'failed'))
        require(timestamp(row['started_at']) <= timestamp(row['completed_at']) <= exported_at)
        require(safe_text(row['tool_version'], 128) and token(row['policy_id']))
        require(isinstance(row['evaluated_rules'], list) and len(row['evaluated_rules']) <= 10000)
        require(all(token(r) for r in row['evaluated_rules']) and len(set(row['evaluated_rules'])) == len(row['evaluated_rules']))
        require(type(row['results_complete']) is bool)
        require(isinstance(row['result_counts'], dict) and not set(row['result_counts']) - RESULTS)
        require(all(type(v) is int and 0 <= v <= 100000000 for v in row['result_counts'].values()))
        if row['results_complete']:
            require(row['status'] == 'complete' and bool(row['evaluated_rules']))
    return document


def report_records(document):
    """Project source assertions for display, preserving good, bad and unknown outcomes."""
    result = []
    for row in document.get('observations', []):
        result.append({'kind': 'wiz_observation', 'reference': row['observation_id'],
            'resource_id': row['resource_id'], 'title': 'Wiz observed configuration', 'result': 'OBSERVED',
            'controls': [], 'observed_at': row['observed_at'], 'observations': row['values'],
            'criterion': None, 'explanation': 'Observed facts; no criterion is inferred.',
            'boundaries': 'Selected safe configuration fields', 'gaps': [], 'dependencies': [],
            'provenance': {'source': 'wiz', 'source_export_id': document['source']['export_id']}})
    for row in document.get('evaluations', []):
        result.append({'kind': 'wiz_evaluation', 'reference': row['rule_id'], 'resource_id': row['resource_id'],
            'title': 'Wiz rule ' + row['rule_id'], 'result': row['result'], 'controls': row['controls'],
            'observed_at': row['observed_at'], 'observations': row['observed'],
            'criterion': {'description': row['criterion'], 'expected': row['expected']},
            'explanation': 'Source evaluation retained without reassessment.', 'boundaries': 'Source rule and target',
            'gaps': [] if document['evaluations_complete'] else ['Wiz evaluation export is incomplete.'],
            'dependencies': [], 'provenance': {'source': 'wiz', 'evaluation_id': row['evaluation_id'],
                'mapping_basis': 'operator-declared mapping', 'source_export_id': document['source']['export_id']}})
    for row in document['findings']:
        result.append({'kind': 'wiz_issue', 'reference': row['rule_id'], 'resource_id': row['resource_id'],
            'title': 'Wiz issue ' + row['finding_id'], 'result': 'SOURCE_FINDING', 'controls': [],
            'observed_at': row['observed_at'], 'observations': {k: row[k] for k in ('finding_id', 'status', 'severity')},
            'criterion': None, 'explanation': 'Issue lifecycle is not a configuration pass/fail determination.',
            'boundaries': 'Source finding only', 'gaps': [], 'dependencies': [],
            'provenance': {'source': 'wiz', 'source_export_id': document['source']['export_id']}})
    return result
