"""Archived, selectable audit evidence views. Never collect or reassess source facts."""
from collections import Counter
from copy import deepcopy
from io import BytesIO
import json
import re
from uuid import uuid4
from xml.sax.saxutils import escape

from . import report_model
from .archive import digest, encode, identity, load_run
from .safety import now

ENCRYPTION = {'schema_version': '1.0', 'id': 'encryption-at-rest', 'version': '1',
              'title': 'Encryption at rest', 'resource_rules': True,
              'checks': ['ST-cmk-key', 'ACR-cmk-key', 'APPC-cmk-key', 'REDIS-cmk-key'],
              'policy_references': [], 'controls': ['SC-28', 'SC-28(1)']}


def request_options(body):
    """Bounded, explicit saved-run selection for the hosted report operation."""
    allowed = {'run_id', 'topic', 'topic_profile', 'controls', 'families', 'resource_ids', 'wiz_import_id', 'operational_ids'}
    if not isinstance(body, dict) or 'run_id' not in body or set(body) - allowed:
        raise ValueError('Invalid evidence report request')
    options = {'run_id': identity(body['run_id'], 'r'), 'pdf': True}
    if 'topic' in body:
        if body['topic'] != 'encryption-at-rest' or 'topic_profile' in body:
            raise ValueError('Invalid topic selector')
        options['topic'] = deepcopy(ENCRYPTION)
    if 'topic_profile' in body:
        options['topic'] = profile(body['topic_profile'])
    for key, maximum in (('controls', 2000), ('families', 20), ('resource_ids', 100), ('operational_ids', 100)):
        value = body.get(key, [])
        if not isinstance(value, list) or len(value) > maximum or any(not isinstance(v, str) or len(v) > 1024 for v in value):
            raise ValueError('Invalid evidence selector')
        options[key] = value
    if any(not re.fullmatch(r'[A-Z]{2}-\d{1,2}(?:\(\d{1,2}\))?', v) for v in options['controls']) or any(
            not re.fullmatch(r'[A-Z]{2}', v) for v in options['families']):
        raise ValueError('Invalid control selector')
    for value in options['operational_ids']:
        identity(value, 'o')
    if 'wiz_import_id' in body:
        options['wiz_import_id'] = identity(body['wiz_import_id'], 'w')
    return options


def profile(value):
    """A reviewed selection map, not new assessment criteria or a Policy interpreter."""
    if value is None:
        return None
    required = {'schema_version', 'id', 'version', 'title', 'resource_rules', 'checks', 'policy_references', 'controls'}
    if not isinstance(value, dict) or set(value) - {'wiz_rules', 'wiz_observations', 'objective_ids'} != required or value['schema_version'] != '1.0':
        raise ValueError('Invalid topic profile')
    if type(value['resource_rules']) is not bool:
        raise ValueError('Invalid topic resource selection')
    for key in ('id', 'version', 'title'):
        if not isinstance(value[key], str) or not value[key].strip() or len(value[key]) > 160:
            raise ValueError('Invalid topic identity')
    for key in ('checks', 'controls', 'objective_ids'):
        if key not in value:
            continue
        if not isinstance(value[key], list) or len(value[key]) > 2000 or any(
                not isinstance(v, str) or not re.fullmatch(r'[A-Za-z0-9_.()\-]{1,128}', v) for v in value[key]):
            raise ValueError('Invalid topic selector')
    if not isinstance(value['policy_references'], list) or len(value['policy_references']) > 2000:
        raise ValueError('Invalid topic policy mapping')
    for item in value['policy_references']:
        if not isinstance(item, dict) or set(item) != {'assignment', 'reference'}:
            raise ValueError('Invalid topic policy mapping')
        if not isinstance(item['assignment'], str) or len(item['assignment']) > 1024 or not re.fullmatch(
                r'[A-Za-z0-9_.\-]{1,128}', str(item['reference'])):
            raise ValueError('Invalid topic policy mapping')
    if 'wiz_observations' in value and type(value['wiz_observations']) is not bool:
        raise ValueError('Invalid Wiz observation selector')
    if 'wiz_rules' in value and (not isinstance(value['wiz_rules'], list) or
            len(value['wiz_rules']) > 2000 or any(not isinstance(v, str) or not re.fullmatch(r'[A-Za-z0-9_.:\-]{1,128}', v) for v in value['wiz_rules'])):
        raise ValueError('Invalid Wiz rule selector')
    return deepcopy(value)


