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
from datetime import datetime

from .safety import now, resource_group_name, resource_id, subscription_id

# Microsoft names each control group in the initiative after the control it maps to.
GROUP_PREFIX = 'NIST_SP_800-53_R5_'
LABEL = re.compile(r'[A-Z]{2}-\d{1,2}(?:\(\d{1,2}\))?')
# Compliance states Azure reports. Anything else is retained as unrecognised, never as a pass.
STATES = ('Compliant', 'NonCompliant', 'Conflict', 'Conflicting', 'Exempt', 'Unknown',
          'Error', 'Protected', 'NotStarted', 'NotRegistered')
RESULTS = {'Compliant': 'PASS', 'NonCompliant': 'FAIL'}
MAX_RECORDS = 5000


def timestamp(value):
    if not isinstance(value, str) or len(value) > 40:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None


def incomplete(section):
    """Completeness is independent of whether the available evidence contains failures."""
    summary = section['summary']
    return source_incomplete(section) or bool(summary['counts']['UNKNOWN'])


def source_incomplete(section):
    summary = section['summary']
    return bool(not section['results'] or summary.get('truncated') or summary.get('unreadable_records')
                or summary.get('records_without_control_mapping'))


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


SCOPES = ('resource', 'resource_group', 'subscription')


def scope_of(target):
    """Policy evaluates at resource, resource group and subscription scope; all three are evidence."""
    if not isinstance(target, str) or len(target) > 1024:
        return None
    parts = target.strip('/').split('/')
    if len(parts) == 2 and parts[0].lower() == 'subscriptions' and subscription_id(parts[1]):
        return target.lower(), 'subscription'
    if (len(parts) == 4 and parts[0].lower() == 'subscriptions' and subscription_id(parts[1])
            and parts[2].lower() == 'resourcegroups' and resource_group_name(parts[3])):
        return target.lower(), 'resource_group'
    resource = resource_id(target)
    return (resource.lower(), 'resource') if resource else None


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
    scope = scope_of(target)
    if scope is None or definition is None:
        return None
    resource, scope_kind = scope
    from .policy_query import assignment_id as validated_assignment_id
    try:
        verified_assignment = validated_assignment_id(resource.split('/')[2], assignment).lower()
    except ValueError:
        verified_assignment = '[unrecognised]'
    action = record.get('policyDefinitionAction')
    if not isinstance(action, str) or not re.fullmatch(r'[A-Za-z]{1,40}', action):
        action = '[unrecognised]'
    evaluated = record.get('timestamp')
    if timestamp(evaluated) is None:
        evaluated = None
    return {'reference': definition, 'resource_id': resource, 'scope': scope_kind,
            'assignment': verified_assignment,
            'action': action, 'compliance_state': state,
            'result': (RESULTS.get(state, 'UNKNOWN') if evaluated and verified_assignment != '[unrecognised]' and action.lower() in
                       ('audit', 'auditifnotexists', 'deny', 'deployifnotexists', 'modify', 'append') else 'UNKNOWN'),
            'controls': list(controls.get(definition.lower(), ())),
            'evaluated_at': evaluated}


