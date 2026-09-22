"""Regression proofs for Policy evidence completeness, scope and historical behavior."""
import copy
import io
import json
import unittest
from urllib.parse import parse_qs, urlsplit

from cloud_governance.archive import digest, encode, load_run, save_run
from cloud_governance.collector import Collector, CollectionError, FixtureTransport, endpoint, INVENTORY_API
from cloud_governance.control_register import build
from cloud_governance.controls import overall_summary
from cloud_governance.policy_compliance import collect, project, definition_controls
from cloud_governance.policy_query import PolicyQueryTransport, FixturePolicyTransport, assignment_id, query_url
from cloud_governance.report import exit_code
from cloud_governance.workflow import assess_snapshot
from tests.test_archive import MemoryStore
from tests.test_controls import fixture
from tests.test_policy_compliance import record, POLICY_SET, SUB, RESOURCE, ASSIGNMENT


def storage_report(state='Compliant'):
    responses, criteria = fixture()
    url = endpoint('/subscriptions/' + SUB + '/resources', INVENTORY_API)
    responses[url]['value'] = [r for r in responses[url]['value'] if r['type'].lower() == 'microsoft.storage/storageaccounts']
    snapshot = Collector(FixtureTransport(responses), mode='offline_fixture').collect([SUB])
    mapping = copy.deepcopy(POLICY_SET)
    mapping['policyDefinitions'][0]['groupNames'].append('NIST_SP_800-53_R5_SC-28')
    section = collect([record(state, resourceId=responses[url]['value'][0]['id'])], mapping)
    return snapshot, assess_snapshot(snapshot, criteria=criteria, policy=section)


class Credential:
    def get_token(self):
        return 'offline-fixture'


class Pages:
    def __init__(self, pages):
        self.pages, self.requests = list(pages), []
    def open(self, request, timeout=None):
        self.requests.append(request)
        page = self.pages.pop(0)
        return io.BytesIO(json.dumps(page(request.full_url) if callable(page) else page).encode())