def records(saved):
    report, context = saved['assessment'], saved['context']
    found = []
    for row in report_model.resource_results(report):
        rule = context['rule_catalog'].get(row['type'].lower(), {})
        found.append({'kind': 'resource_rule', 'reference': row['rule_id'], 'resource_id': row['id'],
            'title': row['name'] + ' - ' + row['rule_id'], 'result': row['result'],
            'controls': row.get('controls', []), 'observed_at': row['collected_at'],
            'observations': row['evidence'], 'criterion': context['criteria_by_mode'].get(rule.get('mode'), 'Not recorded'),
            'explanation': row['reason'], 'boundaries': row['scope'], 'gaps': row['gaps'],
            'dependencies': row['dependencies'], 'provenance': {'api_version': row['api_version'],
                'basis': row['basis'], 'sources': row['sources'], 'errors': row['errors'],
                'verification_commands': row['verification_commands']}})
    for row in report_model.configuration_results(report):
        found.append({'kind': 'configuration_predicate', 'reference': row['check_id'],
            'resource_id': row['resource_id'], 'title': row['title'], 'result': row['result'],
            'controls': row.get('control_refs', []), 'observed_at': row['observed_at'],
            'observations': row['observation'], 'criterion': row['criterion'], 'explanation': row['reason'],
            'boundaries': row['catalog_ref'], 'gaps': [], 'dependencies': [],
            'provenance': {key: row[key] for key in ('api_version', 'source', 'freshness', 'job_evaluation',
                           'lifecycle_evaluation') if key in row}})
    for row in report_model.policy_results(report):
        manual = row['action'].lower() == 'manual'
        found.append({'kind': 'policy_attestation_state' if manual else 'policy_compliance',
            'reference': row['reference'], 'resource_id': row['resource_id'], 'title': row['reference'],
            'result': 'UNKNOWN' if manual else row['result'], 'controls': row['controls'],
            'observed_at': row['evaluated_at'], 'observations': {'provider_state': row['compliance_state'],
                'effect': row['action']}, 'criterion': 'Effective Policy parameters are not present in this source schema.',
            'explanation': 'Saved Microsoft Azure Policy assertion.', 'boundaries': row['scope'],
            'gaps': ['Manual state has no authenticated attestation provenance.'] if manual else [],
            'dependencies': [], 'provenance': {'assignment': row['assignment'], 'source': 'azure_policy'}})
    return found


def operational_records(imported):
    """Use the supplement's frozen objective mapping and freshness, not today's rules."""
    review = imported['report']
    rows = []
    for row in review['records']:
        definitions = {key: review['objective_definitions'][key] for key in row['objective_ids']}
        rows.append({'kind': 'attributed_record', 'reference': row['record_id'],
            'resource_id': row['resource_ids'][0] if len(row['resource_ids']) == 1 else '',
            'title': row['evidence_type'] + ' - ' + row['record_id'],
            'result': 'ATTRIBUTED_' + row['assertion'],
            'controls': sorted({c for value in definitions.values() for c in value['controls']}),
            'observed_at': row['observed_at'], 'observations': {
                key: row[key] for key in ('assertion', 'summary', 'period_start', 'period_end', 'freshness')},
            'criterion': {'basis': 'Candidate objective text, not an approved automated criterion',
                          'objectives': definitions},
            'explanation': 'Operator-supplied statement; does not override automated observations or establish control satisfaction.',
            'boundaries': row['scope_kind'],
            'gaps': ['Declared owner, reviewer and document reference are not independently authenticated.']
                    + ([] if row['freshness'] == 'CURRENT' else ['The saved review marked this record ' + row['freshness'] + '.']),
            'dependencies': [], 'provenance': {'evidence_id': review['evidence_id'],
                'owner': row['owner'], 'reviewer': row['reviewer'], 'reference_sha256': row['reference_sha256'],
                'objective_ids': row['objective_ids'], 'resource_ids': row['resource_ids'],
                'review_as_of': review['as_of'], 'max_age_hours': review['max_age_hours']}})
    return rows


