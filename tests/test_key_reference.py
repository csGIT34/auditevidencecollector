import json
import unittest
from azure_at_rest.controls import CHECKS, project
from azure_at_rest.key_reference import SHAPES, project as project_key, valid

VAULT = 'https://example-vault.vault.azure.net'
VERSIONED = VAULT + '/keys/audit-key/8f1d2c3b4a5e6f70819a2b3c4d5e6f70'
VERSIONLESS = VAULT + '/keys/audit-key'
IDENTITY = '/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/audit-demo/providers/Microsoft.ManagedIdentity/userAssignedIdentities/collector'


def shaped(properties, check_id, *, configured=True, pinned=True, identity=True):
    """Write a reviewed customer-managed key shape into a fixture resource's properties."""
    shape = SHAPES[check_id]

    def setpath(path, value):
        target = properties
        for part in path.split('.')[:-1]:
            target = target.setdefault(part, {})
        target[path.split('.')[-1]] = value

    if 'source' in shape:
        setpath(shape['source'], shape['customer_managed'] if configured else 'Microsoft.Storage'
                if check_id == 'ST-cmk-key' else 'disabled')
    if 'key_uri' in shape and configured:
        setpath(shape['key_uri'], VERSIONED if pinned else VERSIONLESS)
    if 'version' in shape and configured:
        setpath(shape['version'], '8f1d2c3b4a5e6f70819a2b3c4d5e6f70' if pinned else '')
    if configured and identity:
        if shape.get('user_assigned'):
            setpath(shape['user_assigned'], IDENTITY)
        if shape.get('client_identity'):
            setpath(shape['client_identity'], '22222222-2222-2222-2222-222222222222')
        if shape.get('identity_type'):
            setpath(shape['identity_type'], 'userAssignedIdentity')
    return properties


class KeyReferenceTests(unittest.TestCase):
    def test_every_reviewed_shape_reports_the_same_three_facts(self):
        for check_id, shape in SHAPES.items():
            observed = project_key(shaped({}, check_id), shape)
            self.assertEqual({'configured': True, 'version_pinned': True, 'identity': 'user_assigned'}, observed,
                             check_id)
            self.assertTrue(valid(observed))

    def test_a_versionless_reference_is_not_reported_as_version_pinned(self):
        for check_id, shape in SHAPES.items():
            observed = project_key(shaped({}, check_id, pinned=False), shape)
            self.assertFalse(observed['version_pinned'], check_id)
            self.assertTrue(observed['configured'])

    def test_provider_managed_keys_report_no_key_no_version_and_no_identity(self):
        for check_id, shape in SHAPES.items():
            observed = project_key(shaped({}, check_id, configured=False), shape)
            self.assertEqual({'configured': False, 'version_pinned': False, 'identity': 'unspecified'}, observed,
                             check_id)

    def test_absent_and_unreadable_references_never_claim_a_key(self):
        for check_id, shape in SHAPES.items():
            self.assertEqual(False, project_key({}, shape)['configured'], check_id)
        # A key identifier that cannot be parsed must not become a rotation claim.
        for broken in ('not-a-url', 'http://example-vault.vault.azure.net/keys/k/1', VAULT, VAULT + '/secrets/s/1', 7):
            properties = shaped({}, 'ACR-cmk-key')
            properties['encryption']['keyVaultProperties']['keyIdentifier'] = broken
            self.assertIsNone(project_key(properties, SHAPES['ACR-cmk-key']), broken)

    def test_identity_type_is_reported_exactly_and_never_invented(self):
        properties = shaped({}, 'REDIS-cmk-key', identity=False)
        properties['encryption']['customerManagedKeyEncryption']['keyEncryptionKeyIdentity'] = {
            'identityType': 'systemAssignedIdentity'}
        self.assertEqual('system_assigned', project_key(properties, SHAPES['REDIS-cmk-key'])['identity'])
        bare = shaped({}, 'REDIS-cmk-key', identity=False)
        self.assertEqual('unspecified', project_key(bare, SHAPES['REDIS-cmk-key'])['identity'])

    def test_no_vault_host_key_name_or_version_value_is_retained(self):
        for check_id, shape in SHAPES.items():
            payload = json.dumps(project_key(shaped({}, check_id), shape))
            for secret in ('example-vault', 'audit-key', '8f1d2c3b4a5e6f70819a2b3c4d5e6f70', 'vault.azure.net'):
                self.assertNotIn(secret, payload, check_id)

    def test_validation_rejects_impossible_records(self):
        self.assertFalse(valid({'configured': False, 'version_pinned': True, 'identity': 'unspecified'}))
        self.assertFalse(valid({'configured': False, 'version_pinned': False, 'identity': 'user_assigned'}))
        self.assertFalse(valid({'configured': True, 'version_pinned': True, 'identity': 'other'}))
        self.assertFalse(valid({'configured': True, 'version_pinned': True}))
        self.assertFalse(valid('configured'))

    def test_the_adapter_projects_through_the_shared_predicate_path(self):
        for check_id in SHAPES:
            check = CHECKS[check_id]
            raw = {'properties': shaped({'provisioningState': 'Succeeded'}, check_id)}
            observed = project(raw, check.resource_type)[check_id]
            self.assertEqual('observed', observed['state'])
            self.assertTrue(observed['value']['configured'])
            shape = SHAPES[check_id]
            if 'source' in shape:
                broken = {'properties': shaped({}, check_id)}
                target, *rest = shape['source'].split('.')
                node = broken['properties'][target]
                for part in rest[:-1]:
                    node = node[part]
                node[rest[-1]] = 7
                self.assertEqual('invalid', project(broken, check.resource_type)[check_id]['state'])
