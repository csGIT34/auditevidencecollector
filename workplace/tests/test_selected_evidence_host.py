from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from cloud_governance.archive import encode
from cloud_governance.evidence_report import ENCRYPTION, load, publish, request_options
from cloud_governance.hosting import execute
from cloud_governance.operational import publish as import_operational
from tests.test_archive import MemoryStore
from tests.test_evidence_report import source
from tests.test_hosting import environment

ROOT = Path(__file__).resolve().parents[1]


class SelectedEvidenceHostTests(unittest.TestCase):
    def test_operating_periods_adverse_assertions_and_requirements_survive_selection(self):
        store = MemoryStore()
        saved = source(store)
        document = json.loads((ROOT / 'examples/operational-evidence.json').read_text())
        document['records'][0]['assertion'] = 'NOT_SATISFIED'
        imported = import_operational(store, saved['manifest']['run_id'], encode(document),
                                      as_of='2026-09-21T12:00:00Z', max_age_hours=24 * 7)
        profile = {**deepcopy(ENCRYPTION), 'objective_ids': ['BV-B']}
        published = publish(store, saved['manifest']['run_id'], topic=profile, operational_ids=[imported['evidence_id']])
        report = load(store, published['report_id'])['report']
        record = next(r for r in report['records'] if r['kind'] == 'attributed_record')
        self.assertEqual('ATTRIBUTED_NOT_SATISFIED', record['result'])
        self.assertEqual(document['records'][0]['period_start'], record['observations']['period_start'])
        self.assertEqual('ASSERTED_NOT_SATISFIED', report['operational_sources'][0]['requirement_results'][0]['state'])
        self.assertTrue(report['summary']['coverage_incomplete'])
        store.objects[imported['objects']['review.json']['key']] += b' '
        with self.assertRaises(ValueError):
            load(store, published['report_id'])

    def test_operating_review_of_another_run_is_rejected_without_writes(self):
        store = MemoryStore()
        first, second = source(store), source(store)
        document = (ROOT / 'examples/operational-evidence.json').read_bytes()
        imported = import_operational(store, first['manifest']['run_id'], document,
                                      as_of='2026-09-21T12:00:00Z', max_age_hours=24 * 7)
        before = dict(store.objects)
        with self.assertRaises(ValueError):
            publish(store, second['manifest']['run_id'], operational_ids=[imported['evidence_id']])
        self.assertEqual(before, store.objects)

    def test_hosted_selection_archives_pdf_without_any_collection(self):
        store = MemoryStore()
        saved = source(store)
        @contextmanager
        def factory(settings, deadline, operation):
            self.assertEqual('evidence-report', operation)
            yield store, None
        with patch('cloud_governance.collector.Collector.collect', side_effect=AssertionError('No recollection')):
            result = execute('evidence-report', run_id=saved['manifest']['run_id'], selection={'topic': 'encryption-at-rest'},
                             env={**environment(), 'CG_REPORT_ENABLED': 'true'}, factory=factory)
        self.assertEqual('complete', result['state'])
        self.assertTrue(store.read(result['pdf_key']).startswith(b'%PDF'))
        self.assertIn('execution_provenance', load(store, result['report_id'])['report'])

    def test_report_stays_disabled_before_credentials_are_constructed(self):
        with patch('cloud_governance.hosting.token_credential', side_effect=AssertionError('No credentials')):
            result = execute('evidence-report', run_id='r-' + 'a' * 32, env={'CG_REPORT_ENABLED': 'false'})
        self.assertEqual('disabled', result['state'])

    def test_http_rejects_ambiguous_or_unbounded_requests_before_execution(self):
        import azure.functions as func
        import function_app
        valid = {'run_id': 'r-' + 'a' * 32, 'topic': 'encryption-at-rest'}
        bodies = [b'{}', encode({**valid, 'topic_profile': ENCRYPTION}), encode({**valid, 'extra': True}),
                  encode({**valid, 'controls': 'SC-28'}), encode({**valid, 'wiz_import_id': 'latest'}),
                  b'{"run_id":"r-' + b'a' * 32 + b'","run_id":"latest"}', b' ' * 65537]
        with patch.object(function_app, 'execute', side_effect=AssertionError('Invalid request reached execution')):
            for body in bodies:
                response = function_app.generate_evidence_report(func.HttpRequest('POST', 'https://fixture/api/evidence/reports', body=body))
                self.assertEqual(400, response.status_code)
        with patch.object(function_app, 'execute', return_value={'state': 'complete'}) as execute_mock:
            response = function_app.generate_evidence_report(func.HttpRequest('POST', 'https://fixture/api/evidence/reports', body=encode(valid)))
            self.assertEqual(201, response.status_code)
            execute_mock.assert_called_once_with('evidence-report', run_id=valid['run_id'], selection={'topic': 'encryption-at-rest'})

    def test_full_report_indexes_all_twenty_families_without_claiming_coverage(self):
        store = MemoryStore()
        saved = source(store)
        manifest = publish(store, saved['manifest']['run_id'])
        report = load(store, manifest['report_id'])['report']
        self.assertEqual(20, len({r['control'].split('-')[0] for r in report['control_coverage']}))
        self.assertTrue(any(r['status'] == 'NOT_ASSESSED' for r in report['control_coverage']))