def build(saved, *, topic=None, controls=(), families=(), resource_ids=(), wiz=None, operational=()):
    topic = profile(topic)
    controls, families = list(controls), list(families)
    if any(not re.fullmatch(r'[A-Z]{2}-\d{1,2}(?:\(\d{1,2}\))?', c) for c in controls):
        raise ValueError('Invalid control selector')
    if any(not re.fullmatch(r'[A-Z]{2}', f) for f in families):
        raise ValueError('Invalid family selector')
    if any(not isinstance(r, str) or not 1 <= len(r) <= 1024 for r in resource_ids):
        raise ValueError('Invalid resource selector')
    requested = {r.lower() for r in resource_ids}
    population = {r['id'].lower(): r for r in saved['snapshot']['resources'] +
                  saved['snapshot'].get('identity_evidence', {}).get('resources', [])}
    if requested - set(population):
        raise ValueError('Selected resource is absent from the saved inventory')
    selected_population = requested or set(population)
    source_records = records(saved)
    operational_sources = []
    for imported in operational:
        review = imported['report']
        if review['source_run_id'] != saved['manifest']['run_id'] or review['source_manifest_sha256'] != saved['manifest_sha256']:
            raise ValueError('Operational evidence refers to a different source run')
        source_records.extend(operational_records(imported))
        operational_sources.append({'evidence_id': review['evidence_id'], 'manifest_sha256': imported['manifest_sha256'],
            'as_of': review['as_of'], 'max_age_hours': review['max_age_hours'],
            'requirements': deepcopy(review.get('requirements', [])),
            'requirement_results': deepcopy(review.get('requirement_results', [])),
            'limitations': deepcopy(review['limitations'])})
    wiz_gaps, wiz_scans, wiz_context = [], [], []
    if wiz is not None:
        from .wiz_observations import report_records
        source = wiz['document']['source']
        scope = source['scope']
        subscriptions = saved['snapshot']['inventory']['subscriptions']
        if set(scope['subscription_ids']) != {s['id'].lower() for s in subscriptions} or any(
                (s.get('resource_group') or '').lower() != (scope['resource_group'] or '').lower() for s in subscriptions):
            raise ValueError('Wiz and Azure scopes differ')
        if (saved['assessment']['mode'] == 'offline_fixture') != (source['mode'] == 'synthetic'):
            raise ValueError('Wiz and Azure source modes differ')
        provenance = saved['context'].get('execution_provenance') or {}
        if provenance.get('tenant_id') and provenance['tenant_id'].lower() != source['tenant_id']:
            raise ValueError('Wiz and Azure tenants differ')
        wiz_gaps.append('Wiz provenance and control mappings are operator assertions; native authentication is not established by an import.')
        if not source['inventory_complete'] or not source['findings_complete'] or not wiz['document'].get('evaluations_complete', False):
            wiz_gaps.append('Wiz inventory, finding or evaluation coverage is incomplete or was not supplied.')
        extra = report_records(wiz['document'])
        source_records.extend(extra)
        wiz_scans = deepcopy(wiz['document'].get('scans', []))
        if any(scan['status'] != 'complete' or not scan['results_complete'] for scan in wiz_scans):
            wiz_gaps.append('One or more Wiz scans failed or have incomplete evaluated coverage.')
        wiz_gaps.append('Wiz evaluation times are preserved; no approved cross-source freshness criterion was supplied to this report.')
        for r in wiz['document']['resources']:
            if r['resource_id'].lower() not in population:
                wiz_gaps.append('Wiz-only resource requires population reconciliation: ' + r['resource_id'])
    mappings = {(m['assignment'].lower(), m['reference'].lower()) for m in (topic or {}).get('policy_references', [])}

    def relevant(row):
        if controls or families:
            if not any(c in controls or c.split('-')[0] in families for c in row['controls']):
                return False
        if not topic:
            return True
        if row['kind'] == 'resource_rule':
            return topic['resource_rules']
        if row['kind'] == 'configuration_predicate':
            return row['reference'] in topic['checks']
        if row['kind'] == 'attributed_record':
            return bool(set(row['provenance']['objective_ids']) & set(topic.get('objective_ids', [])))
        if row['kind'].startswith('wiz_'):
            return (row['kind'] == 'wiz_observation' and topic.get('wiz_observations', False)) or row['reference'] in topic.get('wiz_rules', [])
        return (row['provenance']['assignment'].lower(), row['reference'].lower()) in mappings

    def in_scope(row):
        if not requested:
            return True
        if row['kind'] == 'attributed_record':
            return row['boundaries'] == 'run' or bool(requested & {r.lower() for r in row['provenance']['resource_ids']})
        return row['resource_id'].lower() in requested

    chosen = [deepcopy(r) for r in source_records if relevant(r) and in_scope(r)]
    gaps = list(wiz_gaps)
    if operational_sources:
        gaps.append('Attached operating records are attributed statements. Their periods and saved review outcomes remain distinct from automated results.')
        if any(r['state'] != 'ASSERTED_SATISFIED' for source in operational_sources for r in source['requirement_results']):
            gaps.append('An attached operating-evidence review contains missing, conflicting, stale or adverse evidence.')
    if wiz is not None and topic:
        wiz_context = [deepcopy(r) for r in source_records if r['kind'].startswith('wiz_') and
            not relevant(r) and set(r['controls']) & set(topic['controls']) and
            (not requested or r['resource_id'].lower() in requested)]
        if wiz_context:
            gaps.append(str(len(wiz_context)) + ' related Wiz evaluations have no explicit topic rule mapping; retained as context.')
    if not saved['snapshot']['inventory']['complete']:
        gaps.append('Source inventory is incomplete; absent resources cannot be treated as absent from the estate.')
    if saved['snapshot']['errors']:
        gaps.append('Source collection contains read errors; inspect the retained errors for the selected scope.')
    policy = report_model.policy_compliance(saved['assessment'])
    if policy:
        gaps.append('Policy definition versions, effective parameters and exemption/attestation documents are not captured by this source schema; provider assertions have that interpretation limit.')
        from .policy_compliance import source_incomplete
        if source_incomplete(policy):
            gaps.append('The source Policy collection is incomplete; missing evaluations may affect this selection.')
        if topic:
            unmapped = [r for r in report_model.policy_results(saved['assessment']) if
                set(r['controls']) & set(topic['controls']) and (r['assignment'].lower(), r['reference'].lower()) not in mappings
                and (not requested or r['resource_id'].lower() in requested)]
            if unmapped:
                gaps.append(str(len(unmapped)) + ' Policy states reference related controls but lack an explicit topic mapping. '
                            'They are retained as context, not counted as topic evaluations.')
        else:
            unmapped = []
    else:
        unmapped = []
        gaps.append('Azure Policy evidence was not collected in this source run.')
    represented = {r['resource_id'].lower() for r in chosen}
    uncovered = sorted(selected_population - represented)
    if uncovered:
        gaps.append(str(len(uncovered)) + ' inventory resources have no saved evaluation for this selection; applicability is unresolved.')
    if not chosen:
        gaps.append('No matching evidence was collected; an empty report is not a positive conclusion.')
    expected_controls = set(controls) | set((topic or {}).get('controls', []))
    observed_controls = {c for row in chosen for c in row['controls']}
    for control in sorted(expected_controls - observed_controls):
        gaps.append('No selected observation references requested control ' + control + '.')
    dependencies = {d['id'].lower() for r in chosen for d in r['dependencies'] if d.get('id')}
    supporting, visited = [], set(represented)
    dependency_rows = {r['resource_id'].lower(): r for r in source_records if r['kind'] == 'resource_rule'}
    while dependencies - visited:
        pending = dependencies - visited
        visited.update(pending)
        for rid in sorted(pending):
            if rid not in dependency_rows:
                gaps.append('Referenced dependency has no saved resource-rule evidence: ' + rid)
                continue
            row = deepcopy(dependency_rows[rid])
            supporting.append(row)
            dependencies.update(d['id'].lower() for d in row['dependencies'] if d.get('id'))
    counts = dict(sorted(Counter(r['result'] for r in chosen).items()))
    from .control_register import CONTROLS, INDEX
    indexed = set(controls) | set((topic or {}).get('controls', [])) | observed_controls
    if families:
        indexed |= {c for c in CONTROLS if c.split('-')[0] in families}
    elif not topic and not controls:
        indexed |= {c for c, detail in CONTROLS.items() if detail['candidate']}
    control_coverage = []
    for control in sorted(indexed):
        evidence = [r for r in chosen if control in r['controls']]
        control_coverage.append({'control': control, 'title': CONTROLS.get(control, {}).get('title', 'Source-mapped control'),
            'evidence_count': len(evidence), 'counts': dict(Counter(r['result'] for r in evidence)),
            'status': 'EVIDENCE_PRESENT' if evidence else 'NOT_ASSESSED', 'applicability': 'UNDECLARED'})
    unassessed = sum(r['status'] == 'NOT_ASSESSED' for r in control_coverage)
    if unassessed:
        gaps.append(str(unassessed) + ' indexed controls have no selected evidence. Applicability and ownership require declared tailoring.')
    incomplete = bool(gaps or any(r['gaps'] or r['result'] in ('UNKNOWN', 'ERROR', 'UNSUPPORTED') for r in chosen))
    return {'schema_version': '1.0', 'kind': 'evidence_report', 'generated_at': now(),
        'title': topic['title'] if topic else 'Selected audit evidence' if controls or families or requested else 'Audit evidence',
        'source_run_id': saved['manifest']['run_id'], 'source_manifest_sha256': saved['manifest_sha256'],
        'source_mode': saved['assessment']['mode'], 'selection': {'topic': topic, 'controls': controls,
            'families': families, 'resource_ids': sorted(requested)},
        'source_scope': saved['snapshot']['inventory'],
        'source_criteria': deepcopy((report_model.configuration(saved['assessment']) or {}).get('policy')),
        'policy_source_context': ({key: deepcopy(policy[key]) for key in ('source', 'collected_at', 'assignment_filter', 'summary', 'limits')}
                                  if policy else None),
        'source_summary': report_model.overall(saved['assessment']),
        'control_index_sha256': INDEX['index_sha256'], 'control_coverage': control_coverage,
        'summary': {'record_count': len(chosen), 'counts': counts, 'coverage_incomplete': incomplete,
            'finding_count': counts.get('FAIL', 0), 'inventory_resource_count': len(selected_population)},
        'resources_without_selected_evidence': uncovered,
        'records': chosen, 'supporting_dependencies': supporting, 'related_policy_context': deepcopy(unmapped),
        'related_wiz_context': wiz_context, 'wiz_scans': wiz_scans,
        'operational_sources': operational_sources,
        'wiz_source': ({'import_id': wiz['manifest']['wiz_import_id'], 'manifest_sha256': wiz['manifest_sha256'],
                        'source': deepcopy(wiz['document']['source'])} if wiz else None),
        'source_errors': deepcopy(saved['snapshot']['errors']), 'gaps': gaps,
        'limits': ['Positive, negative and unknown evidence is retained. No result determines NIST control satisfaction.',
                   'This derived report selects saved observations; it neither recollects nor reassesses the source run.',
                   'Control/topic selection does not establish complete coverage of every control objective.',
                   'A failed criterion is evidence, not a failed archive publication.']}


