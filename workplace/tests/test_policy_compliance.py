import json
import unittest
from cloud_governance.collector import CollectionError
from cloud_governance.policy_compliance import (collect, control_labels, definition_controls, project,
                                                validate)
from cloud_governance.policy_query import (API_VERSION, MAX_RECORDS, PATH, FixturePolicyTransport,
                                           decode_records, query_url)

SUB = '11111111-1111-1111-1111-111111111111'
RESOURCE = '/subscriptions/' + SUB + '/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/acct'
ASSIGNMENT = '/subscriptions/' + SUB + '/providers/microsoft.authorization/policyassignments/nist-800-53-r5-audit'
REFERENCE = '72650e9f-97bc-4b2a-ab5f-9781a9fcecbc'

POLICY_SET = {'policyDefinitions': [
    {'policyDefinitionReferenceId': REFERENCE, 'groupNames': ['NIST_SP_800-53_R5_CM-6', 'NIST_SP_800-53_R5_AC-6(7)']},
    {'policyDefinitionReferenceId': 'unmapped-definition', 'groupNames': ['SOMETHING_ELSE_AC-2']}]}


def record(state='NonCompliant', **extra):
    return {'complianceState': state, 'policyDefinitionReferenceId': REFERENCE, 'resourceId': RESOURCE,
            'policyAssignmentId': ASSIGNMENT, 'policyAssignmentName': 'nist-800-53-r5-audit',
            'policyDefinitionAction': 'auditIfNotExists', 'timestamp': '2026-09-20T18:00:00Z',
            # Fields Azure returns that must not be retained.
            'managementGroupIds': 'EXAMPLE-MG,example-root,33333333-3333-3333-3333-333333333333',
            'effectiveParameters': 'SECRET-CANARY', 'policyAssignmentParameters': 'SECRET-CANARY', **extra}


class PolicyQueryTests(unittest.TestCase):
    def test_only_one_url_can_be_built_and_it_pins_its_api_version(self):
        url = query_url(SUB, 10)
        self.assertIn(PATH, url)
        self.assertIn('api-version=' + API_VERSION, url)
        self.assertTrue(url.startswith('https://management.azure.com/subscriptions/' + SUB))

    def test_an_inexact_subscription_or_record_limit_is_refused_before_any_request(self):
        for bad in ('not-a-uuid', 'C687BD83-9FEC-4D0F-A460-0D8FBFDC40D8', SUB + '/resourceGroups/x',
                    '', None, 7, ['x']):
            with self.assertRaises(ValueError):
                query_url(bad, 10)
        for limit in (0, -1, MAX_RECORDS + 2, 1.5, '10', True):
            with self.assertRaises(ValueError):
                query_url(SUB, limit)

    def test_the_fixture_transport_enforces_the_same_contract(self):
        transport = FixturePolicyTransport({SUB: [record()]})
        self.assertEqual(1, len(transport.query(SUB)))
        self.assertEqual([SUB], transport.requested)
        with self.assertRaises(ValueError):
            transport.query('not-a-uuid')
        with self.assertRaises(CollectionError):
            transport.query('22222222-2222-2222-2222-222222222222')
        denied = FixturePolicyTransport({SUB: {'fixture_error': 403}})
        with self.assertRaises(CollectionError):
            denied.query(SUB)

    def test_an_operator_export_is_bounded_and_versioned(self):
        self.assertEqual([], decode_records(json.dumps({'schema_version': '1.0', 'records': []})))
        for bad in (json.dumps({'schema_version': '2.0', 'records': []}),
                    json.dumps({'records': []}), json.dumps({'schema_version': '1.0'}),
                    json.dumps({'schema_version': '1.0', 'records': {}}), '[]'):
            with self.assertRaises(ValueError):
                decode_records(bad)


