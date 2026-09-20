"""Correlate saved Azure and normalized Wiz evidence without reassessment."""
from collections import Counter, defaultdict
import math
from uuid import uuid4

from . import __version__
from .archive import digest, encode, load_run
from .safety import now
from .wiz import _failure, load_export, require, timestamp


def reconcile(saved, imported, *, as_of, max_age_hours, max_skew_hours):
    for limit in (max_age_hours, max_skew_hours):
        require(type(limit) in (int, float) and math.isfinite(limit) and 0 <= limit <= 87600)
    require(max_age_hours > 0)
    reference = timestamp(as_of)
    snapshot, assessment = saved['snapshot'], saved['assessment']
    source = imported['document']['source']
    synthetic = snapshot['mode'] == 'offline_fixture'
    require(synthetic == (source['mode'] == 'synthetic'))
    scope = source['scope']
    azure_scope = snapshot['inventory']['subscriptions']
    require({s['id'].lower() for s in azure_scope} == set(scope['subscription_ids']))
    for sub in azure_scope:
        require((sub.get('resource_group') or '').lower() == (scope['resource_group'] or '').lower())
    provenance = saved['context'].get('execution_provenance') or {}
    tenant = provenance.get('tenant_id')
    if tenant is not None:
        require(tenant.lower() == source['tenant_id'])
    timestamp_checks = [snapshot['started_at'], snapshot['completed_at'], source['exported_at']]
    timestamp_checks += [r['observed_at'] for r in imported['document']['resources'] + imported['document']['findings']]
    timestamp_checks += [r['collected_at'] for r in snapshot['resources']]
    require(all(timestamp(t) <= reference for t in timestamp_checks))
    azure = {r['id'].lower():r for r in assessment['results']}
    wiz = {r['resource_id'].lower():r for r in imported['document']['resources']}
    finding_index = defaultdict(list)
    for finding in imported['document']['findings']:
        finding_index[finding['resource_id'].lower()].append(finding)
    gaps = []
    if not tenant:
        gaps.append('azure_tenant_not_recorded')
    elif provenance.get('tenant_validation') != 'arm_subscription_metadata':
        gaps.append('azure_tenant_not_authenticated')
    if not snapshot['inventory']['complete']:
        gaps.append('azure_inventory_incomplete')
    if not source['inventory_complete']:
        gaps.append('wiz_inventory_incomplete')
    if not source['findings_complete']:
        gaps.append('wiz_findings_incomplete')
    if not azure and not wiz:
        gaps.append('empty_population')
    rows = []
    for key in sorted(set(azure) | set(wiz)):
        direct, external = azure.get(key), wiz.get(key)
        presence = 'BOTH' if direct and external else 'AZURE_ONLY' if direct else 'WIZ_ONLY'
        row_gaps = []
        if presence != 'BOTH':
            row_gaps.append('inventory_difference_requires_review')
        observations = []
        if direct:
            observations.append(('azure', direct['collected_at']))
        if external:
            observations.append(('wiz', external['observed_at']))
        for system, observed in observations:
            if (reference - timestamp(observed)).total_seconds() > max_age_hours * 3600:
                row_gaps.append(system + '_observation_stale')
        if direct and external and abs((timestamp(direct['collected_at']) - timestamp(external['observed_at'])).total_seconds()) > max_skew_hours * 3600:
            row_gaps.append('observation_time_skew')
        findings = []
        for finding in sorted(finding_index[key], key=lambda f:f['finding_id']):
            copied = dict(finding)
            copied['stale'] = (reference - timestamp(finding['observed_at'])).total_seconds() > max_age_hours * 3600
            copied['within_time_window'] = direct is not None and abs((timestamp(direct['collected_at']) - timestamp(finding['observed_at'])).total_seconds()) <= max_skew_hours * 3600
            if copied['stale']:
                row_gaps.append('wiz_finding_stale')
            if direct and not copied['within_time_window']:
                row_gaps.append('finding_time_skew')
            findings.append(copied)
        rows.append({'resource_id':direct['id'] if direct else external['resource_id'], 'presence':presence,
                     'azure':{**{field:direct[field] for field in ('result', 'rule_id', 'rule_version', 'reason', 'scope', 'basis', 'gaps', 'collection_status')},
                              'observed_at':direct['collected_at']} if direct else None,
                     'wiz':dict(external) if external else None, 'wiz_findings':findings, 'gaps':sorted(set(row_gaps))})
    counts = Counter(row['presence'] for row in rows)
    return {'schema_version':'1.0', 'kind':'wiz_azure_reconciliation', 'generator_version':__version__,
            'synthetic':synthetic, 'as_of':as_of, 'max_age_hours':max_age_hours, 'max_skew_hours':max_skew_hours,
            'source_run_id':saved['manifest']['run_id'], 'source_run_manifest_sha256':saved['manifest_sha256'],
            'wiz_import_id':imported['manifest']['wiz_import_id'], 'wiz_manifest_sha256':imported['manifest_sha256'],
            'wiz_input_sha256':imported['manifest']['input_sha256'], 'wiz_source':source,
            'azure_tenant_id':tenant, 'azure_tenant_validation':provenance.get('tenant_validation', 'not_recorded'),
            'azure_inventory_complete':snapshot['inventory']['complete'],
            'azure_assessment_conclusion':assessment['summary']['conclusion'],
            'azure_coverage_incomplete':assessment['summary']['coverage_incomplete'],
            'state':'REVIEW_REQUIRED' if gaps or any(r['gaps'] for r in rows) else 'COMPARISON_COMPLETE',
            'presence_counts':{k:counts[k] for k in ('BOTH', 'AZURE_ONLY', 'WIZ_ONLY')},
            'finding_count':len(imported['document']['findings']), 'gaps':gaps, 'resources':rows,
            'limitations':['Presence is a source comparison, not a compliance finding.',
                           'Wiz severities/statuses are preserved; no rule equivalence or NIST conclusion is inferred.',
                           'No finding does not mean PASS. Completeness and mapping are exporter assertions.',
                           'Wiz tenant identity is declared by the export, not authenticated by this offline importer.',
                           'Saved Azure findings are unchanged. Missing observations can reflect timing, filters or coverage.']}