def markdown(document):
    lines = ['# ' + document['title'], '', 'Source run: ' + document['source_run_id'],
             'Source manifest SHA-256: ' + document['source_manifest_sha256'],
             'Mode: ' + document['source_mode'], '', '## Selected evidence', '',
             'Summary: ' + json.dumps(document['summary'], sort_keys=True), '']
    for label, value in (('Selection', document['selection']), ('Coverage gaps', document['gaps']),
                         ('Collected scope', document['source_scope']), ('Saved approved/draft criteria', document['source_criteria']),
                         ('Policy source context', document['policy_source_context']),
                         ('Resources without selected evidence', document['resources_without_selected_evidence']),
                         ('Source read errors', document['source_errors'])):
        lines += ['## ' + label, '', '```json', json.dumps(value, indent=2, sort_keys=True), '```', '']
    lines += ['## Control evidence index', '', '| Control | Evidence records | State |', '| --- | ---: | --- |']
    lines += ['| ' + row['control'] + ' | ' + str(row['evidence_count']) + ' | ' + row['status'] + ' |' for row in document['control_coverage']]
    lines.append('')
    for row in document['records']:
        lines += ['## ' + row['result'] + ' - ' + row['title'], '', '```json', json.dumps(row, indent=2, sort_keys=True), '```', '']
    for label, key in (('Supporting dependencies', 'supporting_dependencies'), ('Unclassified Policy context', 'related_policy_context')):
        lines += ['## ' + label, '', '```json', json.dumps(document[key], indent=2, sort_keys=True), '```', '']
    for key in ('wiz_source', 'wiz_scans', 'related_wiz_context', 'operational_sources'):
        lines += ['## ' + key, '', '```json', json.dumps(document[key], indent=2, sort_keys=True), '```', '']
    return '\n'.join(lines + ['## Limits', ''] + ['- ' + s for s in document['limits']]) + '\n'


