"""Control-indexed evidence register.

Evidence is collected per resource; auditors ask per control. This module inverts the
index without re-evaluating anything: it reads a saved assessment and reports, for each
control, exactly which observations exist, which failed, and what is still missing.

No control is ever marked satisfied. Automated configuration evidence is one input to an
assessor's determination under SP 800-53A; operating effectiveness, organization-defined
parameters and the organizational objectives remain outside this tool.
"""
from collections import Counter
import json

from . import report_model
from pathlib import Path
import re

from .safety import now

INDEX = json.loads(Path(__file__).with_name('control_index.json').read_text())
CONTROLS, FAMILIES, REFERENCES = INDEX['controls'], INDEX['families'], INDEX['references']
# Controls implicated by the deployed Azure resource types, as opposed to organization-wide candidates.
SERVICE_APPLICABLE = {label for label, control in CONTROLS.items() if control['service_applicable']}

# Ordered by precedence: the first matching condition decides a control's status.
STATUSES = ('EXCLUDED', 'INHERITED_CLAIMED', 'FINDINGS_PRESENT', 'INCOMPLETE_EVIDENCE',
            'AUTOMATED_EVIDENCE_COLLECTED', 'ATTRIBUTED_EVIDENCE_ONLY', 'NOT_ASSESSED')
DISPOSITIONS = ('IN_SCOPE', 'INHERITED', 'EXCLUDED')
LABEL = re.compile(r'[A-Z]{2}-\d{1,2}(?:\(\d{1,2}\))?')

LIMITS = [
    'Evidence is indexed by control; it is not a control determination. No status in this register means a control is satisfied.',
    'AUTOMATED_EVIDENCE_COLLECTED means every mapped observation met its supplied criterion at collection time. It does not establish operating effectiveness over an assessment period, organization-defined parameter values, or the parts of a control no API can observe.',
    'A control absent from this register was never referenced by collected evidence or declared in tailoring. Absence is not evidence of applicability or of satisfaction.',
    'INHERITED_CLAIMED repeats a declared inheritance; this tool does not evaluate a provider assurance report, its scope, period or exceptions.',
    'EXCLUDED repeats an approved written exclusion. An unapproved or draft exclusion is not honored and remains NOT_ASSESSED.',
]


