"""Optional lab-only function. Excluded from the production source allowlist."""
from datetime import datetime, timezone
import json
import os
from uuid import uuid4
from azure_at_rest.azure_adapters import verify_tenant
from azure_at_rest.hosting import Settings, resources
from azure_at_rest.workflow import Deadline


def probe(env, factory=resources):
    if env.get('CG_LAB_PROBE_ENABLED') != 'true':
        raise ValueError('lab_probe_disabled')
    expires = datetime.fromisoformat(env['CG_LAB_EXPIRES_AT'])
    if expires.tzinfo is None or datetime.now(timezone.utc) >= expires:
        raise ValueError('lab_probe_expired')
    settings = Settings.parse(env)
    if settings.development or not settings.resource_group or not settings.resource_group.startswith('rg-'):
        raise ValueError('explicit_hosted_lab_scope_required')
    key = 'probes/' + uuid4().hex + '/create-only.bin'
    data = b'Cloud governance synthetic Blob conditional-create probe.\n'
    with factory(settings, Deadline(30), 'collect') as (store, transport):
        verify_tenant(transport, settings.subscriptions, settings.tenant)
        store.put_new(key, data)
        try:
            store.put_new(key, data)
        except FileExistsError:
            pass
        else:
            raise RuntimeError('conditional_create_not_enforced')
        if store.read(key) != data or key not in store.keys(key.rsplit('/', 1)[0] + '/'):
            raise RuntimeError('probe_bytes_or_listing_mismatch')
    return {'state': 'complete', 'tenant_preflight': 'passed', 'blob_create_read_list': 'passed',
            'same_key_conflict': 'passed', 'probe_key': key}


def register(app):
    import azure.functions as func
    @app.function_name(name='LabProbe')
    @app.route(route='lab-probe', methods=['POST'], auth_level=func.AuthLevel.FUNCTION)
    def handler(req: func.HttpRequest) -> func.HttpResponse:
        try:
            if req.get_body() not in (b'', b'{}'):
                raise ValueError('empty_body_required')
            result = probe(os.environ)
        except Exception:
            return func.HttpResponse('{"state":"failed","code":"lab_probe_failed_or_disabled"}', status_code=503, mimetype='application/json')
        return func.HttpResponse(json.dumps(result), status_code=201, mimetype='application/json', headers={'Cache-Control':'no-store'})