def render_pdf(document):
    from .pdf_report import serialized_render, renderer_dependencies, inline
    renderer_dependencies()
    @serialized_render
    def render():
        from pathlib import Path
        import reportlab
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle
        pdfmetrics.registerFont(TTFont('EvidenceVera', str(Path(reportlab.__file__).with_name('fonts') / 'Vera.ttf')))
        styles = getSampleStyleSheet()
        for name in ('Normal', 'Heading1', 'Heading2'):
            styles[name].fontName = 'EvidenceVera'
            styles[name].wordWrap = 'CJK'
        styles['Normal'].fontSize = 8
        styles['Normal'].leading = 11
        styles['Heading2'].fontSize = 11
        styles['Heading2'].textColor = colors.HexColor('#126D78')
        story, output = [], BytesIO()
        def add(label, value):
            text = (label + ': ' + inline(value)).encode('ascii', 'backslashreplace').decode()
            story.extend([Paragraph(escape(text), styles['Normal']), Spacer(1, 5)])
        story.append(Paragraph(escape(document['title']), styles['Heading1']))
        for name in ('generated_at', 'source_mode', 'source_run_id', 'source_manifest_sha256', 'source_scope', 'selection', 'summary', 'gaps', 'limits',
                     'resources_without_selected_evidence', 'source_errors'):
            add(name.replace('_', ' ').capitalize(), document[name])
        story.append(Paragraph('Control evidence index', styles['Heading1']))
        cells = [['Control', 'Evidence records', 'State']]
        cells += [[r['control'], str(r['evidence_count']), r['status']] for r in document['control_coverage']]
        table = LongTable([[Paragraph(escape(c), styles['Normal']) for c in row] for row in cells],
                          colWidths=[95, 115, 300], repeatRows=1)
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E3EDF2')),
                                   ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
        story.append(table)
        for section, rows in (('Evidence', document['records']), ('Supporting dependency evidence', document['supporting_dependencies'])):
            if not rows:
                continue
            story.append(Paragraph(section, styles['Heading1']))
            for row in rows:
                story.append(Paragraph(escape(row['result'] + ' - ' + row['title']), styles['Heading2']))
                for name in ('resource_id', 'kind', 'reference', 'controls', 'observed_at', 'observations', 'criterion',
                             'explanation', 'boundaries', 'gaps', 'dependencies', 'provenance'):
                    value = row[name]
                    if name == 'provenance':
                        value = {k: v for k, v in value.items() if k != 'verification_commands'}
                    add(name.replace('_', ' ').capitalize(), value)
        if document['related_policy_context']:
            story.append(Paragraph('Related Policy context: not classified as topic evidence', styles['Heading1']))
            for row in document['related_policy_context']:
                add('Saved assertion', row)
        if document['wiz_source']:
            story.append(Paragraph('Wiz source and scan evidence', styles['Heading1']))
            add('Source', document['wiz_source'])
            for scan in document['wiz_scans']:
                add('Scan', scan)
            for row in document['related_wiz_context']:
                add('Related unclassified context', row)
        if document['operational_sources']:
            story.append(Paragraph('Operating evidence periods and requirements', styles['Heading1']))
            for source in document['operational_sources']:
                add('Saved review', source)
        if document['source_criteria']:
            add('Saved criteria identity', {key: document['source_criteria'].get(key) for key in ('id', 'version', 'status', 'max_observation_age_seconds')})
        if document['policy_source_context']:
            add('Policy source context', document['policy_source_context'])
        if document.get('execution_provenance'):
            add('Report generation provenance', document['execution_provenance'])
        def footer(canvas, doc):
            canvas.setFont('Helvetica', 8)
            canvas.drawString(40, 24, 'SYNTHETIC EVIDENCE' if document['source_mode'] == 'offline_fixture' else 'SAVED AUDIT EVIDENCE')
            canvas.drawRightString(570, 24, 'Page ' + str(doc.page))
        SimpleDocTemplate(output, title=document['title'], leftMargin=40, rightMargin=40,
                          topMargin=40, bottomMargin=42).build(story, onFirstPage=footer, onLaterPages=footer)
        return output.getvalue()
    return render()


