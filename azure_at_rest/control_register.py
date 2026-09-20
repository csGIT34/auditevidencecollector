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
    'A control absent from this register was never referenced by collected evidence or declared in purview. Absence is not evidence of applicability or of satisfaction.',
    'INHERITED_CLAIMED repeats a declared inheritance; this tool does not evaluate a provider assurance report, its scope, period or exceptions.',
    'EXCLUDED repeats an approved written exclusion. An unapproved or draft exclusion is not honored and remains NOT_ASSESSED.',
]


def validate_purview(document):
    """Approved control purview. Absent or draft dispositions never exclude a control."""
    if document is None:
        return None
    if not isinstance(document, dict) or set(document) - {'controls'} != {'schema_version', 'id', 'version', 'status'}:
        raise ValueError('Invalid control purview')
    if document['schema_version'] != '1.0' or document['status'] not in ('draft', 'approved'):
        raise ValueError('Invalid purview version/status')
    if any(not isinstance(document[key], str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', document[key])
           for key in ('id', 'version')):
        raise ValueError('Invalid purview identity')
    controls = document.get('controls', {})
    if not isinstance(controls, dict) or len(controls) > 2000:
        raise ValueError('Invalid purview controls')
    for label, entry in controls.items():
        if label not in CONTROLS:
            raise ValueError('Unknown control in purview: ' + str(label)[:40])
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


def _evidence(report, operational):
    """Flatten saved results into per-control evidence items. Nothing is re-evaluated."""
    items = []
    for row in report.get('results', []):
        items.append({'kind': 'encryption_rule', 'reference': row['rule_id'], 'resource_id': row['id'],
                      'result': row['result'], 'summary': row['reason'], 'controls': _labels(row.get('controls', [])),
                      'gaps': list(row.get('gaps', []))})
    for row in report.get('configuration_assessment', {}).get('results', []):
        items.append({'kind': 'configuration_predicate', 'reference': row['check_id'],
                      'resource_id': row.get('resource_id', ''), 'result': row['result'], 'summary': row['title'],
                      'controls': _labels(row.get('control_refs', [])), 'gaps': []})
    for row in (operational or {}).get('records', []):
        items.append({'kind': 'attributed_record', 'reference': row.get('id', ''), 'resource_id': row.get('scope', ''),
                      'result': 'ATTRIBUTED', 'summary': row.get('title', ''),
                      'controls': _labels(row.get('control_refs', [])), 'gaps': []})
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


def build(report, purview=None, operational=None):
    """Index a saved assessment by control. Deterministic from frozen inputs."""
    purview = validate_purview(purview)
    approved = bool(purview) and purview['status'] == 'approved'
    declared = (purview or {}).get('controls', {})
    items = _evidence(report, operational)
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
            missing.append('A ' + entry['disposition'].lower() + ' disposition is recorded in a draft purview; it is not honored here.')
        if status == 'NOT_ASSESSED':
            missing.append('No automated observation or attributed record references this control in this run.')
        if status == 'INHERITED_CLAIMED' and not entry.get('assurance_reference'):
            missing.append('No provider assurance reference is recorded for the claimed inheritance.')
        if status in ('AUTOMATED_EVIDENCE_COLLECTED', 'FINDINGS_PRESENT', 'INCOMPLETE_EVIDENCE'):
            missing.append('Assessor determination, organization-defined parameters and operating effectiveness over the assessment period are outside this evidence.')
        rows.append({'control': label, 'title': CONTROLS[label]['title'], 'family': CONTROLS[label]['family'],
                     'candidate': CONTROLS[label]['candidate'],
                     'service_applicable': label in SERVICE_APPLICABLE, 'purview': disposition,
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
            'purview': {'declared': bool(purview), 'status': (purview or {}).get('status'),
                        'id': (purview or {}).get('id'), 'version': (purview or {}).get('version'),
                        'declared_controls': len(declared)},
            'assessment': {'generated_at': report.get('generated_at'), 'tool_version': report.get('tool_version'),
                           'rule_version': report.get('rule_version'), 'mode': report.get('mode')},
            'summary': {'controls': len(rows), 'with_evidence': sum(1 for row in rows if row['evidence_count']),
                        'service_applicable': sum(1 for row in rows if row['service_applicable']),
                        'service_applicable_with_evidence': sum(1 for row in rows if row['service_applicable'] and row['evidence_count']),
                        'statuses': {state: status_counts.get(state, 0) for state in STATUSES},
                        'evidence_items': len(items)},
            'families': families, 'limits': LIMITS, 'controls': rows}


def template(scope='service'):
    """Starter purview. Default scope is the controls the deployed resource types implicate."""
    if scope not in ('service', 'candidate'):
        raise ValueError('Unknown purview template scope')
    controls = {label: {'disposition': 'IN_SCOPE', 'owner': ''}
                for label, control in sorted(CONTROLS.items())
                if (label in SERVICE_APPLICABLE if scope == 'service' else control['candidate'])}
    return {'schema_version': '1.0', 'id': 'REPLACE-WITH-APPROVED-PURVIEW-ID', 'version': '1',
            'status': 'draft', 'controls': controls}


def markdown(register):
    """Auditor-facing control index. One section per family, one row per control."""
    out = ['# Control-indexed evidence register', '',
           'Generated: ' + register['generated_at'] + '. Source assessment: ' +
           str(register['assessment']['generated_at']) + ' (' + str(register['assessment']['mode']) + ', tool ' +
           str(register['assessment']['tool_version']) + ').', '',
           'NIST catalog: ' + register['catalog_source']['version'] + '.', '']
    purview = register['purview']
    out += ['**Purview: ' + ('declared ' + str(purview['id']) + ' v' + str(purview['version']) + ' (' +
            str(purview['status']) + '), ' + str(purview['declared_controls']) + ' controls'
            if purview['declared'] else 'NOT DECLARED — every control below is UNDECLARED and no exclusion or '
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
                '| Control | Title | Applies to our resources | Purview | Status | PASS | FAIL | Other | Evidence |',
                '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        for row in members:
            counts = row['counts']
            other = sum(counts[state] for state in ('UNKNOWN', 'ERROR', 'UNSUPPORTED', 'NOT_APPLICABLE'))
            out.append('| ' + row['control'] + ' | ' + row['title'] + ' | ' +
                       ('yes' if row['service_applicable'] else 'no') + ' | ' + row['purview'] + ' | ' + row['status'] +
                       ' | ' + str(counts['PASS']) + ' | ' + str(counts['FAIL']) + ' | ' + str(other) + ' | ' +
                       str(row['evidence_count']) + ' |')
    out += ['', '## Limitations', ''] + ['- ' + limit for limit in register['limits']] + ['']
    return '\n'.join(out)