def markdown(report):
    def cell(value):
        return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '\\|').replace('\n', ' ')
    lines = ['# Azure / Wiz evidence comparison', '',
             '**SYNTHETIC — NOT TENANT EVIDENCE**' if report['synthetic'] else 'Point-in-time comparison of operator-supplied evidence.', '',
             f"State: {report['state']}", f"Azure run: {report['source_run_id']}", f"Wiz import: {report['wiz_import_id']}",
             f"Comparison as of: {report['as_of']}", f"Freshness / maximum time skew: {report['max_age_hours']} / {report['max_skew_hours']} hours", '',
             '## Source provenance', '',
             f"Azure manifest SHA-256: {report['source_run_manifest_sha256']}",
             f"Wiz input SHA-256: {report['wiz_input_sha256']}",
             f"Wiz manifest SHA-256: {report['wiz_manifest_sha256']}",
             f"Azure inventory complete: {report['azure_inventory_complete']}",
             f"Saved Azure conclusion / coverage incomplete: {report['azure_assessment_conclusion']} / {report['azure_coverage_incomplete']}",
             f"Azure tenant / validation: {report['azure_tenant_id']} / {report['azure_tenant_validation']}",
             'Wiz source metadata:', '', '```json', encode(report['wiz_source']).decode().strip(), '```', '',
             '## Limitations', '']
    lines += ['- ' + item for item in report['limitations']]
    lines += ['', 'Overall gaps: ' + (', '.join(report['gaps']) or 'None in the comparison criteria.'), '',
              '## Resource observations', '', '| Resource | Presence | Saved Azure result | Azure observed | Wiz observed | Wiz finding IDs | Comparison gaps |',
              '| --- | --- | --- | --- | --- | --- | --- |']
    for row in report['resources']:
        values = [row['resource_id'], row['presence'], row['azure']['result'] if row['azure'] else 'No observation',
                  row['azure']['observed_at'] if row['azure'] else 'None', row['wiz']['observed_at'] if row['wiz'] else 'None',
                  ', '.join(f['finding_id'] for f in row['wiz_findings']) or 'None supplied; no PASS implied', ', '.join(row['gaps']) or 'None']
        lines.append('| ' + ' | '.join(cell(v) for v in values) + ' |')
    lines += ['', '## Wiz findings (source meaning retained)', '',
              '| ID / rule | Resource | Severity / status | Observed | Stale / within Azure time window |', '| --- | --- | --- | --- | --- |']
    for row in report['resources']:
        for f in row['wiz_findings']:
            values = [f['finding_id'] + ' / ' + f['rule_id'], f['resource_id'], f['severity'] + ' / ' + f['status'],
                      f['observed_at'], str(f['stale']) + ' / ' + str(f['within_time_window'])]
            lines.append('| ' + ' | '.join(cell(v) for v in values) + ' |')
    return '\n'.join(lines) + '\n'