def publish(store, run_id, *, topic=None, controls=(), families=(), resource_ids=(), pdf=False, wiz_import_id=None,
            operational_ids=(), provenance=None, deadline=None):
    if deadline:
        deadline.check()
    saved = load_run(store, run_id)
    from .wiz import load_export
    wiz = load_export(store, wiz_import_id) if wiz_import_id else None
    from .operational import load as load_operational
    if len(set(operational_ids)) != len(operational_ids) or len(operational_ids) > 100:
        raise ValueError('Invalid operational supplement selection')
    operational = [load_operational(store, key) for key in operational_ids]
    document = build(saved, topic=topic, controls=controls, families=families, resource_ids=resource_ids, wiz=wiz, operational=operational)
    if provenance is not None:
        from .provenance import validate_provenance
        document['execution_provenance'] = deepcopy(validate_provenance(provenance))
        source_tenant = (saved['context'].get('execution_provenance') or {}).get('tenant_id')
        if source_tenant and source_tenant.lower() != provenance['tenant_id'].lower():
            raise ValueError('Report identity and source tenants differ')
    if deadline:
        deadline.check()
    report_id = 'e-' + uuid4().hex
    prefix = 'evidence-reports/' + report_id
    content = {'report.json': encode(document), 'report.md': markdown(document).encode()}
    if pdf:
        content['report.pdf'] = render_pdf(document)
    manifest = {'schema_version': '1.0', 'kind': 'evidence_report', 'state': 'complete', 'report_id': report_id,
                'generated_at': document['generated_at'], 'source_run_id': run_id,
                'source_manifest_sha256': saved['manifest_sha256'], 'objects': {}}
    if deadline:
        deadline.check()
    store.put_new(prefix + '/intent.json', encode({k: v for k, v in manifest.items() if k not in ('state', 'objects')}))
    try:
        for name, raw in content.items():
            if deadline:
                deadline.check()
            key = prefix + '/' + name
            store.put_new(key, raw)
            manifest['objects'][name] = {'key': key, 'bytes': len(raw), 'sha256': digest(raw)}
        if deadline:
            deadline.check()
        store.put_new(prefix + '/manifest.json', encode(manifest))
    except Exception:
        from .archive import _failure
        _failure(store, prefix, 'evidence_report_publication')
        raise
    return manifest