class PolicyComplianceTests(unittest.TestCase):
    def test_control_labels_read_microsofts_group_names_including_enhancements(self):
        self.assertEqual(['AC-6(7)', 'CM-6'],
                         control_labels(['NIST_SP_800-53_R5_CM-6', 'NIST_SP_800-53_R5_AC-6(7)']))
        # Groups from another framework, or malformed names, contribute nothing.
        self.assertEqual([], control_labels(['SOMETHING_ELSE_AC-2', 'NIST_SP_800-53_R5_', None, 7]))
        self.assertEqual([], control_labels(None))

    def test_definition_mapping_covers_every_readable_reference(self):
        mapping = definition_controls(POLICY_SET)
        self.assertEqual(['AC-6(7)', 'CM-6'], mapping[REFERENCE])
        self.assertEqual([], mapping['unmapped-definition'])
        for bad in (None, {}, {'policyDefinitions': 'x'}):
            with self.assertRaises(ValueError):
                definition_controls(bad)

    def test_a_projected_record_keeps_only_bounded_facts(self):
        row = project(record(), definition_controls(POLICY_SET))
        self.assertEqual({'reference', 'resource_id', 'scope', 'assignment', 'action', 'compliance_state',
                          'result', 'controls', 'evaluated_at'}, set(row))
        self.assertEqual('resource', row['scope'])
        self.assertEqual('FAIL', row['result'])
        self.assertEqual(['AC-6(7)', 'CM-6'], row['controls'])
        self.assertEqual(RESOURCE.lower(), row['resource_id'])

    def test_management_hierarchy_and_parameter_values_are_never_retained(self):
        payload = json.dumps(collect([record()], POLICY_SET))
        for leaked in ('EXAMPLE-MG', 'example-root', 'SECRET-CANARY', 'managementGroupIds', 'effectiveParameters'):
            self.assertNotIn(leaked, payload)

    def test_only_the_two_documented_states_conclude_and_anything_else_is_unknown(self):
        controls = definition_controls(POLICY_SET)
        self.assertEqual('PASS', project(record('Compliant'), controls)['result'])
        self.assertEqual('FAIL', project(record('NonCompliant'), controls)['result'])
        for state in ('Exempt', 'Conflict', 'Unknown'):
            self.assertEqual('UNKNOWN', project(record(state), controls)['result'])
        # An unrecognised state must not borrow a result from a neighbouring one.
        odd = project(record('DefinitelyCompliantHonest'), controls)
        self.assertEqual('UNKNOWN', odd['result'])
        self.assertEqual('[unrecognised]', odd['compliance_state'])

    def test_unreadable_records_are_counted_and_never_become_results(self):
        broken = [record(resourceId='not-a-resource'), record(policyDefinitionReferenceId=''), 'nonsense', None]
        section = collect(broken + [record()], POLICY_SET)
        self.assertEqual(1, section['summary']['record_count'])
        self.assertEqual(4, section['summary']['unreadable_records'])
        self.assertEqual('FINDINGS_PRESENT', section['summary']['conclusion'])

    def test_an_empty_evaluation_is_incomplete_rather_than_compliant(self):
        section = collect([], POLICY_SET)
        self.assertEqual('INCOMPLETE', section['summary']['conclusion'])
        self.assertEqual(0, section['summary']['record_count'])
        self.assertTrue(any('Absent evaluation is not compliance' in limit for limit in section['limits']))

    def test_records_from_another_assignment_are_filtered_out(self):
        other = record(policyAssignmentName='SecurityCenterBuiltIn')
        section = collect([other, record()], POLICY_SET, assignment_name='nist-800-53-r5-audit')
        self.assertEqual(1, section['summary']['record_count'])
        self.assertEqual('nist-800-53-r5-audit', section['assignment_filter'])

    def test_definitions_without_a_control_mapping_stay_visible(self):
        unmapped = record(policyDefinitionReferenceId='unmapped-definition')
        section = collect([unmapped], POLICY_SET)
        self.assertEqual(1, section['summary']['records_without_control_mapping'])
        self.assertEqual([], section['results'][0]['controls'])

    def test_saved_evidence_is_validated_structurally(self):
        section = collect([record()], POLICY_SET)
        self.assertIs(section, validate(section))
        for mutate in (lambda s: s['results'].append(dict(s['results'][0])),
                       lambda s: s['results'][0].update(result='MAYBE'),
                       lambda s: s['results'][0].update(controls=['not a control']),
                       lambda s: s['summary'].update(record_count=99),
                       lambda s: s.update(schema_version='9.9'),
                       lambda s: s.pop('limits')):
            broken = json.loads(json.dumps(section))
            mutate(broken)
            with self.assertRaises(ValueError):
                validate(broken)

    def test_policy_evaluates_at_three_scopes_and_each_is_kept_distinct(self):
        # Most records in a real tenant are subscription scoped; discarding them loses the evidence.
        subscription = record(resourceId='/subscriptions/' + SUB)
        group = record(resourceId='/subscriptions/' + SUB + '/resourceGroups/audit-demo')
        section = collect([subscription, group, record()], POLICY_SET)
        self.assertEqual(3, section['summary']['record_count'])
        self.assertEqual({'resource': 1, 'resource_group': 1, 'subscription': 1},
                         section['summary']['records_by_scope'])
        self.assertEqual(0, section['summary']['unreadable_records'])
        self.assertTrue(any('describes that scope, not each resource inside it' in limit
                            for limit in section['limits']))

    def test_a_scoped_result_never_claims_the_resources_inside_it(self):
        from cloud_governance.policy_compliance import scope_of
        self.assertEqual('subscription', scope_of('/subscriptions/' + SUB)[1])
        self.assertEqual('resource_group', scope_of('/subscriptions/' + SUB + '/resourceGroups/rg')[1])
        self.assertEqual('resource', scope_of(RESOURCE)[1])
        for bad in ('not-a-resource', '/subscriptions/not-a-uuid', '/subscriptions', '', None, 7):
            self.assertIsNone(scope_of(bad))

    def test_local_retention_overflow_is_explicitly_truncated(self):
        # Live transport follows continuation. The projector additionally retains a
        # bounded sample and detects overflow through one extra row.
        def distinct(count):
            return [record(resourceId=RESOURCE + str(index)) for index in range(count)]
        exact = collect(distinct(10), POLICY_SET, limit=10)
        self.assertFalse(exact['summary']['truncated'])
        self.assertEqual(10, exact['summary']['record_count'])
        over = collect(distinct(11), POLICY_SET, limit=10)
        self.assertTrue(over['summary']['truncated'])
        self.assertEqual(10, over['summary']['record_count'])
        # Truncated evidence still reports the findings it did read.
        self.assertEqual('FINDINGS_PRESENT', over['summary']['conclusion'])
        validate(over)

    def test_truncated_evidence_can_never_conclude_compliant(self):
        def compliant(count):
            return [record('Compliant', resourceId=RESOURCE + str(index)) for index in range(count)]
        whole = collect(compliant(5), POLICY_SET, limit=5)
        self.assertEqual('PROVIDER_ASSERTED_COMPLIANT', whole['summary']['conclusion'])
        # The same all-compliant records, truncated, must not read as a compliant estate.
        cut = collect(compliant(6), POLICY_SET, limit=5)
        self.assertEqual('INCOMPLETE', cut['summary']['conclusion'])
        self.assertTrue(any('truncated sample' in limit for limit in cut['limits']))
        # A saved section claiming otherwise is rejected.
        forged = json.loads(json.dumps(cut))
        forged['summary']['conclusion'] = 'PROVIDER_ASSERTED_COMPLIANT'
        with self.assertRaises(ValueError):
            validate(forged)

    def test_the_query_asks_for_one_record_beyond_the_retained_limit(self):
        from cloud_governance.policy_query import MAX_RECORDS, QUERY_TOP, query_url
        self.assertEqual(MAX_RECORDS + 1, QUERY_TOP)
        self.assertIn('$top=' + str(QUERY_TOP), query_url(SUB, QUERY_TOP))
        transport = FixturePolicyTransport({SUB: [record()]})
        transport.query(SUB)  # Default requests the extra record.
        with self.assertRaises(ValueError):
            query_url(SUB, QUERY_TOP + 1)

    def test_a_denied_query_reports_its_status_not_a_network_fault(self):
        from urllib.error import HTTPError
        from cloud_governance.policy_query import PolicyQueryTransport

        class Credential:
            def get_token(self):
                return 'token'

        class Denying:
            def open(self, request, timeout=None):
                raise HTTPError(request.full_url, 403, 'Forbidden', {}, None)

        transport = PolicyQueryTransport(Credential(), opener=Denying())
        with self.assertRaises(CollectionError) as caught:
            transport.query(SUB)
        # HTTPError subclasses OSError; catching OSError first would hide the 403.
        self.assertEqual('http_error', caught.exception.code)
        self.assertEqual(403, caught.exception.status)