def collect(records, policy_set, *, assignment_name=None, assignment_id=None, subscription=None,
            resource_group=None, limit=MAX_RECORDS, as_of=None, max_age_seconds=None):
    """Project a query or export into frozen evidence. Nothing is re-evaluated.

    Live queries paginate and carry completeness metadata. Bounded exports can carry
    one extra row to signal truncation. Original provider states are always preserved.
    """
    if type(limit) is not int or not 1 <= limit <= MAX_RECORDS or not isinstance(records, list) or len(records) > limit + 1:
        raise ValueError('Invalid policy compliance records')
    if resource_group and not subscription:
        raise ValueError('Resource group evidence requires its subscription')
    collected_at = as_of or now()
    reference_time = timestamp(collected_at)
    if reference_time is None or (max_age_seconds is not None and
            (type(max_age_seconds) is not int or max_age_seconds <= 0)):
        raise ValueError('Invalid Policy freshness criteria')
    truncated = len(records) > limit or not getattr(records, 'complete', True)
    records = records[:limit]
    controls = definition_controls(policy_set)
    rows, dropped = [], 0
    for record in records:
        if not isinstance(record, dict):
            dropped += 1
            continue
        if assignment_id and str(record.get('policyAssignmentId', '')).lower() != assignment_id.lower():
            dropped += 1
            continue
        if assignment_name and str(record.get('policyAssignmentName', '')).lower() != assignment_name.lower():
            continue
        projected = project(record, controls)
        if projected is None:
            dropped += 1
            continue
        target = projected['resource_id']
        if subscription and not (target == '/subscriptions/' + subscription.lower()
                                  or target.startswith('/subscriptions/' + subscription.lower() + '/')):
            dropped += 1
            continue
        if resource_group:
            scope = '/subscriptions/' + subscription.lower() + '/resourcegroups/' + resource_group.lower()
            if target != scope and not target.startswith(scope + '/'):
                dropped += 1
                continue
        evaluated = timestamp(projected['evaluated_at'])
        if evaluated is not None:
            age = (reference_time - evaluated).total_seconds()
            if age < 0 or (max_age_seconds is not None and age > max_age_seconds):
                projected['result'] = 'UNKNOWN'
        rows.append(projected)
    rows.sort(key=lambda row: (row['resource_id'], row['reference']))
    counts = {state: 0 for state in ('PASS', 'FAIL', 'UNKNOWN')}
    for row in rows:
        counts[row['result']] += 1
    unmapped = sum(1 for row in rows if not row['controls'])
    scopes = {kind: sum(1 for row in rows if row['scope'] == kind) for kind in SCOPES}
    conclusion = ('FINDINGS_PRESENT' if counts['FAIL']
                  else 'INCOMPLETE' if truncated or not rows or counts['UNKNOWN'] or dropped or unmapped
                  else 'PROVIDER_ASSERTED_COMPLIANT')
    return {'schema_version': '1.0', 'collected_at': collected_at, 'source': 'azure_policy',
            'assignment_filter': assignment_id or assignment_name,
            'summary': {'record_count': len(rows), 'counts': counts, 'conclusion': conclusion,
                        'unreadable_records': dropped, 'records_without_control_mapping': unmapped,
                        'records_by_scope': scopes, 'truncated': truncated},
            'limits': [
                'Microsoft asserts these results; this program did not observe the configuration behind them.',
                'The control mapping is Microsoft\'s interpretation, frozen at collection time.',
                'A resource type with no applicable definition produces no record. Absent evaluation is not compliance.',
            'Manual compliance states may come from defaults or attestations; these rows do not contain authenticated attestation provenance.',
            'Invalid, future or older-than-approved evaluation times cannot support a current positive result.'
            + (' No maximum evaluation age was supplied.' if max_age_seconds is None
               else ' Maximum evaluation age: ' + str(max_age_seconds) + ' seconds.'),
                'A subscription or resource group scoped result describes that scope, not each resource inside it.']
            + (['The evaluation returned more records than this run retains. These results are a truncated '
                'sample and the absence of a finding here does not mean one does not exist.'] if truncated else []),
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
        if not isinstance(row, dict) or set(row) != {'reference', 'resource_id', 'scope', 'assignment', 'action',
                                                     'compliance_state', 'result', 'controls', 'evaluated_at'}:
            raise ValueError('Invalid policy compliance record')
        key = (row['resource_id'], row['reference'])
        if key in seen:
            raise ValueError('Duplicate policy compliance record')
        seen.add(key)
        if row['scope'] not in SCOPES:
            raise ValueError('Invalid policy compliance scope')
        if row['result'] not in ('PASS', 'FAIL', 'UNKNOWN'):
            raise ValueError('Invalid policy compliance result')
        if not isinstance(row['controls'], list) or any(not LABEL.fullmatch(str(c)) for c in row['controls']):
            raise ValueError('Invalid policy compliance control reference')
    counts = {state: 0 for state in ('PASS', 'FAIL', 'UNKNOWN')}
    for row in rows:
        counts[row['result']] += 1
    if section['summary'].get('counts') != counts or section['summary'].get('record_count') != len(rows):
        raise ValueError('Saved policy compliance summary mismatch')
    # Truncation cannot produce a clean bill of health, but a finding found is still a finding.
    if section['summary'].get('truncated') and section['summary'].get('conclusion') == 'PROVIDER_ASSERTED_COMPLIANT':
        raise ValueError('Truncated policy evidence cannot report a compliant conclusion')
    return section