def load(store, report_id):
    prefix = 'evidence-reports/' + identity(report_id, 'e')
    try:
        store.read(prefix + '/failure.json')
    except FileNotFoundError:
        pass
    else:
        raise ValueError('Failed evidence report publication')
    manifest = json.loads(store.read(prefix + '/manifest.json'))
    if (manifest.get('schema_version'), manifest.get('kind'), manifest.get('state'), manifest.get('report_id')) != ('1.0', 'evidence_report', 'complete', report_id):
        raise ValueError('Invalid evidence report manifest')
    objects = manifest['objects']
    if set(objects) not in ({'report.json', 'report.md'}, {'report.json', 'report.md', 'report.pdf'}):
        raise ValueError('Incomplete evidence report')
    values = {}
    for name, descriptor in objects.items():
        if descriptor['key'] != prefix + '/' + name:
            raise ValueError('Report object escaped its archive')
        data = store.read(descriptor['key'])
        if len(data) != descriptor['bytes'] or digest(data) != descriptor['sha256']:
            raise ValueError('Evidence report integrity mismatch')
        values[name] = data
    source = load_run(store, manifest['source_run_id'])
    if source['manifest_sha256'] != manifest['source_manifest_sha256']:
        raise ValueError('Evidence source changed')
    report = json.loads(values['report.json'])
    if any(report[k] != manifest[k] for k in ('source_run_id', 'source_manifest_sha256')):
        raise ValueError('Evidence report source mismatch')
    if report.get('wiz_source'):
        from .wiz import load_export
        imported = load_export(store, report['wiz_source']['import_id'])
        if imported['manifest_sha256'] != report['wiz_source']['manifest_sha256']:
            raise ValueError('Wiz source changed')
    from .operational import load as load_operational
    for item in report.get('operational_sources', []):
        imported = load_operational(store, item['evidence_id'])
        if imported['manifest_sha256'] != item['manifest_sha256']:
            raise ValueError('Operational source changed')
    return {'manifest': manifest, 'report': report, 'markdown': values['report.md'].decode()}
