"""Customer-managed key references, projected to bounded facts.

Each service declares its key in a different shape. This module reads the exact
reviewed fields per predicate and emits the same three facts every time: whether a
customer-managed key is configured, whether its reference pins a version, and which
identity type reaches the vault.

A key identifier is not a secret, but it names a vault and a key. Nothing here retains
the URI, the vault host, the key name or the version value; only the derived facts are
projected, so a report cannot become a map of an organization's key material.
"""
from urllib.parse import urlsplit

from .safety import MISSING, get

IDENTITIES = ('user_assigned', 'system_assigned', 'unspecified')

# Exact reviewed field shapes per predicate. A service is added only after its pinned
# ARM template reference is read; no shape is inferred from a sibling service.
SHAPES = {
    'ST-cmk-key': {'source': 'encryption.keySource', 'customer_managed': 'Microsoft.Keyvault',
                   'source_values': ('microsoft.storage', 'microsoft.keyvault'),
                   'version': 'encryption.keyvaultproperties.keyversion',
                   'user_assigned': 'encryption.identity.userAssignedIdentity'},
    'ACR-cmk-key': {'source': 'encryption.status', 'customer_managed': 'enabled',
                    'source_values': ('enabled', 'disabled'),
                    'key_uri': 'encryption.keyVaultProperties.keyIdentifier',
                    'client_identity': 'encryption.keyVaultProperties.identity'},
    'APPC-cmk-key': {'key_uri': 'encryption.keyVaultProperties.keyIdentifier',
                     'client_identity': 'encryption.keyVaultProperties.identityClientId'},
    'REDIS-cmk-key': {'key_uri': 'encryption.customerManagedKeyEncryption.keyEncryptionKeyUrl',
                      'identity_type': 'encryption.customerManagedKeyEncryption.keyEncryptionKeyIdentity.identityType',
                      'user_assigned': 'encryption.customerManagedKeyEncryption.keyEncryptionKeyIdentity.'
                                       'userAssignedIdentityResourceId'},
}


def _versioned(uri):
    """A versioned key reference ends in /keys/<name>/<version>; a versionless one does not.

    Returns None when the reference cannot be parsed, so an unreadable value never
    becomes a rotation claim.
    """
    if not isinstance(uri, str) or len(uri) > 2048:
        return None
    try:
        parts = urlsplit(uri)
    except ValueError:
        return None
    if parts.scheme != 'https' or not parts.hostname:
        return None
    segments = [segment for segment in parts.path.split('/') if segment]
    if len(segments) < 2 or segments[0] != 'keys':
        return None
    return len(segments) >= 3


def project(properties, shape):
    """Bounded customer-managed key facts, or None when the shape is unreadable."""
    source = get(properties, shape['source'], MISSING) if 'source' in shape else MISSING
    uri = get(properties, shape['key_uri'], MISSING) if 'key_uri' in shape else MISSING
    if 'source' in shape:
        # An absent selector is the documented provider-managed default, not an unreadable read.
        if source is MISSING:
            configured = False
        elif not isinstance(source, str) or source.lower() not in shape['source_values']:
            # A selector outside its documented values is unreadable, not a different state.
            return None
        else:
            configured = source.lower() == shape['customer_managed'].lower()
    elif uri is MISSING or uri is None:
        configured = False
    elif not isinstance(uri, str):
        # A present but malformed key identifier is unreadable, never "no customer key".
        return None
    else:
        configured = bool(uri)
    if not configured:
        return {'configured': False, 'version_pinned': False, 'identity': 'unspecified'}

    if 'version' in shape:
        version = get(properties, shape['version'], MISSING)
        if version is not MISSING and not isinstance(version, str):
            return None
        pinned = bool(version) if version is not MISSING else False
    else:
        pinned = _versioned(uri)
        if pinned is None:
            return None

    identity = 'unspecified'
    if shape.get('user_assigned') and get(properties, shape['user_assigned'], MISSING) not in (MISSING, None, ''):
        identity = 'user_assigned'
    elif shape.get('client_identity') and get(properties, shape['client_identity'], MISSING) not in (MISSING, None, ''):
        identity = 'user_assigned'
    elif shape.get('identity_type'):
        declared = get(properties, shape['identity_type'], MISSING)
        if declared == 'userAssignedIdentity':
            identity = 'user_assigned'
        elif declared == 'systemAssignedIdentity':
            identity = 'system_assigned'
    return {'configured': True, 'version_pinned': pinned, 'identity': identity}


def valid(value):
    return (isinstance(value, dict) and set(value) == {'configured', 'version_pinned', 'identity'}
            and type(value['configured']) is bool and type(value['version_pinned']) is bool
            and value['identity'] in IDENTITIES
            and (value['configured'] or (not value['version_pinned'] and value['identity'] == 'unspecified')))
