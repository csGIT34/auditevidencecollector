"""Host-neutral Functions handlers with explicit configuration and safe outcomes."""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
import os
import re
from threading import Lock
from uuid import uuid4
from .archive import identity, publish_pdf
from .azure_adapters import BlobStore, BudgetArmTransport, account_url, container_name, token_credential, verify_tenant
from .safety import subscription_id, resource_group_name
from .storage import parts
from .workflow import Deadline, collect_run

LOG = logging.getLogger('cloud_governance')
LOCKS = {'collect': Lock(), 'report': Lock()}


class ConfigurationError(ValueError):
    pass


class OperationBusy(RuntimeError):
    pass


def enabled(env, operation):
    value = env.get('CG_' + operation.upper() + '_ENABLED', 'false')
    if value not in ('true', 'false'):
        raise ConfigurationError('invalid_enabled_setting')
    return value == 'true'


def schedule(env):
    value = env.get('CG_COLLECTION_SCHEDULE', '')
    if enabled(env, 'collection') and not value:
        raise ConfigurationError('collection_schedule_required')
    if value:
        # Restrict to six numeric NCRONTAB fields; host validates calendar semantics.
        fields = value.split()
        if len(fields) != 6 or any(not re.fullmatch(r'[0-9*/,-]+', f) for f in fields):
            raise ConfigurationError('invalid_collection_schedule')
        try:
            for field, low, high in zip(fields, (0,0,0,1,1,0), (59,59,23,31,12,6)):
                for expression in field.split(','):
                    base, *step = expression.split('/')
                    if len(step) > 1 or (step and not 1 <= int(step[0]) <= high + 1):
                        raise ValueError()
                    if base != '*':
                        bounds = [int(v) for v in base.split('-')]
                        if len(bounds) not in (1,2) or any(not low <= v <= high for v in bounds) or bounds != sorted(bounds):
                            raise ValueError()
        except ValueError:
            raise ConfigurationError('invalid_collection_schedule') from None
    return value


@dataclass(frozen=True)
class Settings:
    tenant: str
    client_id: str | None
    subscriptions: tuple[str, ...]
    blob_url: str
    container: str
    prefix: str
    development: bool
    collection_budget: int
    report_budget: int
    arm_retries: int
    blob_retries: int
    max_pages: int
    lock_wait: int
    resource_group: str | None

    @classmethod
    def parse(cls, env):
        try:
            auth = env.get('CG_AUTH_MODE', 'managed_identity')
            if auth not in ('managed_identity', 'azure_cli'):
                raise ValueError()
            development = auth == 'azure_cli'
            tenant, client = env['CG_TENANT_ID'], env.get('CG_MANAGED_IDENTITY_CLIENT_ID') or None
            if not subscription_id(tenant) or (not development and not subscription_id(client)):
                raise ValueError()
            subscriptions = tuple(dict.fromkeys(x.strip().lower() for x in env['CG_SUBSCRIPTION_IDS'].split(',')))
            if not subscriptions or any(not subscription_id(x) for x in subscriptions):
                raise ValueError()
            resource_group = env.get('CG_RESOURCE_GROUP') or None
            if resource_group is not None and (not resource_group_name(resource_group) or len(subscriptions) != 1):
                raise ValueError()
            url = account_url(env['CG_EVIDENCE_ACCOUNT_URL'])
            container = container_name(env['CG_EVIDENCE_CONTAINER'])
            prefix = env.get('CG_EVIDENCE_PREFIX', '')
            if prefix:
                parts(prefix)
            if development and (env.get('CG_LOCAL_DEVELOPMENT') != 'true' or env.get('WEBSITE_HOSTNAME') or env.get('WEBSITE_INSTANCE_ID')):
                raise ValueError()
            # Explicitly named host storage account must differ from evidence storage.
            runtime = env['CG_RUNTIME_STORAGE_ACCOUNT']
            if not re.fullmatch(r'[a-z0-9]{3,24}', runtime) or url == f'https://{runtime}.blob.core.windows.net':
                raise ValueError()
            runtime_url = env.get('AzureWebJobsStorage__blobServiceUri', '').rstrip('/')
            runtime_name = env.get('AzureWebJobsStorage__accountName')
            if runtime_url and runtime_url != f'https://{runtime}.blob.core.windows.net':
                raise ValueError()
            if runtime_name and runtime_name != runtime:
                raise ValueError()
            if not development and (env.get('AzureWebJobsStorage') or not (runtime_url or runtime_name)):
                raise ValueError()
            def number(key, default, low, high):
                value = int(env.get(key, str(default)))
                if not low <= value <= high:
                    raise ValueError()
                return value
            return cls(tenant.lower(), client.lower() if client else None, subscriptions, url, container, prefix, development,
                       number('CG_COLLECTION_BUDGET_SECONDS', 480, 30, 540), number('CG_REPORT_BUDGET_SECONDS', 180, 10, 180),
                       number('CG_ARM_RETRIES', 2, 0, 3), number('CG_BLOB_RETRIES', 2, 0, 3),
                       number('CG_MAX_PAGES', 1000, 1, 10000), number('CG_LOCK_WAIT_SECONDS', 0, 0, 30), resource_group)
        except (KeyError, TypeError, ValueError):
            raise ConfigurationError('invalid_host_configuration') from None

    def provenance(self, operation, invocation_id):
        return {'schema_version': '1.0', 'invocation_id': invocation_id, 'environment': 'local' if self.development else 'azure_functions',
                'authentication': 'azure_cli' if self.development else 'managed_identity', 'tenant_id': self.tenant,
                'identity_client_id': None if self.development else self.client_id,
                'tenant_validation': 'arm_subscription_metadata' if operation == 'collect' else 'deployment_configuration',
                'storage': {'backend': 'azure_blob', 'retention_policy': 'not_verified', 'account_url': self.blob_url,
                            'container': self.container, 'prefix': self.prefix}}


