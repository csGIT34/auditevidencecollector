"""Versioned runs and PDF publications. Completion manifests are written last."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
from uuid import uuid4

from . import __version__
from .catalog import RULES, RULE_VERSION
from .safety import now
from .snapshot import validate_snapshot
from .storage import ObjectStore
from .provenance import validate_provenance

ARCHIVE_VERSION = '1.1'
READABLE_ARCHIVE_VERSIONS = ('1.0','1.1')
RENDERER_VERSION = '1.3'
STATUSES = ('PASS', 'FAIL', 'UNKNOWN', 'ERROR', 'UNSUPPORTED', 'NOT_APPLICABLE')

CRITERIA = {
    'na': 'Narrow resource applicability rationale only: this construct is not a customer at-rest store. Other controls and dependent workloads remain unassessed.',
    'guarantee': 'Successful exact-type detail read plus the stated Microsoft service-enforced encryption guarantee. Provider keys accepted; optional CMK not required. Contradictory Storage enabled=false flags prevent PASS. Required children/destinations must be completely enumerated and positively assessed.',
    'tde': 'Explicit TDE state Enabled passes; Disabled fails; absent/transitional/unrecognized state is unknown. SQL master is narrowly not applicable because TDE is unsupported there; absence of user data in master is not verified.',
    'database_parent': 'Completely enumerate user databases and evaluate their TDE. Any failed child fails the parent; incomplete evidence is unknown; no assessable user database is narrowly not applicable; otherwise all assessable children must pass.',
    'kusto': 'enableDiskEncryption must explicitly be true to cover VM cache disks, alongside the documented backing-storage guarantee; false fails, missing is unknown.',
    'servicebus': 'Successful identity read must identify Premium SKU for the scoped service guarantee. Other or missing SKU is unknown.',
    'redis_enterprise': 'Successful identity read must identify an Enterprise_ or EnterpriseFlash_ SKU. Modern Managed Redis and other SKUs remain unknown under this saved rule.',
    'redis': 'Persistence flags cannot safely resolve every backing destination; this rule remains unknown pending separate destination evidence.',
    'linked': 'WorkspaceResourceId must resolve to a Microsoft.OperationalInsights/workspaces record that passes its scoped rule. Missing, wrong-type or nonpassing dependency is unknown.',
    'eventhub': 'Owning namespace must have a successful detail read. Capture must explicitly be disabled or enabled with a resolved, positively assessed Storage account. Missing parent/flag/destination or dependency gaps prevent PASS.',
    'workload': 'Evaluate declared children/storage dependencies. A failed dependency fails the workload; otherwise it remains unknown because runtime, temporary and external data paths are incomplete.',
    'unsupported': 'No reviewed rule exists for this exact type; retain inventory and mark unsupported, without inferring applicability or protection.',
}
COMMON_CRITERIA = ('A required read error prevents a positive result. Missing details, invalid relevant fields or incomplete/failed provisioning prevent PASS. '
                   'Dependent evidence must retain its own identity/scope. These criteria examine only scoped encryption evidence; no whole-control or period-wide effectiveness conclusion follows.')


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot_digest(snapshot):
    return digest(json.dumps(snapshot, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def identity(value, kind):
    if not isinstance(value, str) or not re.fullmatch(kind + r'-[0-9a-f]{32}', value):
        raise ValueError('Invalid archive identity')
    return value


def make_context():
    """Freeze explanatory rule criteria and program scope with each new run."""
    if {r.mode for r in RULES.values()} - set(CRITERIA):
        raise ValueError('Missing saved rule criterion')
    from .controls import CHECKS, VERSION, OBJECTIVES
    return {'configuration_objectives': OBJECTIVES, 'configuration_rules': {k:asdict(v) for k,v in CHECKS.items()}, 'configuration_rule_version': VERSION,
            'schema_version': ARCHIVE_VERSION, 'collector_version': __version__,
            'rule_version': RULE_VERSION, 'common_criteria': COMMON_CRITERIA,
            'criteria_by_mode': CRITERIA,
            'rule_catalog': {k: asdict(v) for k, v in RULES.items()},
            'program_scope': json.loads(Path(__file__).with_name('program_scope.json').read_text())}


def validate_pair(snapshot, report):
    """Structural consistency, not re-evaluation against current rules.

    Historical read intentionally does NOT call validate_snapshot (which uses
    current RULES) or assess. Hashes and this archive-v1 contract guard integrity.
    """
    if snapshot.get('schema_version') not in ('1.0','1.1') or report.get('schema_version') not in ('1.0','1.1'):
        raise ValueError('Unsupported saved evidence schema')
    if report['snapshot_sha256'] != snapshot_digest(snapshot):
        raise ValueError('Evidence/result mismatch')
    if (report['collection_started_at'], report['collection_completed_at'], report['mode'], report['inventory'], report['errors']) != (
            snapshot['started_at'], snapshot['completed_at'], snapshot['mode'], snapshot['inventory'], snapshot['errors']):
        raise ValueError('Collection identity mismatch')
    records = {r['id']: r for r in snapshot['resources']}
    results = report['results']
    if len(records) != len(snapshot['resources']) or len(results) != len(records) or {r['id'] for r in results} != set(records):
        raise ValueError('Saved population mismatch')
    for row in results:
        raw = records[row['id']]
        for field in ('type', 'name', 'subscription_id', 'resource_group', 'location', 'kind', 'sku', 'collected_at', 'collection_status', 'evidence', 'errors'):
            if row[field] != raw[field]:
                raise ValueError('Saved observation mismatch')
        if row['result'] not in STATUSES or row['rule_version'] != report['rule_version']:
            raise ValueError('Saved result mismatch')
    if 'configuration_assessment' in report:
        validate_configuration_pair(snapshot, report['configuration_assessment'])
    if 'overall_summary' in report:
        from .controls import overall_summary
        if report['overall_summary'] != overall_summary(report):
            raise ValueError('Saved overall summary mismatch')
    counts = {s: 0 for s in STATUSES}
    counts.update(Counter(r['result'] for r in results))
    if report['summary']['counts'] != counts or report['summary']['resource_count'] != len(results):
        raise ValueError('Saved summary mismatch')
    child_complete = all(c['complete'] for r in snapshot['resources'] for c in r['children'].values())
    incomplete = (not snapshot['inventory']['complete'] or not child_complete or not results or bool(snapshot['errors'])
                  or any(counts[s] for s in ('UNKNOWN', 'ERROR', 'UNSUPPORTED')) or any(r['gaps'] for r in results))
    conclusion = 'FAILURES_FOUND' if counts['FAIL'] else 'INCOMPLETE' if incomplete else 'SUPPORTED_SCOPE_SATISFIED'
    for field, value in [('coverage_incomplete', bool(incomplete)), ('conclusion', conclusion),
                         ('inventory_complete', snapshot['inventory']['complete']), ('child_collections_complete', child_complete),
                         ('collection_error_count', len(snapshot['errors']))]:
        if report['summary'][field] != value:
            raise ValueError('Saved coverage summary mismatch')


def _object(key, data):
    return {'key': key, 'sha256': digest(data), 'bytes': len(data)}


def _failure(store, prefix, stage):
    try:
        store.put_new(prefix + '/failure.json', encode({'schema_version': ARCHIVE_VERSION, 'state': 'failed', 'stage': stage, 'recorded_at': now()}))
    except (OSError, ValueError):
        pass  # An intent without a final manifest still indicates incomplete publication.


def save_run(store: ObjectStore, snapshot, report, *, provenance=None):
    validate_snapshot(snapshot)
    validate_pair(snapshot, report)
    context = make_context()
    if report.get("schema_version") != "1.1" or "overall_summary" not in report or "configuration_assessment" not in report:
        raise ValueError("New archives require the full assessment contract")
    validate_configuration_population(snapshot,report,context)
    if provenance is not None:
        context['execution_provenance'] = validate_provenance(provenance)
    if report['tool_version'] != context['collector_version'] or report['rule_version'] != context['rule_version']:
        raise ValueError('Cannot archive old results with current context')
    run_id = 'r-' + uuid4().hex
    prefix = 'runs/' + run_id
    created_at = now()
    store.put_new(prefix + '/intent.json', encode({'schema_version': ARCHIVE_VERSION, 'run_id': run_id, 'archive_started_at': created_at}))
    stage = 'evidence'
    try:
        objects = {}
        for name, value in [('snapshot', snapshot), ('assessment', report), ('context', context)]:
            stage = name
            key = prefix + '/' + name + '.json'
            data = encode(value)
            store.put_new(key, data)
            objects[name] = _object(key, data)
        manifest = {'schema_version': ARCHIVE_VERSION, 'kind': 'collection_run', 'state': 'complete', 'run_id': run_id,
                    'archive_started_at': created_at, 'archive_completed_at': now(),
                    'collection_started_at': snapshot['started_at'], 'collection_completed_at': snapshot['completed_at'],
                    'assessment_generated_at': report['generated_at'], 'mode': snapshot['mode'],
                    'scope': snapshot['inventory'], 'collector_version': report['tool_version'], 'rule_version': report['rule_version'],
                    'snapshot_schema_version': snapshot['schema_version'], 'assessment_schema_version': report['schema_version'],
                    'assessment_conclusion': report.get('overall_summary',report['summary'])['conclusion'], 'coverage_incomplete': report.get('overall_summary',report['summary'])['coverage_incomplete'],
                    'objects': objects}
        stage = 'completion_manifest'
        store.put_new(prefix + '/manifest.json', encode(manifest))
        return manifest
    except Exception:
        _failure(store, prefix, stage)
        raise


def load_run(store: ObjectStore, run_id):
    prefix = 'runs/' + identity(run_id, 'r')
    try:
        store.read(prefix + '/failure.json')
    except FileNotFoundError:
        pass
    else:
        raise ValueError('Run publication recorded a failure')
    manifest_bytes = store.read(prefix + '/manifest.json')
    manifest = json.loads(manifest_bytes)
    if manifest.get('schema_version') not in READABLE_ARCHIVE_VERSIONS or (manifest.get('kind'), manifest.get('state'), manifest.get('run_id')) != ('collection_run', 'complete', run_id):
        raise ValueError('Invalid or incomplete run manifest')
    if set(manifest['objects']) != {'snapshot', 'assessment', 'context'}:
        raise ValueError('Incomplete object manifest')
    saved = {}
    for name, descriptor in manifest['objects'].items():
        if descriptor['key'] != prefix + '/' + name + '.json':
            raise ValueError('Manifest object escaped run')
        data = store.read(descriptor['key'])
        if len(data) != descriptor['bytes'] or digest(data) != descriptor['sha256']:
            raise ValueError('Object integrity mismatch')
        saved[name] = json.loads(data)
    validate_pair(saved['snapshot'], saved['assessment'])
    if manifest['schema_version']=='1.1':
        if saved['assessment'].get('schema_version')!='1.1':raise ValueError('Invalid new assessment version')
        validate_configuration_population(saved['snapshot'],saved['assessment'],saved['context'])
    elif saved['snapshot']['schema_version']!='1.0' or saved['assessment']['schema_version']!='1.0':
        raise ValueError('Invalid legacy archive version')
    if 'execution_provenance' in saved['context']:
        validate_provenance(saved['context']['execution_provenance'])
    if (saved['context']['schema_version'] != manifest['schema_version'] or saved['context']['rule_version'] != saved['assessment']['rule_version']
            or saved['context']['collector_version'] != saved['assessment']['tool_version']):
        raise ValueError('Saved context mismatch')
    for field, value in [('snapshot_schema_version',saved['snapshot']['schema_version']), ('assessment_schema_version',saved['assessment']['schema_version']), ('collection_started_at', saved['snapshot']['started_at']), ('collection_completed_at', saved['snapshot']['completed_at']),
                         ('collector_version', saved['assessment']['tool_version']), ('rule_version', saved['assessment']['rule_version']),
                         ('scope', saved['snapshot']['inventory']), ('mode', saved['snapshot']['mode']),
                         ('assessment_generated_at', saved['assessment']['generated_at']),
                         ('assessment_conclusion', saved['assessment'].get('overall_summary',saved['assessment']['summary'])['conclusion']), ('coverage_incomplete', saved['assessment'].get('overall_summary',saved['assessment']['summary'])['coverage_incomplete'])]:
        if manifest[field] != value:
            raise ValueError('Manifest metadata mismatch')
    return {'manifest': manifest, 'manifest_sha256': digest(manifest_bytes), **saved}


def list_runs(store: ObjectStore):
    runs = []
    keys = set(store.keys('runs/'))
    ids = sorted({k.split('/')[1] for k in keys if len(k.split('/')) == 3 and k.endswith('/intent.json')})
    for run_id in ids:
        identity(run_id, 'r')
        prefix = 'runs/' + run_id
        if prefix + '/failure.json' in keys:
            runs.append({'run_id': run_id, 'archive_state': 'failed'})
        elif prefix + '/manifest.json' in keys:
            try:
                manifest = load_run(store, run_id)['manifest']
                runs.append({'run_id': run_id, 'archive_state': 'complete', 'collected_at': manifest['collection_completed_at'],
                             'assessment_conclusion': manifest['assessment_conclusion'], 'coverage_incomplete': manifest['coverage_incomplete']})
            except (OSError, ValueError, KeyError, TypeError):
                runs.append({'run_id': run_id, 'archive_state': 'corrupt_or_incomplete'})
        else:
            runs.append({'run_id': run_id, 'archive_state': 'failed' if prefix + '/failure.json' in keys else 'incomplete'})
    return runs


def publish_pdf(store: ObjectStore, run_id, *, provenance=None, deadline=None):
    if deadline:
        deadline.check()
    saved = load_run(store, run_id)
    from .pdf_report import render_pdf, renderer_dependencies
    dependencies = renderer_dependencies()  # Fail clearly before reserving a report if dependency is absent.
    report_id = 'p-' + uuid4().hex
    prefix = 'reports/' + run_id + '/' + report_id
    generated_at = now()
    generation = {'report_id': report_id, 'run_id': run_id, 'generated_at': generated_at,
                  'renderer_version': RENDERER_VERSION, 'generator_tool_version': __version__, 'dependencies': dependencies,
                  'source_manifest_sha256': saved['manifest_sha256']}
    if provenance is not None:
        generation['execution_provenance'] = validate_provenance(provenance)
    store.put_new(prefix + '/intent.json', encode({'schema_version': ARCHIVE_VERSION, **generation}))
    stage = 'render_pdf'
    try:
        if deadline:
            deadline.check()
        data = render_pdf(saved, generation)
        if deadline:
            deadline.check()
        if not data.startswith(b'%PDF-') or not data.rstrip().endswith(b'%%EOF'):
            raise ValueError('Invalid rendered PDF')
        stage = 'pdf_object'
        key = prefix + '/report.pdf'
        store.put_new(key, data)
        manifest = {'schema_version': ARCHIVE_VERSION, 'kind': 'pdf_report', 'state': 'complete', **generation,
                    'archive_completed_at': now(), 'source_objects': saved['manifest']['objects'], 'pdf': _object(key, data)}
        stage = 'completion_manifest'
        store.put_new(prefix + '/manifest.json', encode(manifest))
        return manifest
    except Exception:
        _failure(store, prefix, stage)
        raise RuntimeError('PDF_PUBLICATION_FAILED') from None


def validate_configuration_pair(snapshot, assessment):
    records = {r['id']:r for r in snapshot['resources'] + snapshot.get('identity_evidence',{}).get('resources',[])}
    if assessment.get('schema_version') != '1.0' or not isinstance(assessment.get('results'), list):
        raise ValueError('Invalid saved configuration assessment')
    seen = set()
    policy = assessment.get('policy')
    from .controls import criterion_for
    for row in assessment['results']:
        key = (row['resource_id'], row['check_id'])
        if key in seen or row['resource_id'] not in records or row['result'] not in ('PASS','FAIL','UNKNOWN','ERROR'):
            raise ValueError('Invalid saved configuration population')
        seen.add(key)
        raw = records[row['resource_id']]
        if row['observed_at'] != raw['collected_at'] or row['observation'] != raw.get('configuration',{}).get(row['check_id'], {'state':'missing'}):
            raise ValueError('Saved configuration observation mismatch')
        if row['criterion'] != criterion_for(policy,row['resource_id'],row['check_id']):
            raise ValueError('Saved configuration criterion mismatch')
        if row['result'] in ('PASS','FAIL') and (not policy or policy['status'] != 'approved' or not row['criterion'] or row['observation']['state'] != 'observed'):
            raise ValueError('Configuration conclusion without evidence/criteria')
    counts = {s:0 for s in ('PASS','FAIL','UNKNOWN','ERROR')}
    counts.update(Counter(r['result'] for r in assessment['results']))
    expected = 'FAILURES_FOUND' if counts['FAIL'] else 'INCOMPLETE' if not seen or counts['UNKNOWN'] or counts['ERROR'] or not snapshot.get('identity_evidence',{}).get('complete',True) else 'SELECTED_CONFIGURATION_CRITERIA_SATISFIED'
    if assessment['summary'] != {'check_count':len(seen), 'counts':counts, 'conclusion':expected}:
        raise ValueError('Saved configuration summary mismatch')


def validate_configuration_population(snapshot, report, context):
    """Check frozen registry linkage, never re-run a saved predicate."""
    assessment=report['configuration_assessment']
    if assessment['rule_version']!=context['configuration_rule_version']:
        raise ValueError('Saved configuration rule version mismatch')
    records=snapshot['resources']+snapshot.get('identity_evidence',{}).get('resources',[])
    rules=context['configuration_rules']
    expected={(r['id'],cid) for r in records for cid,c in rules.items() if c['resource_type'].lower()==r['type'].lower()}
    rows=assessment['results']
    if {(r['resource_id'],r['check_id']) for r in rows}!=expected or len(rows)!=len(expected):
        raise ValueError('Incomplete configuration assessment population')
    for row in rows:
        rule=rules[row['check_id']]
        for field,key in [('catalog_ref','catalog_ref'),('source','source'),('api_version','api'),('property','path'),('title','title')]:
            if row[field]!=rule[key]:raise ValueError('Saved predicate metadata mismatch')
        if row['control_refs']!=context['configuration_objectives']['checks'][row['catalog_ref']]['controls']:
            raise ValueError('Saved objective mapping mismatch')
