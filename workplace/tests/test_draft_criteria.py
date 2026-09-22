import unittest
from cloud_governance import report_model
from cloud_governance.controls import CHECKS, validate_policy
from cloud_governance.workflow import assess_snapshot
from scripts.draft_criteria import BASELINE, TLS_ACCEPTED, draft
from tests.test_controls import collect, fixture


def report():
    responses, policy = fixture()
    return assess_snapshot(collect(responses))  # No criteria: every predicate is unjudged.


class DraftCriteriaTests(unittest.TestCase):
    def test_a_draft_is_never_written_as_approved(self):
        document, _ = draft(report())
        self.assertEqual('draft', document['status'])
        self.assertIn('REPLACE', document['id'])
        # A draft is a valid criteria document, it simply cannot produce a positive result.
        self.assertIs(document, validate_policy(document))

    def test_baseline_proposals_do_not_depend_on_what_the_tenant_does(self):
        document, review = draft(report())
        # httpsOnly is proposed true regardless of the observed value in the run.
        self.assertEqual({'operator': 'equals', 'value': True}, document['checks']['ST-https'])
        self.assertEqual({'operator': 'equals', 'value': False}, document['checks']['ST-anonymous-blob'])
        flagged = {row['check'] for row in review}
        # Every proposal that merely echoes the tenant is flagged for a deliberate decision.
        for check_id, criterion in document['checks'].items():
            path = CHECKS[check_id].path
            if path not in BASELINE and path not in ('minimumTlsVersion', 'minTlsVersion',
                                                     'scmMinTlsVersion', 'minimalTlsVersion'):
                self.assertIn(check_id, flagged, check_id)

    def test_tls_is_proposed_as_named_acceptable_values_not_an_ordering(self):
        document, _ = draft(report())
        criterion = document['checks']['ST-tls']
        self.assertEqual('one_of', criterion['operator'])
        self.assertTrue(set(criterion['value']) <= set(TLS_ACCEPTED))
        self.assertNotIn('TLS1_0', criterion['value'])

    def test_a_proposal_stronger_than_the_tenant_is_kept_and_explained(self):
        source = report()
        rows = report_model.configuration_results(source)
        target = next(r for r in rows if r['check_id'] == 'ST-https')
        target['observation'] = {'state': 'observed', 'value': False}
        document, review = draft(source)
        # The weaker observation does not soften the proposal.
        self.assertEqual(True, document['checks']['ST-https']['value'])
        note = next(row for row in review if row['check'] == 'ST-https')
        self.assertEqual(False, note['observed'])
        self.assertIn('will read FAIL', note['why'])

    def test_predicates_without_an_observation_or_baseline_are_left_out(self):
        source = report()
        for row in report_model.configuration_results(source):
            row['observation'] = {'state': 'missing'}
        document, _ = draft(source)
        for check_id in document['checks']:
            self.assertIn(CHECKS[check_id].path, set(BASELINE) | {'minimumTlsVersion', 'minTlsVersion',
                                                                  'scmMinTlsVersion', 'minimalTlsVersion'})
