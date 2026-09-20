import json
from pathlib import Path
import unittest
from cloud_governance.controls import CHECKS, validate_observations
from cloud_governance.graph import application_web, redirect_transport

SECRET = 'https://internal-host.corp.example.invalid/oauth2/callback'


class RedirectTransportTests(unittest.TestCase):
    def test_transport_is_reported_without_retaining_any_redirect_uri(self):
        observed = application_web({'redirectUris': [SECRET, 'https://other.invalid/cb'],
                                    'implicitGrantSettings': {'enableAccessTokenIssuance': False,
                                                              'enableIdTokenIssuance': False}})
        payload = json.dumps(observed)
        # A redirect URI names an internal host; only the transport position is evidence.
        self.assertNotIn('internal-host', payload)
        self.assertNotIn('corp.example.invalid', payload)
        self.assertEqual('all_https', observed['APPREG-redirect-transport']['value'])

    def test_each_transport_position_is_distinguished(self):
        self.assertEqual('all_https', redirect_transport(['https://a.invalid/cb']))
        self.assertEqual('plaintext_http_present', redirect_transport(['https://a.invalid/cb', 'http://b.invalid/cb']))
        self.assertEqual('non_http_scheme_present', redirect_transport(['ms-app://s-1-15-2-1234']))
        self.assertEqual('none_declared', redirect_transport([]))

    def test_an_absent_block_is_missing_and_a_malformed_one_is_invalid(self):
        self.assertIsNone(redirect_transport(None))
        for bad in ('https://a.invalid', {'uri': 'x'}, [7], ['x' * 3000], list(range(600))):
            self.assertEqual('[invalid]', redirect_transport(bad))
        absent = application_web(None)
        self.assertEqual('missing', absent['APPREG-redirect-transport']['state'])
        self.assertEqual('missing', absent['APPREG-implicit-access-token']['state'])

    def test_implicit_grant_is_read_exactly_and_never_assumed(self):
        enabled = application_web({'implicitGrantSettings': {'enableAccessTokenIssuance': True,
                                                             'enableIdTokenIssuance': True}})
        self.assertTrue(enabled['APPREG-implicit-access-token']['value'])
        self.assertTrue(enabled['APPREG-implicit-id-token']['value'])
        # A non-boolean must not read as disabled.
        odd = application_web({'implicitGrantSettings': {'enableAccessTokenIssuance': 'false'}})
        self.assertEqual('invalid', odd['APPREG-implicit-access-token']['state'])
        self.assertEqual('missing', odd['APPREG-implicit-id-token']['state'])

    def test_projected_observations_satisfy_the_saved_evidence_contract(self):
        observed = application_web({'redirectUris': ['https://a.invalid/cb'],
                                    'implicitGrantSettings': {'enableAccessTokenIssuance': False,
                                                              'enableIdTokenIssuance': False}})
        validate_observations(observed, 'graph.application')
        objectives = json.loads(Path('cloud_governance/control_objectives.json').read_text())['checks']
        for cid in ('APPREG-implicit-access-token', 'APPREG-implicit-id-token', 'APPREG-redirect-transport'):
            self.assertEqual('graph.application', CHECKS[cid].resource_type)
            # These exist to give IA-13 an evidence path it previously had nowhere.
            self.assertIn('IA-13', objectives[CHECKS[cid].catalog_ref]['controls'])