def validate_tailoring(document):
    """Approved control tailoring. Absent or draft dispositions never exclude a control."""
    if document is None:
        return None
    if not isinstance(document, dict) or set(document) - {'controls'} != {'schema_version', 'id', 'version', 'status'}:
        raise ValueError('Invalid control tailoring')
    if document['schema_version'] != '1.0' or document['status'] not in ('draft', 'approved'):
        raise ValueError('Invalid tailoring version/status')
    if any(not isinstance(document[key], str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', document[key])
           for key in ('id', 'version')):
        raise ValueError('Invalid tailoring identity')
    controls = document.get('controls', {})
    if not isinstance(controls, dict) or len(controls) > 2000:
        raise ValueError('Invalid tailoring controls')
    for label, entry in controls.items():
        if label not in CONTROLS:
            raise ValueError('Unknown control in tailoring: ' + str(label)[:40])
        if not isinstance(entry, dict) or entry.get('disposition') not in DISPOSITIONS:
            raise ValueError('Invalid control disposition')
        allowed = {'disposition', 'owner', 'rationale', 'assurance_reference', 'approver', 'reviewed_on'}
        if set(entry) - allowed or not isinstance(entry.get('owner', ''), str):
            raise ValueError('Invalid control disposition fields')
        if any(not isinstance(entry[key], str) or len(entry[key]) > 2000 for key in set(entry) - {'disposition'}):
            raise ValueError('Invalid control disposition text')
        if entry['disposition'] != 'IN_SCOPE' and not entry.get('rationale'):
            raise ValueError('Inherited or excluded controls require a recorded rationale')
        if entry['disposition'] == 'EXCLUDED' and not entry.get('approver'):
            raise ValueError('An excluded control requires a recorded approver')
    return document


def _labels(values):
    return [v for v in values if isinstance(v, str) and LABEL.fullmatch(v) and v in CONTROLS]


def _observed(row):
    """The value an auditor needs to see, when the predicate actually observed one."""
    observation = row.get('observation') or {}
    return observation.get('value') if observation.get('state') in ('observed', 'partial') else None


def _evidence(report, operational):
    """Flatten saved results into per-control evidence items. Nothing is re-evaluated.

    Each item carries what proves it: the resource, what was read, at which API version,
    what was observed and when. A control row is the index; these are the evidence.
    """
    items = []
    for row in report_model.resource_results(report):
        items.append({'kind': 'resource_rule', 'reference': row['rule_id'], 'resource_id': row['id'],
                      'result': row['result'], 'summary': row['reason'], 'controls': _labels(row.get('controls', [])),
                      'gaps': list(row.get('gaps', [])),
                      'proof': {'basis': row.get('basis'), 'scope': row.get('scope'),
                                'api_version': row.get('api_version'), 'observed_at': row.get('collected_at'),
                                'resource_type': row.get('type'),
                                'sources': [s['url'] for s in row.get('sources', [])]}})
    for row in report_model.configuration_results(report):
        items.append({'kind': 'configuration_predicate', 'reference': row['check_id'],
                      'resource_id': row.get('resource_id', ''), 'result': row['result'], 'summary': row['title'],
                      'controls': _labels(row.get('control_refs', [])), 'gaps': [],
                      'proof': {'property': row.get('property'), 'api_version': row.get('api_version'),
                                'observed': _observed(row), 'criterion': row.get('criterion'),
                                'observed_at': row.get('observed_at'), 'reason': row.get('reason'),
                                'sources': [row['source']] if row.get('source') else []}})
    for row in report_model.policy_results(report):
        from .policy_compliance import source_incomplete as policy_incomplete
        manual = row['action'].lower() == 'manual'
        gaps = []
        if policy_incomplete(report_model.policy_compliance(report)):
            gaps.append('The Policy evidence source is incomplete; these rows do not establish complete control coverage.')
        if manual:
            gaps.append('Manual Policy state is not an automated observation or authenticated attestation record.')
        items.append({'kind': 'policy_attestation_state' if manual else 'policy_compliance', 'reference': row['reference'],
                      'resource_id': row['resource_id'], 'result': 'UNKNOWN' if manual else row['result'],
                      'summary': 'Azure Policy asserted ' + row['compliance_state'],
                      'controls': _labels(row['controls']), 'gaps': gaps,
                      'proof': {'compliance_state': row['compliance_state'], 'evaluation_scope': row['scope'],
                                'policy_action': row['action'], 'assignment': row['assignment'],
                                'observed_at': row['evaluated_at'], 'asserted_by': 'Microsoft Azure Policy'}})
    for row in (operational or {}).get('records', []):
        items.append({'kind': 'attributed_record', 'reference': row.get('id', ''), 'resource_id': row.get('scope', ''),
                      'result': 'ATTRIBUTED', 'summary': row.get('title', ''),
                      'controls': _labels(row.get('control_refs', [])), 'gaps': [],
                      'proof': {'owner': row.get('owner'), 'period': row.get('period'),
                                'observed_at': row.get('recorded_at'), 'asserted_by': row.get('owner')}})
    return items


def _status(entry, counts, gaps, approved):
    if entry and approved and entry['disposition'] == 'EXCLUDED':
        return 'EXCLUDED'
    if entry and approved and entry['disposition'] == 'INHERITED':
        return 'INHERITED_CLAIMED'
    if counts['FAIL']:
        return 'FINDINGS_PRESENT'
    if counts['UNKNOWN'] or counts['ERROR'] or counts['UNSUPPORTED'] or gaps:
        return 'INCOMPLETE_EVIDENCE'
    if counts['PASS']:
        return 'AUTOMATED_EVIDENCE_COLLECTED'
    if counts['ATTRIBUTED']:
        return 'ATTRIBUTED_EVIDENCE_ONLY'
    return 'NOT_ASSESSED'


def build(report, tailoring=None, operational=None):
    """Index a saved assessment by control. Deterministic from frozen inputs."""
    tailoring = validate_tailoring(tailoring)
    approved = bool(tailoring) and tailoring['status'] == 'approved'
    declared = (tailoring or {}).get('controls', {})
    items = _evidence(report, operational)
    outside = sorted({label for row in report_model.policy_results(report)
                      for label in row['controls'] if label not in CONTROLS})
    selected = sorted({label for item in items for label in item['controls']} | set(declared)
                      | {label for label, control in CONTROLS.items() if control['candidate']},
                      key=lambda label: (CONTROLS[label]['family'], CONTROLS[label]['oscal_id']))
    rows = []
    for label in selected:
        entry = declared.get(label)
        evidence = [item for item in items if label in item['controls']]
        counts = Counter(item['result'] for item in evidence)
        counts = {state: counts.get(state, 0) for state in ('PASS', 'FAIL', 'UNKNOWN', 'ERROR', 'UNSUPPORTED',
                                                            'NOT_APPLICABLE', 'ATTRIBUTED')}
        gaps = sorted({gap for item in evidence for gap in item['gaps']})
        disposition = entry['disposition'] if entry else 'UNDECLARED'
        status = _status(entry, counts, gaps, approved)
        missing = list(gaps)
        if entry and not approved and entry['disposition'] != 'IN_SCOPE':
            missing.append('A ' + entry['disposition'].lower() + ' disposition is recorded in a draft tailoring; it is not honored here.')
        if status == 'NOT_ASSESSED':
            missing.append('No automated observation or attributed record references this control in this run.')
        if status == 'INHERITED_CLAIMED' and not entry.get('assurance_reference'):
            missing.append('No provider assurance reference is recorded for the claimed inheritance.')
        if CONTROLS[label].get('withdrawn') and evidence:
            missing.append('This control is withdrawn in the pinned catalog revision; evidence referencing it '
                           'should be re-pointed at its replacement.')
        if status in ('AUTOMATED_EVIDENCE_COLLECTED', 'FINDINGS_PRESENT', 'INCOMPLETE_EVIDENCE'):
            missing.append('Assessor determination, organization-defined parameters and operating effectiveness over the assessment period are outside this evidence.')
        rows.append({'control': label, 'title': CONTROLS[label]['title'], 'family': CONTROLS[label]['family'],
                     'candidate': CONTROLS[label]['candidate'],
                     'withdrawn': CONTROLS[label].get('withdrawn', False),
                     'service_applicable': label in SERVICE_APPLICABLE, 'tailoring': disposition,
                     'owner': (entry or {}).get('owner', ''), 'rationale': (entry or {}).get('rationale', ''),
                     'assurance_reference': (entry or {}).get('assurance_reference', ''),
                     'approver': (entry or {}).get('approver', ''), 'status': status, 'counts': counts,
                     'evidence_count': len(evidence), 'evidence': evidence, 'gaps': missing})
    families = []
    for family, meta in sorted(FAMILIES.items()):
        members = [row for row in rows if row['family'] == family]
        families.append({'family': family, 'title': meta['title'], 'responsibility': meta['responsibility'],
                         'controls': len(members),
                         'with_evidence': sum(1 for row in members if row['evidence_count']),
                         'not_assessed': sum(1 for row in members if row['status'] == 'NOT_ASSESSED'),
                         'findings': sum(1 for row in members if row['status'] == 'FINDINGS_PRESENT')})
    status_counts = Counter(row['status'] for row in rows)
    return {'schema_version': '1.0', 'generated_at': now(), 'catalog_source': INDEX['source'],
            'references': REFERENCES,
            'control_index_sha256': INDEX['index_sha256'],
            'tailoring': {'declared': bool(tailoring), 'status': (tailoring or {}).get('status'),
                        'id': (tailoring or {}).get('id'), 'version': (tailoring or {}).get('version'),
                        'declared_controls': len(declared)},
            'assessment': {'generated_at': report.get('generated_at'), 'tool_version': report.get('tool_version'),
                           'rule_version': report.get('rule_version'), 'mode': report.get('mode')},
            'summary': {'controls': len(rows), 'with_evidence': sum(1 for row in rows if row['evidence_count']),
                        'service_applicable': sum(1 for row in rows if row['service_applicable']),
                        'service_applicable_with_evidence': sum(1 for row in rows if row['service_applicable'] and row['evidence_count']),
                        'statuses': {state: status_counts.get(state, 0) for state in STATUSES},
                        'evidence_items': len(items),
                        'controls_outside_packaged_catalog': outside},
            'families': families, 'limits': LIMITS, 'controls': rows}


def template(scope='service'):
    """Starter tailoring. Default scope is the controls the deployed resource types implicate."""
    if scope not in ('service', 'candidate'):
        raise ValueError('Unknown tailoring template scope')
    controls = {label: {'disposition': 'IN_SCOPE', 'owner': ''}
                for label, control in sorted(CONTROLS.items())
                if (label in SERVICE_APPLICABLE if scope == 'service' else control['candidate'])}
    return {'schema_version': '1.0', 'id': 'REPLACE-WITH-APPROVED-TAILORING-ID', 'version': '1',
            'status': 'draft', 'controls': controls}


def markdown(register):
    """Auditor-facing control index. One section per family, one row per control."""
    out = ['# Control-indexed evidence register', '',
           'Generated: ' + register['generated_at'] + '. Source assessment: ' +
           str(register['assessment']['generated_at']) + ' (' + str(register['assessment']['mode']) + ', tool ' +
           str(register['assessment']['tool_version']) + ').', '',
           'NIST catalog: ' + register['catalog_source']['version'] + '.', '']
    tailoring = register['tailoring']
    out += ['**Tailoring: ' + ('declared ' + str(tailoring['id']) + ' v' + str(tailoring['version']) + ' (' +
            str(tailoring['status']) + '), ' + str(tailoring['declared_controls']) + ' controls'
            if tailoring['declared'] else 'NOT DECLARED — every control below is UNDECLARED and no exclusion or '
            'inheritance is recognized') + '**', '']
    summary = register['summary']
    out += ['Controls indexed: **' + str(summary['controls']) + '**; with evidence: **' +
            str(summary['with_evidence']) + '**; evidence items: ' + str(summary['evidence_items']) + '.', '',
            'Implicated by the deployed Azure resource types: **' + str(summary['service_applicable']) +
            '**, of which **' + str(summary['service_applicable_with_evidence']) + '** have evidence. Remaining '
            'controls are organization-wide candidates that creating these resources does not by itself implicate.', '',
            'Governing references: ' + '; '.join(reference['label'] + ' — ' + reference['role']
                                                 for reference in register['references']), '',
            '| Status | Controls |', '| --- | --- |']
    out += ['| ' + state + ' | ' + str(count) + ' |' for state, count in summary['statuses'].items()]
    out += ['', '## Families', '', '| Family | Responsibility | Controls | With evidence | Not assessed | Findings |',
            '| --- | --- | --- | --- | --- | --- |']
    for row in register['families']:
        out.append('| ' + row['family'].upper() + ' — ' + row['title'] + ' | ' + row['responsibility'] + ' | ' +
                   str(row['controls']) + ' | ' + str(row['with_evidence']) + ' | ' + str(row['not_assessed']) +
                   ' | ' + str(row['findings']) + ' |')
    for family in register['families']:
        members = [row for row in register['controls'] if row['family'] == family['family']]
        if not members:
            continue
        out += ['', '## ' + family['family'].upper() + ' — ' + family['title'], '',
                '| Control | Title | Applies to our resources | Tailoring | Status | PASS | FAIL | Other | Evidence |',
                '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        for row in members:
            counts = row['counts']
            other = sum(counts[state] for state in ('UNKNOWN', 'ERROR', 'UNSUPPORTED', 'NOT_APPLICABLE'))
            out.append('| ' + row['control'] + ' | ' + row['title'] + ' | ' +
                       ('yes' if row['service_applicable'] else 'no') + ' | ' + row['tailoring'] + ' | ' + row['status'] +
                       ' | ' + str(counts['PASS']) + ' | ' + str(counts['FAIL']) + ' | ' + str(other) + ' | ' +
                       str(row['evidence_count']) + ' |')
    out += ['', '## Limitations', ''] + ['- ' + limit for limit in register['limits']] + ['']
    return '\n'.join(out)


def _value(observed):
    if observed is None:
        return '—'
    if isinstance(observed, bool):
        return 'true' if observed else 'false'
    if isinstance(observed, (int, float, str)):
        return str(observed)[:80]
    return json.dumps(observed, sort_keys=True)[:80]


def evidence_markdown(register, *, scope='service'):
    """Auditor evidence package: per control, the observations that support it.

    An observation is evidence whether or not an approved criterion turned it into a
    pass. Criteria produce a conclusion; the underlying reading is what an assessor
    examines, so it is presented either way.
    """
    rows = [row for row in register['controls']
            if (row['service_applicable'] if scope == 'service' else True)]
    out = ['# Control evidence package', '',
           'Generated: ' + register['generated_at'] + '. Source run: ' +
           str(register['assessment']['generated_at']) + ' (' + str(register['assessment']['mode']) + ').', '',
           'Controls in scope: **' + str(len(rows)) + '**' +
           (' — the controls the collected Azure resource types implicate.' if scope == 'service' else '.'), '']
    verdicts = {status: [] for status in STATUSES}
    for row in rows:
        counts = row['counts']
        verdicts[row['status']].append(row)
    out += ['| Verdict | Controls |', '| --- | --- |']
    out += ['| ' + name + ' | ' + str(len(found)) + ' |' for name, found in verdicts.items()]
    out += ['', 'A verdict summarises the observations below it. No verdict is a control determination: '
            'an assessor decides whether this evidence satisfies the control.', '']
    for row in rows:
        counts = row['counts']
        verdict = row['status']
        out += ['## ' + row['control'] + ' — ' + row['title'], '',
                '**' + verdict + '** · passing ' + str(counts['PASS']) + ' · failing ' + str(counts['FAIL'])
                + ' · other ' + str(counts['UNKNOWN'] + counts['ERROR'] + counts['UNSUPPORTED']) + '', '']
        if not row['evidence']:
            out += ['No observation in this run references this control.', '']
            continue
        out += ['| Result | Resource | Checked | Observed | Read at | Source |',
                '| --- | --- | --- | --- | --- | --- |']
        for item in sorted(row['evidence'], key=lambda i: (i['result'] != 'FAIL', i['reference'])):
            proof = item.get('proof') or {}
            checked = (proof.get('property') or proof.get('basis') or proof.get('policy_action')
                       or item['reference'])
            observed = (_value(proof['observed']) if 'observed' in proof
                        else proof.get('compliance_state') or proof.get('asserted_by') or '—')
            source = (proof.get('sources') or [''])[0] if proof.get('sources') else ''
            out.append('| ' + item['result'] + ' | `' + item['resource_id'].rsplit('/', 1)[-1] + '` | '
                       + str(checked) + ' | ' + observed + ' | ' + str(proof.get('observed_at') or '—') + ' | '
                       + ('[api](' + source + ')' if source else '—') + ' |')
        out.append('')
    out += ['## Limitations', ''] + ['- ' + limit for limit in register['limits']] + ['']
    return '\n'.join(out)
