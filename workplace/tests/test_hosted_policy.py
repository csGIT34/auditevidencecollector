import json
from contextlib import contextmanager
import unittest
from cloud_governance import report_model
from cloud_governance.archive import load_run
from cloud_governance.collector import FixtureTransport
from cloud_governance.hosting import ConfigurationError, ExecutionError, Settings, execute
from cloud_governance.policy_query import FixturePolicyTransport, assignment_url, set_definition_url
from tests.helpers import SUB
from tests.test_archive import MemoryStore
from tests.test_controls import fixture
from tests.test_hosting import environment

ASSIGNMENT = 'nist-800-53-r5-audit'
REFERENCE = '72650e9f-97bc-4b2a-ab5f-9781a9fcecbc'
SET_ID = '/providers/Microsoft.Authorization/policySetDefinitions/179d1daa-458f-4e47-8086-2a68d0d6c38f'


def policy_metadata():
    """The two GET reads the collector makes to freeze Microsoft's control mapping."""
    return {assignment_url(SUB, ASSIGNMENT): {'id': 'assignment', 'properties': {'policyDefinitionId': SET_ID}},
            set_definition_url(SET_ID): {'id': 'set', 'properties': {'policyDefinitions': [
                {'policyDefinitionReferenceId': REFERENCE,
                 'groupNames': ['NIST_SP_800-53_R5_CM-6', 'NIST_SP_800-53_R5_SC-28']}]}}}


def policy_records(state='Compliant'):
    resource = '/subscriptions/' + SUB + '/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/acct'
    return [{'complianceState': state, 'policyDefinitionReferenceId': REFERENCE, 'resourceId': resource,
             'policyAssignmentId': '/subscriptions/' + SUB + '/providers/microsoft.authorization/policyassignments/' + ASSIGNMENT,
             'policyAssignmentName': ASSIGNMENT, 'policyDefinitionAction': 'audit',
             'timestamp': '2026-09-20T18:00:00Z'}]


def arm_responses():
    """All-service fixture plus the subscription metadata a hosted run verifies first."""
    from cloud_governance.collector import SUBSCRIPTIONS_API, endpoint
    from tests.test_hosting import TENANT
    responses, _ = fixture()
    responses[endpoint('/subscriptions/' + SUB, SUBSCRIPTIONS_API)] = {
        'subscriptionId': SUB, 'tenantId': TENANT, 'state': 'Enabled'}
    return responses


def hosted(store, *, records=None, metadata=None, attach=True, env_extra=None):
    responses = arm_responses()

    @contextmanager
    def factory(settings, deadline, operation):
        transport = FixtureTransport(responses)
        if attach:
            transport.policy_transport = FixturePolicyTransport(
                {SUB: policy_records() if records is None else records},
                metadata=policy_metadata() if metadata is None else metadata)
        yield store, transport

    env = {**environment(), 'CG_SUBSCRIPTION_IDS': SUB, 'CG_POLICY_ASSIGNMENT': ASSIGNMENT, **(env_extra or {})}
    return execute('collect', env=env, factory=factory)


