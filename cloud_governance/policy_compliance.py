"""Azure Policy compliance as provider-asserted evidence.

Microsoft maintains the policy definitions and their NIST SP 800-53 Rev. 5 control
mapping, so this program reads that work rather than reimplementing it. What arrives here
is Microsoft's assertion about a resource at an evaluation time, not this program's
observation and not an assessor's determination.

Two boundaries are preserved throughout:

* The control mapping is Microsoft's. A definition's association with a control is their
  interpretation, frozen into each record at collection time so a replay cannot silently
  acquire a different mapping later.
* A resource type with no applicable definition produces no record. Absent evaluation is
  recorded as absent and never reads as compliant.
"""
import re

from .safety import MISSING, get, now, resource_id

# Microsoft names each control group in the initiative after the control it maps to.
GROUP_PREFIX = 'NIST_SP_800-53_R5_'
LABEL = re.compile(r'[A-Z]{2}-\d{1,2}(?:\(\d{1,2}\))?')
# Compliance states Azure reports. Anything else is retained as unrecognised, never as a pass.
STATES = ('Compliant', 'NonCompliant', 'Conflict', 'Exempt', 'Unknown')
RESULTS = {'Compliant': 'PASS', 'NonCompliant': 'FAIL'}
MAX_RECORDS = 5000


def control_labels(group_names):
    """Controls a definition is mapped to, as Microsoft's initiative declares them."""
    labels = []
    for name in group_names or ():
        if not isinstance(name, str) or not name.startswith(GROUP_PREFIX):
            continue
        label = name[len(GROUP_PREFIX):]
        if LABEL.fullmatch(label) and label not in labels:
            labels.append(label)
    return sorted(labels)


def definition_controls(policy_set):
    """Map each policy definition reference in an initiative to its declared controls."""
    if not isinstance(policy_set, dict):
        raise ValueError('Invalid policy set definition')
    references = policy_set.get('policyDefinitions')
    if not isinstance(references, list) or len(references) > 20000:
        raise ValueError('Invalid policy set definition references')
    mapping = {}
    for reference in references:
        if not isinstance(reference, dict):
            raise ValueError('Invalid policy definition reference')
        key = reference.get('policyDefinitionReferenceId')
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_.\-]{1,128}', key):
            continue
        mapping[key.lower()] = control_labels(reference.get('groupNames'))
    return mapping


def project(record, controls):
    """Bounded facts from one policy state. Parameters and hierarchy are not retained."""
    if not isinstance(record, dict):
        return None
    state = record.get('complianceState')
    definition = record.get('policyDefinitionReferenceId')
    target = record.get('resourceId')
    assignment = record.get('policyAssignmentId')
    if not isinstance(state, str) or state not in STATES:
        state = '[unrecognised]'
    if not isinstance(definition, str) or not re.fullmatch(r'[A-Za-z0-9_.\-]{1,128}', definition):
        definition = None
    resource = resource_id(target) if isinstance(target, str) else None
    if resource is None or definition is None:
        return None
    action = record.get('policyDefinitionAction')
    if not isinstance(action, str) or not re.fullmatch(r'[A-Za-z]{1,40}', action):
        action = '[unrecognised]'
    evaluated = record.get('timestamp')
    if not isinstance(evaluated, str) or len(evaluated) > 40:
        evaluated = None
    return {'reference': definition, 'resource_id': resource.lower(),
            'assignment': (resource_id(assignment) or '[unrecognised]').lower()
                          if isinstance(assignment, str) else '[unrecognised]',
            'action': action, 'compliance_state': state,
            'result': RESULTS.get(state, 'UNKNOWN'),
            'controls': list(controls.get(definition.lower(), ())),
            'evaluated_at': evaluated}


def collect(records, policy_set, *, assignment_name=None):
    """Project a query or export into frozen evidence. Nothing is re-evaluated."""
    if not isinstance(records, list) or len(records) > MAX_RECORDS:
        raise ValueError('Invalid policy compliance records')
    controls = definition_controls(policy_set)
    rows, dropped = [], 0
    for record in records:
        if assignment_name and str(record.get('policyAssignmentName', '')).lower() != assignment_name.lower():
            continue
        projected = project(record, controls)
        if projected is None:
            dropped += 1
            continue
        rows.append(projected)
    rows.sort(key=lambda row: (row['resource_id'], row['reference']))
    counts = {state: 0 for state in ('PASS', 'FAIL', 'UNKNOWN')}
    for row in rows:
        counts[row['result']] += 1
    unmapped = sum(1 for row in rows if not row['controls'])
    conclusion = ('FINDINGS_PRESENT' if counts['FAIL']
                  else 'INCOMPLETE' if not rows or counts['UNKNOWN'] or dropped
                  else 'PROVIDER_ASSERTED_COMPLIANT')
    return {'schema_version': '1.0', 'collected_at': now(), 'source': 'azure_policy',
            'assignment_filter': assignment_name,
            'summary': {'record_count': len(rows), 'counts': counts, 'conclusion': conclusion,
                        'unreadable_records': dropped, 'records_without_control_mapping': unmapped},
            'limits': [
                'Microsoft asserts these results; this program did not observe the configuration behind them.',
                'The control mapping is Microsoft\'s interpretation, frozen at collection time.',
                'A resource type with no applicable definition produces no record. Absent evaluation is not compliance.',
                'Definitions with the Manual effect record an attestation, not an automated observation.'],
            'results': rows}


def validate(section):
    """Structural check for a saved policy compliance section."""
    if not isinstance(section, dict) or section.get('schema_version') != '1.0':
        raise ValueError('Invalid policy compliance evidence')
    if set(section) != {'schema_version', 'collected_at', 'source', 'assignment_filter', 'summary', 'limits', 'results'}:
        raise ValueError('Invalid policy compliance fields')
    rows = section.get('results')
    if not isinstance(rows, list) or len(rows) > MAX_RECORDS:
        raise ValueError('Invalid policy compliance results')
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'reference', 'resource_id', 'assignment', 'action',
                                                     'compliance_state', 'result', 'controls', 'evaluated_at'}:
            raise ValueError('Invalid policy compliance record')
        key = (row['resource_id'], row['reference'])
        if key in seen:
            raise ValueError('Duplicate policy compliance record')
        seen.add(key)
        if row['result'] not in ('PASS', 'FAIL', 'UNKNOWN'):
            raise ValueError('Invalid policy compliance result')
        if not isinstance(row['controls'], list) or any(not LABEL.fullmatch(str(c)) for c in row['controls']):
            raise ValueError('Invalid policy compliance control reference')
    counts = {state: 0 for state in ('PASS', 'FAIL', 'UNKNOWN')}
    for row in rows:
        counts[row['result']] += 1
    if section['summary'].get('counts') != counts or section['summary'].get('record_count') != len(rows):
        raise ValueError('Saved policy compliance summary mismatch')
    return section
