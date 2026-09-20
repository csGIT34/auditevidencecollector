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
        self.assertEqual(ASSIGNMENT, section['assignment_filter'])
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
