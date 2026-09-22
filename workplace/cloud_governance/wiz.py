"""Offline Wiz evidence contract. No native API assumptions, tokens or network calls."""
from datetime import datetime
import json
import re
from uuid import uuid4

from .archive import digest, encode, identity
from .safety import now, resource_group_name, resource_id, subscription_id

SCHEMA_VERSION = '1.0'
MAX_INPUT_BYTES = 20 * 1024 * 1024
STATUSES = {'OPEN', 'IN_PROGRESS', 'RESOLVED', 'REJECTED', 'UNKNOWN'}
SEVERITIES = {'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFORMATIONAL', 'UNKNOWN'}


def require(condition):
    if not condition:
        raise ValueError('invalid_wiz_evidence')


def timestamp(value):
    require(isinstance(value, str) and len(value) <= 64)
    require(re.fullmatch(r'\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})', value) is not None)
    stamp = datetime.fromisoformat(value.replace('z', '+00:00'))
    require(stamp.tzinfo is not None)
    return stamp


def token(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', value) is not None


def fields(value, names):
    require(isinstance(value, dict) and set(value) == set(names.split()))


def decode(data):
    require(isinstance(data, bytes) and len(data) <= MAX_INPUT_BYTES)
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value)
            value[key] = item
        return value
    def invalid_constant(_):
        raise ValueError('invalid_wiz_evidence')
    return json.loads(data, object_pairs_hook=unique, parse_constant=invalid_constant)


def validate_export(document):
    """Strict allowlist: native Wiz exports must be mapped to this contract first."""
    if isinstance(document, dict) and document.get('schema_version') == '2.0':
        from .wiz_observations import validate
        return validate(document)
    fields(document, 'schema_version kind source resources findings')
    require(document['schema_version'] == SCHEMA_VERSION and document['kind'] == 'wiz_evidence')
    source = document['source']
    fields(source, 'system mode export_id exported_at tenant_id mapping_version scope inventory_complete findings_complete')
    require(source['system'] == 'wiz' and source['mode'] in {'synthetic', 'operator_export'})
    require(token(source['export_id']) and source['mapping_version'] == '1.0')
    require(subscription_id(source['tenant_id']) == source['tenant_id'])
    exported = timestamp(source['exported_at'])
    require(type(source['inventory_complete']) is bool and type(source['findings_complete']) is bool)
    scope = source['scope']
    fields(scope, 'subscription_ids resource_group')
    subscriptions = scope['subscription_ids']
    require(isinstance(subscriptions, list) and 1 <= len(subscriptions) <= 1000)
    require(all(isinstance(s, str) and subscription_id(s) == s for s in subscriptions))
    require(len(set(subscriptions)) == len(subscriptions))
    require(scope['resource_group'] is None or (len(subscriptions) == 1 and resource_group_name(scope['resource_group']) is not None))
    require(isinstance(document['resources'], list) and len(document['resources']) <= 100000)
    require(isinstance(document['findings'], list) and len(document['findings']) <= 100000)
    resources, wiz_ids, findings = set(), set(), set()
    def scoped(rid):
        require(resource_id(rid) is not None)
        bits = rid.split('/')
        require(subscription_id(bits[2]) in subscriptions)
        if scope['resource_group'] is not None:
            require(bits[3].lower() == 'resourcegroups' and bits[4].lower() == scope['resource_group'].lower())
    for row in document['resources']:
        fields(row, 'wiz_id resource_id observed_at')
        scoped(row['resource_id'])
        require(token(row['wiz_id']) and row['wiz_id'] not in wiz_ids)
        key = row['resource_id'].lower()
        require(key not in resources and timestamp(row['observed_at']) <= exported)
        resources.add(key)
        wiz_ids.add(row['wiz_id'])
    for row in document['findings']:
        fields(row, 'finding_id resource_id rule_id severity status observed_at')
        scoped(row['resource_id'])
        require(row['resource_id'].lower() in resources)
        require(token(row['finding_id']) and row['finding_id'] not in findings and token(row['rule_id']))
        require(row['severity'] in SEVERITIES and row['status'] in STATUSES)
        require(timestamp(row['observed_at']) <= exported)
        findings.add(row['finding_id'])
    return document


def _failure(store, prefix, stage):
    try:
        store.put_new(prefix + '/failure.json', encode({'state':'failed', 'stage':stage, 'recorded_at':now()}))
    except Exception:
        pass


def import_export(store, data):
    document = validate_export(decode(data))  # Validate everything before first write.
    export_id = 'w-' + uuid4().hex
    prefix = 'external/wiz/' + export_id
    imported_at = now()
    manifest = {'schema_version':SCHEMA_VERSION, 'kind':'wiz_import', 'state':'complete',
                'wiz_import_id':export_id, 'imported_at':imported_at,
                'source_mode':document['source']['mode'], 'input_sha256':digest(data),
                'input_bytes':len(data), 'object':{'key':prefix + '/export.json', 'sha256':digest(data), 'bytes':len(data)}}
    store.put_new(prefix + '/intent.json', encode({'wiz_import_id':export_id, 'imported_at':imported_at}))
    stage = 'export'
    try:
        store.put_new(prefix + '/export.json', data)  # Exact accepted bytes, including whitespace.
        stage = 'completion_manifest'
        store.put_new(prefix + '/manifest.json', encode(manifest))
    except Exception:
        _failure(store, prefix, stage)
        raise
    return manifest


def load_export(store, export_id):
    prefix = 'external/wiz/' + identity(export_id, 'w')
    try:
        store.read(prefix + '/failure.json')
    except FileNotFoundError:
        pass
    else:
        raise ValueError('failed_wiz_publication')
    raw = store.read(prefix + '/manifest.json')
    manifest = decode(raw)
    require((manifest.get('schema_version'), manifest.get('kind'), manifest.get('state'), manifest.get('wiz_import_id')) ==
            (SCHEMA_VERSION, 'wiz_import', 'complete', export_id))
    descriptor = manifest['object']
    require(descriptor['key'] == prefix + '/export.json')
    data = store.read(descriptor['key'])
    require(len(data) == descriptor['bytes'] == manifest['input_bytes'])
    require(digest(data) == descriptor['sha256'] == manifest['input_sha256'])
    document = validate_export(decode(data))
    require(manifest['source_mode'] == document['source']['mode'])
    timestamp(manifest['imported_at'])
    return {'manifest':manifest, 'manifest_sha256':digest(raw), 'document':document}