def publish_comparison(store, run_id, wiz_import_id, *, as_of, max_age_hours, max_skew_hours):
    saved, imported = load_run(store, run_id), load_export(store, wiz_import_id)
    report = reconcile(saved, imported, as_of=as_of, max_age_hours=max_age_hours, max_skew_hours=max_skew_hours)
    comparison_id = 'c-' + uuid4().hex
    prefix = 'comparisons/' + comparison_id
    generation = {'comparison_id':comparison_id, 'generated_at':now(), 'source_run_id':run_id, 'wiz_import_id':wiz_import_id}
    report.update(generation)
    store.put_new(prefix + '/intent.json', encode(generation))
    stage = 'comparison'
    try:
        objects = {}
        for name, data in [('comparison.json', encode(report)), ('comparison.md', markdown(report).encode())]:
            stage = name
            key = prefix + '/' + name
            store.put_new(key, data)
            objects[name] = {'key':key, 'sha256':digest(data), 'bytes':len(data)}
        manifest = {'schema_version':'1.0', 'kind':'evidence_comparison', 'state':'complete', **generation,
                    'comparison_state':report['state'], 'source_run_manifest_sha256':saved['manifest_sha256'],
                    'wiz_manifest_sha256':imported['manifest_sha256'], 'objects':objects}
        stage = 'completion_manifest'
        store.put_new(prefix + '/manifest.json', encode(manifest))
        return manifest
    except Exception:
        _failure(store, prefix, stage)
        raise


def load_comparison(store, comparison_id):
    """Verify the saved comparison and its exact source archives; no fresh evaluation."""
    import json
    from .archive import identity
    prefix = 'comparisons/' + identity(comparison_id, 'c')
    try:
        store.read(prefix + '/failure.json')
    except FileNotFoundError:
        pass
    else:
        raise ValueError('failed_comparison_publication')
    manifest = json.loads(store.read(prefix + '/manifest.json'))
    require((manifest.get('schema_version'), manifest.get('kind'), manifest.get('state'), manifest.get('comparison_id')) ==
            ('1.0', 'evidence_comparison', 'complete', comparison_id))
    require(set(manifest['objects']) == {'comparison.json', 'comparison.md'})
    objects = {}
    for name, descriptor in manifest['objects'].items():
        require(descriptor['key'] == prefix + '/' + name)
        data = store.read(descriptor['key'])
        require(len(data) == descriptor['bytes'] and digest(data) == descriptor['sha256'])
        objects[name] = data
    report = json.loads(objects['comparison.json'])
    require(report['schema_version'] == '1.0' and report['kind'] == 'wiz_azure_reconciliation')
    for key in ('comparison_id', 'generated_at', 'source_run_id', 'wiz_import_id', 'source_run_manifest_sha256', 'wiz_manifest_sha256'):
        require(report[key] == manifest[key])
    require(report['state'] == manifest['comparison_state'])
    saved = load_run(store, manifest['source_run_id'])
    imported = load_export(store, manifest['wiz_import_id'])
    require(saved['manifest_sha256'] == manifest['source_run_manifest_sha256'])
    require(imported['manifest_sha256'] == manifest['wiz_manifest_sha256'])
    require(report['wiz_input_sha256'] == imported['manifest']['input_sha256'])
    return {'manifest':manifest, 'report':report, 'markdown':objects['comparison.md'].decode('utf-8')}