class PolicyIntegrityTests(unittest.TestCase):
    def test_policy_failure_reaches_actual_assessment_exit_and_archive(self):
        snapshot, report = storage_report('NonCompliant')
        self.assertEqual('FAILURES_FOUND', report['summary']['conclusion'])
        self.assertEqual(1, report['summary']['failed_check_count'])
        self.assertEqual(1, exit_code(report))
        store = MemoryStore()
        manifest = save_run(store, snapshot, report)
        self.assertEqual('complete', manifest['state'])
        self.assertEqual(report, load_run(store, manifest['run_id'])['assessment'])

    def test_old_archive_keeps_its_original_pre_policy_summary_and_bytes(self):
        snapshot, report = storage_report('NonCompliant')
        store = MemoryStore()
        manifest = save_run(store, snapshot, report)
        report.pop('summary_version')
        report['summary'] = overall_summary(report, include_policy=False)
        descriptor = manifest['objects']['assessment']
        raw = encode(report)
        store.objects[descriptor['key']] = raw
        descriptor.update(sha256=digest(raw), bytes=len(raw))
        manifest['assessment_conclusion'] = report['summary']['conclusion']
        manifest['coverage_incomplete'] = report['summary']['coverage_incomplete']
        store.objects['runs/' + manifest['run_id'] + '/manifest.json'] = encode(manifest)
        original = dict(store.objects)
        loaded = load_run(store, manifest['run_id'])
        self.assertEqual('SUPPORTED_SCOPE_SATISFIED', loaded['assessment']['summary']['conclusion'])
        self.assertEqual(original, store.objects)

    def test_manual_and_truncated_evidence_never_becomes_automated_control_coverage(self):
        for section in (collect([record('Compliant', policyDefinitionAction='manual')], POLICY_SET),
                        collect([record('Compliant', resourceId=RESOURCE + str(i)) for i in range(3)], POLICY_SET, limit=2)):
            register = build({'schema_version': '1.2', 'evidence': {'policy_compliance': section}})
            relevant = [r for r in register['controls'] if r['evidence_count']]
            self.assertTrue(relevant)
            self.assertTrue(all(r['status'] == 'INCOMPLETE_EVIDENCE' for r in relevant))

    def test_bad_stale_and_future_timestamps_preserve_assertion_but_not_pass(self):
        for stamp in ('not-a-date', None, '2026-09-18T12:00:00Z', '2026-09-22T12:00:00Z'):
            section = collect([record('Compliant', timestamp=stamp)], POLICY_SET,
                              as_of='2026-09-21T12:00:00Z', max_age_seconds=86400)
            self.assertEqual('Compliant', section['results'][0]['compliance_state'])
            self.assertEqual('UNKNOWN', section['results'][0]['result'])

    def test_incomplete_policy_propagates_even_when_another_row_failed(self):
        _, report = storage_report('NonCompliant')
        section = collect([record('NonCompliant'), record('Unknown', resourceId=RESOURCE + '2')], POLICY_SET)
        report['evidence']['policy_compliance'] = section
        summary = overall_summary(report)
        self.assertEqual('FAILURES_FOUND', summary['conclusion'])
        self.assertTrue(summary['coverage_incomplete'])

    def test_assignment_filter_precedes_limit_and_distinguishes_same_name(self):
        unrelated = record('NonCompliant', policyAssignmentId=ASSIGNMENT.replace('/providers/', '/resourceGroups/other/providers/', 1))
        rows = [unrelated] * 5001 + [record('Compliant')]
        result = FixturePolicyTransport({SUB: rows}).query(SUB, assignment=ASSIGNMENT)
        self.assertEqual(1, len(result))
        self.assertTrue(result.complete)
        rejected = collect([unrelated], POLICY_SET, assignment_id=ASSIGNMENT)
        self.assertEqual(1, rejected['summary']['unreadable_records'])

    def test_resource_group_query_and_projection_both_enforce_scope(self):
        result = query_url(SUB, None, assignment=ASSIGNMENT, resource_group='audit-demo')
        self.assertIn('/resourceGroups/audit-demo/providers/Microsoft.PolicyInsights/', result)
        self.assertEqual(["PolicyAssignmentId eq '" + ASSIGNMENT + "'"], parse_qs(urlsplit(result).query)['$filter'])
        foreign = record('Compliant', resourceId=RESOURCE.replace('audit-demo', 'other'))
        section = collect([record('Compliant'), foreign], POLICY_SET, assignment_id=ASSIGNMENT,
                          subscription=SUB, resource_group='audit-demo')
        self.assertEqual(1, section['summary']['record_count'])
        self.assertEqual(1, section['summary']['unreadable_records'])

    def test_management_group_assignment_is_retained_with_full_identity(self):
        scoped = '/providers/Microsoft.Management/managementGroups/work/providers/Microsoft.Authorization/policyAssignments/nist'
        self.assertEqual(scoped, assignment_id(SUB, scoped))
        result = project(record('Compliant', policyAssignmentId=scoped), definition_controls(POLICY_SET))
        self.assertEqual(scoped.lower(), result['assignment'])
        self.assertEqual('PASS', result['result'])

    def test_query_consumes_continuation_and_preserves_good_and_bad_evidence(self):
        pages = Pages([lambda url: {'value': [record('Compliant')], '@odata.nextLink': url + '&$skiptoken=second'},
                       {'value': [record('NonCompliant', resourceId=RESOURCE + '2')]}])
        result = PolicyQueryTransport(Credential(), opener=pages).query(SUB, assignment=ASSIGNMENT)
        self.assertEqual(2, len(pages.requests))
        self.assertTrue(all(r.method == 'POST' and r.data == b'' for r in pages.requests))
        self.assertTrue(result.complete)
        self.assertEqual({'PASS': 1, 'FAIL': 1, 'UNKNOWN': 0}, collect(result, POLICY_SET)['summary']['counts'])

    def test_page_bound_and_unsafe_continuation_cannot_claim_completeness(self):
        pages = Pages([lambda url: {'value': [record('Compliant')], '@odata.nextLink': url + '&$skiptoken=second'}])
        result = PolicyQueryTransport(Credential(), opener=pages).query(SUB, max_pages=1)
        self.assertFalse(result.complete)
        self.assertEqual('INCOMPLETE', collect(result, POLICY_SET)['summary']['conclusion'])
        for changed in ('https://attacker.invalid/path', query_url(SUB, None) + '&$filter=wrong&$skiptoken=next'):
            with self.subTest(changed=changed):
                pages = Pages([{'value': [], '@odata.nextLink': changed}])
                with self.assertRaises(CollectionError):
                    PolicyQueryTransport(Credential(), opener=pages).query(SUB)
                self.assertEqual(1, len(pages.requests))
