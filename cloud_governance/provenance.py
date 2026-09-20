"""Additive, versioned archive context; snapshot v1 remains unchanged."""
import re
from .safety import subscription_id
from .storage import parts


def validate_provenance(value):
    if not isinstance(value, dict) or set(value) - {'invocation_id'} != {'schema_version', 'environment', 'authentication', 'tenant_id', 'identity_client_id', 'tenant_validation', 'storage'}:
        raise ValueError('invalid_provenance')
    if 'invocation_id' in value and not re.fullmatch(r'[0-9a-f]{32}', value['invocation_id']):
        raise ValueError('invalid_provenance')
    if value['schema_version'] != '1.0' or value['environment'] not in ('azure_functions', 'local'):
        raise ValueError('invalid_provenance')
    if value['authentication'] not in ('managed_identity', 'azure_cli', 'offline_fixture') or value['tenant_validation'] not in ('arm_subscription_metadata', 'deployment_configuration', 'not_verified'):
        raise ValueError('invalid_provenance')
    for key in ('tenant_id', 'identity_client_id'):
        if value[key] is not None and not subscription_id(value[key]):
            raise ValueError('invalid_provenance')
    storage = value['storage']
    if not isinstance(storage, dict) or storage.get('retention_policy') != 'not_verified':
        raise ValueError('invalid_provenance')
    if storage.get('backend') == 'local':
        if set(storage) != {'backend', 'retention_policy'}:
            raise ValueError('invalid_provenance')
    elif storage.get('backend') == 'azure_blob':
        if set(storage) != {'backend', 'retention_policy', 'account_url', 'container', 'prefix'}:
            raise ValueError('invalid_provenance')
        if not re.fullmatch(r'https://[a-z0-9]{3,24}\.blob\.core\.windows\.net', storage['account_url']):
            raise ValueError('invalid_provenance')
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,61}[a-z0-9]', storage['container']) or '--' in storage['container']:
            raise ValueError('invalid_provenance')
        if storage['prefix']:
            parts(storage['prefix'])
    else:
        raise ValueError('invalid_provenance')
    return value