class HostedPolicyCollectionTests(unittest.TestCase):
    def test_policy_evidence_is_absent_unless_an_assignment_is_configured(self):
        self.assertIsNone(Settings.parse(environment()).policy_assignment)
        store = MemoryStore()

        @contextmanager
        def factory(settings, deadline, operation):
            yield store, FixtureTransport(arm_responses())

        outcome = execute('collect', env={**environment(), 'CG_SUBSCRIPTION_IDS': SUB}, factory=factory)
        saved = load_run(store, outcome['run_id'])['assessment']
        self.assertIsNone(report_model.policy_compliance(saved))
        self.assertIsNone(outcome['policy_summary'])

    def test_a_hosted_run_archives_policy_evidence_beside_the_other_kinds(self):
        store = MemoryStore()
        outcome = hosted(store)
        self.assertEqual('complete', outcome['archive_state'])
        self.assertEqual(1, outcome['policy_summary']['record_count'])
        saved = load_run(store, outcome['run_id'])['assessment']
        section = report_model.policy_compliance(saved)
        self.assertEqual(policy_records()[0]['policyAssignmentId'].lower(), section['assignment_filter'].lower())
        self.assertEqual(['CM-6', 'SC-28'], section['results'][0]['controls'])
        # All three evidence kinds are peers in the same archived run.
        self.assertEqual(['resource_rules', 'configuration', 'policy_compliance'],
                         [kind for kind, _ in report_model.sections(saved)])

    def test_the_control_mapping_is_frozen_into_the_run(self):
        store = MemoryStore()
        outcome = hosted(store)
        saved = load_run(store, outcome['run_id'])['assessment']
        controls = report_model.policy_results(saved)[0]['controls']
        # A later change to Microsoft's initiative cannot alter what this run recorded.
        self.assertEqual(['CM-6', 'SC-28'], controls)
        self.assertIn('SC-28', saved['control_mapping']['controls'])

    def test_a_configured_assignment_without_a_transport_fails_rather_than_collecting_silently(self):
        with self.assertRaises(ExecutionError):
            hosted(MemoryStore(), attach=False)

    def test_a_denied_policy_read_fails_the_operation_rather_than_archiving_a_gap(self):
        # Compliance the collector could not read must not be archived as an empty result.
        with self.assertRaises(ExecutionError):
            hosted(MemoryStore(), metadata={})

    def test_policy_collection_requires_exactly_one_selected_subscription(self):
        with self.assertRaises(ConfigurationError):
            Settings.parse({**environment(), 'CG_SUBSCRIPTION_IDS': SUB + ',22222222-2222-2222-2222-222222222222',
                            'CG_POLICY_ASSIGNMENT': ASSIGNMENT})

    def test_findings_are_carried_into_the_hosted_outcome(self):
        store = MemoryStore()
        outcome = hosted(store, records=policy_records('NonCompliant'))
        self.assertEqual({'PASS': 0, 'FAIL': 1, 'UNKNOWN': 0}, outcome['policy_summary']['counts'])
        self.assertEqual('FINDINGS_PRESENT', outcome['policy_summary']['conclusion'])

    def test_the_auditor_pdf_carries_the_policy_evidence(self):
        from cloud_governance.archive import publish_pdf
        from pypdf import PdfReader
        from io import BytesIO
        store = MemoryStore()
        outcome = hosted(store)
        published = publish_pdf(store, outcome['run_id'])
        text = '\n'.join(page.extract_text() or '' for page in
                         PdfReader(BytesIO(store.read(published['pdf']['key']))).pages)
        # The kind that covers most controls must not be missing from the auditor artifact.
        self.assertIn('Azure Policy compliance', text)
        self.assertIn('Microsoft evaluated these results', text)
        self.assertIn(REFERENCE, text)
        self.assertIn('CM-6', text)

    def test_a_truncated_evaluation_is_stated_in_the_pdf(self):
        from cloud_governance.archive import publish_pdf
        from pypdf import PdfReader
        from io import BytesIO
        from cloud_governance.policy_compliance import MAX_RECORDS
        resource = '/subscriptions/' + SUB + '/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/'
        many = [dict(policy_records()[0], resourceId=resource + str(index)) for index in range(MAX_RECORDS + 1)]
        store = MemoryStore()
        outcome = hosted(store, records=many)
        self.assertTrue(outcome['policy_summary']['truncated'])
        published = publish_pdf(store, outcome['run_id'])
        text = '\n'.join(page.extract_text() or '' for page in
                         PdfReader(BytesIO(store.read(published['pdf']['key']))).pages)
        self.assertIn('truncated sample', text)

    def test_the_hosted_policy_transport_receives_a_scoped_credential(self):
        """The SDK credential needs a scope; the policy transport calls get_token() with none."""
        from contextlib import ExitStack
        from unittest.mock import patch
        from cloud_governance.hosting import resources
        from cloud_governance.workflow import Deadline
        captured = {}

        class FakeCredential:
            def get_token(self, *scopes):
                captured['scopes'] = scopes
                class Token:
                    token, expires_on = 'x', 2 ** 31
                return Token()

        settings = Settings.parse({**environment(), 'CG_SUBSCRIPTION_IDS': SUB,
                                   'CG_POLICY_ASSIGNMENT': ASSIGNMENT})
        with ExitStack() as stack:
            stack.enter_context(patch('cloud_governance.hosting.token_credential', return_value=FakeCredential()))
            stack.enter_context(patch('cloud_governance.hosting.BlobStore'))
            try:
                with resources(settings, Deadline(60), 'collect') as (_, transport):
                    transport.policy_transport.credential.get_token()
            except Exception:
                pass  # Only the credential contract is under test here.
        # A raw SDK credential would have been called with no scope and failed at runtime.
        self.assertTrue(captured.get('scopes'), 'policy transport must receive a scoped credential')

    def test_a_denied_policy_read_names_which_read_was_refused(self):
        """Three reads are authorized at three scopes; a bare 403 is not actionable."""
        from cloud_governance.policy_query import assignment_url
        # Only the assignment resolves, so the initiative read is the one that fails.
        partial = {assignment_url(SUB, ASSIGNMENT): policy_metadata()[assignment_url(SUB, ASSIGNMENT)]}
        with self.assertRaises(ExecutionError) as caught:
            hosted(MemoryStore(), metadata=partial)
        self.assertEqual('initiative', caught.exception.outcome['policy_read'])

    def test_manual_definitions_are_counted_but_not_rendered_as_evidence(self):
        """Azure emits one Manual record per definition whatever the estate contains."""
        from cloud_governance.archive import publish_pdf
        from pypdf import PdfReader
        from io import BytesIO
        manual = dict(policy_records()[0], policyDefinitionAction='manual',
                      policyDefinitionReferenceId='9f3c7ad2-55b1-4e0e-9a77-0d2b6c8e41aa',
                      resourceId='/subscriptions/' + SUB)
        store = MemoryStore()
        outcome = hosted(store, records=policy_records() + [manual])
        published = publish_pdf(store, outcome['run_id'])
        text = '\n'.join(page.extract_text() or '' for page in
                         PdfReader(BytesIO(store.read(published['pdf']['key']))).pages)
        self.assertIn('1 of 2 records in this assignment carry the Manual effect', text)
        self.assertIn('1 records evaluated a resource or a scope', text)
        # The evaluated definition is evidence and stays; the Manual one is not rendered.
        self.assertIn(REFERENCE, text)
        self.assertNotIn('9f3c7ad2-55b1-4e0e-9a77-0d2b6c8e41aa', text)
        # It is still archived in full: the PDF omits it, the evidence does not.
        saved = load_run(store, outcome['run_id'])['assessment']
        self.assertEqual(2, len(report_model.policy_results(saved)))