@contextmanager
def resources(settings, deadline, operation):
    credential = token_credential(settings.client_id, settings.tenant, development=settings.development)
    store = None
    try:
        store = BlobStore(settings.blob_url, settings.container, credential, settings.prefix,
                          retries=settings.blob_retries, deadline=deadline)
        transport = BudgetArmTransport(credential, deadline, settings.arm_retries) if operation == 'collect' else None
        yield store, transport
    finally:
        if store:
            store.close()
        credential.close()


def execute(operation, *, run_id=None, env=None, factory=resources):
    """Returns safe metadata; reports pre-archive failures without exception payloads."""
    env = os.environ if env is None else env
    invocation_id = uuid4().hex
    stage = 'configuration'
    locked = False
    LOG.info(json.dumps({'operation': operation if operation in LOCKS else 'invalid', 'state': 'started', 'invocation_id': invocation_id}))
    try:
        if operation not in ('collect', 'report'):
            raise ConfigurationError('invalid_operation')
        setting = 'collection' if operation == 'collect' else 'report'
        if not enabled(env, setting):
            return {'operation': operation, 'state': 'disabled', 'invocation_id': invocation_id}
        if operation == 'collect':
            schedule(env)
        else:
            identity(run_id, 'r')
        if env.get('CG_EXECUTION_EXPIRES_AT'):
            expires = datetime.fromisoformat(env['CG_EXECUTION_EXPIRES_AT'])
            if expires.tzinfo is None or datetime.now(timezone.utc) >= expires:
                raise ConfigurationError('execution_window_expired')
        settings = Settings.parse(env)
        deadline = Deadline(settings.collection_budget if operation == 'collect' else settings.report_budget)
        stage = 'overlap_guard'
        locked = LOCKS[operation].acquire(timeout=settings.lock_wait)
        if not locked:
            raise OperationBusy('operation_busy')
        stage = 'authentication_and_storage'
        with factory(settings, deadline, operation) as (store, transport):
            if operation == 'collect':
                stage = 'tenant_preflight'
                verify_tenant(transport, settings.subscriptions, settings.tenant)
                stage = 'collection_assessment_archive'
                result = collect_run(store, transport, settings.subscriptions, mode='azure_live', max_pages=settings.max_pages,
                                     provenance=settings.provenance(operation, invocation_id), deadline=deadline, resource_group=settings.resource_group)
            else:
                stage = 'saved_run_pdf_archive'
                manifest = publish_pdf(store, run_id, provenance=settings.provenance(operation, invocation_id), deadline=deadline)
                result = {key: manifest[key] for key in ('run_id', 'report_id', 'generated_at')}
                result['pdf_key'] = manifest['pdf']['key']
                result['archive_state'] = 'complete'
        result.update(operation=operation, state='complete', invocation_id=invocation_id)
        LOG.info(json.dumps(result, sort_keys=True))
        return result
    except Exception as exc:
        result = {'operation': operation if operation in LOCKS else 'invalid', 'state': 'failed',
                  'invocation_id': invocation_id, 'stage': stage,
                  'code': 'operation_busy' if isinstance(exc, OperationBusy) else 'operation_failed'}
        LOG.error(json.dumps(result, sort_keys=True))  # No raw exception, request or SDK data.
        raise RuntimeError(json.dumps(result, sort_keys=True)) from None
    finally:
        if locked:
            LOCKS[operation].release()
