import unittest
from cloud_governance import report_model

RESOURCE = {'id': '/subscriptions/x/rule', 'result': 'PASS', 'rule_id': 'storage-sse', 'reason': 'ok',
            'controls': ['SC-28'], 'gaps': []}
PREDICATE = {'check_id': 'ST-https', 'result': 'PASS', 'title': 'HTTPS', 'control_refs': ['SC-8'],
             'resource_id': '/subscriptions/x/account'}
POLICY = {'reference': 'policy-def', 'result': 'PASS', 'resource_id': '/subscriptions/x/account',
          'controls': ['CM-6']}


def v10():
    return {'schema_version': '1.0', 'summary': {'conclusion': 'INCOMPLETE', 'coverage_incomplete': True},
            'results': [RESOURCE]}


def v11():
    return {'schema_version': '1.1', 'summary': {'conclusion': 'FAILURES_FOUND', 'coverage_incomplete': True},
            'results': [RESOURCE],
            'configuration_assessment': {'summary': {'conclusion': 'INCOMPLETE'}, 'results': [PREDICATE]},
            'overall_summary': {'conclusion': 'FAILURES_FOUND', 'coverage_incomplete': True}}


def v12():
    return {'schema_version': '1.2', 'summary': {'conclusion': 'FAILURES_FOUND', 'coverage_incomplete': True},
            'evidence': {
                'resource_rules': {'summary': {'conclusion': 'INCOMPLETE'}, 'results': [RESOURCE]},
                'configuration': {'summary': {'conclusion': 'INCOMPLETE'}, 'results': [PREDICATE]},
                'policy_compliance': {'summary': {'conclusion': 'INCOMPLETE'}, 'results': [POLICY]}}}


class ReportModelTests(unittest.TestCase):
    def test_every_schema_reads_its_reviewed_rule_results(self):
        for report in (v10(), v11(), v12()):
            self.assertEqual([RESOURCE], report_model.resource_results(report), report['schema_version'])

    def test_configuration_is_absent_before_it_existed_and_present_after(self):
        self.assertIsNone(report_model.configuration(v10()))
        self.assertEqual([], report_model.configuration_results(v10()))
        for report in (v11(), v12()):
            self.assertEqual([PREDICATE], report_model.configuration_results(report), report['schema_version'])
            self.assertEqual('INCOMPLETE', report_model.configuration_summary(report)['conclusion'])

    def test_policy_compliance_only_exists_in_the_current_schema(self):
        for report in (v10(), v11()):
            self.assertIsNone(report_model.policy_compliance(report))
            self.assertEqual([], report_model.policy_results(report))
        self.assertEqual([POLICY], report_model.policy_results(v12()))

    def test_the_overall_conclusion_comes_from_each_schema_as_recorded(self):
        # A 1.0 report has only one evidence kind, so its summary is the overall one.
        self.assertEqual('INCOMPLETE', report_model.overall(v10())['conclusion'])
        self.assertEqual('FAILURES_FOUND', report_model.overall(v11())['conclusion'])
        self.assertEqual('FAILURES_FOUND', report_model.overall(v12())['conclusion'])
        # In 1.1 the top-level summary is the reviewed-rule summary, not the overall one.
        self.assertEqual('FAILURES_FOUND', report_model.resource_summary(v11())['conclusion'])
        self.assertEqual('INCOMPLETE', report_model.resource_summary(v12())['conclusion'])

    def test_sections_lists_only_the_kinds_a_report_actually_carries(self):
        self.assertEqual(['resource_rules'], [kind for kind, _ in report_model.sections(v10())])
        self.assertEqual(['resource_rules', 'configuration'], [kind for kind, _ in report_model.sections(v11())])
        self.assertEqual(['resource_rules', 'configuration', 'policy_compliance'],
                         [kind for kind, _ in report_model.sections(v12())])

    def test_kinds_are_declared_in_presentation_order_and_schemas_are_known(self):
        self.assertEqual(('resource_rules', 'configuration', 'policy_compliance'), report_model.KINDS)
        self.assertEqual(('1.0', '1.1', '1.2'), report_model.SCHEMAS)
        self.assertFalse(report_model.is_current(v11()))
        self.assertTrue(report_model.is_current(v12()))
