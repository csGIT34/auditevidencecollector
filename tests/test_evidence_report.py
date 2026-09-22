import copy
from io import BytesIO, StringIO
import json
import tempfile
import unittest
from unittest.mock import patch
from pypdf import PdfReader

from cloud_governance.archive import save_run, load_run
from cloud_governance.cli import main
from cloud_governance.evidence_report import ENCRYPTION, build, load, publish
from cloud_governance.storage import FileStore
from tests.test_archive import MemoryStore
from tests.test_policy_integrity import storage_report


def source(store):
    snapshot, report = storage_report('NonCompliant')
    manifest = save_run(store, snapshot, report)
    return load_run(store, manifest['run_id'])


class EvidenceReportTests(unittest.TestCase):
    def test_full_view_retains_positive_negative_unknown_and_original_source(self):
        store = MemoryStore()
        saved = source(store)
        original = dict(store.objects)
        result = publish(store, saved['manifest']['run_id'])
        document = load(store, result['report_id'])['report']
        self.assertGreater(document['summary']['counts']['PASS'], 0)
        self.assertEqual(1, document['summary']['counts']['FAIL'])
        self.assertEqual(original, {k: store.objects[k] for k in original})
        self.assertEqual(saved['manifest_sha256'], document['source_manifest_sha256'])

    def test_encryption_selects_checks_and_keeps_unclassified_policy_as_context(self):
        saved = source(MemoryStore())
        view = build(saved, topic=ENCRYPTION)
        self.assertEqual({'resource_rule', 'configuration_predicate'}, {r['kind'] for r in view['records']})
        self.assertEqual(['ST-cmk-key'], [r['reference'] for r in view['records'] if r['kind'] == 'configuration_predicate'])
        self.assertEqual(1, len(view['related_policy_context']))
        self.assertTrue(view['summary']['coverage_incomplete'])
        self.assertEqual('NonCompliant', view['related_policy_context'][0]['compliance_state'])
        configured = copy.deepcopy(ENCRYPTION)
        row = view['related_policy_context'][0]
        configured['policy_references'] = [{'assignment': row['assignment'], 'reference': row['reference']}]
        mapped = build(saved, topic=configured)
        self.assertEqual([], mapped['related_policy_context'])
        self.assertEqual(1, mapped['summary']['finding_count'])

    def test_control_family_and_resource_selection_preserve_empty_coverage(self):
        saved = source(MemoryStore())
        row = saved['snapshot']['resources'][0]
        view = build(saved, families=['SC'], resource_ids=[row['id']])
        self.assertTrue(view['records'])
        self.assertTrue(all(any(c.startswith('SC-') for c in r['controls']) for r in view['records']))
        empty = build(saved, controls=['PE-3'])
        self.assertEqual(0, empty['summary']['record_count'])
        self.assertEqual([row['id'].lower()], empty['resources_without_selected_evidence'])
        self.assertTrue(empty['summary']['coverage_incomplete'])
        with self.assertRaises(ValueError):
            build(saved, resource_ids=[row['id'] + 'missing'])

    def test_pdf_has_positive_evidence_and_negative_context_without_network(self):
        store = MemoryStore()
        saved = source(store)
        with patch('cloud_governance.collector.Collector.collect', side_effect=AssertionError('No recollection')):
            manifest = publish(store, saved['manifest']['run_id'], topic=ENCRYPTION, pdf=True)
        pdf = PdfReader(BytesIO(store.read(manifest['objects']['report.pdf']['key'])))
        text = '\n'.join(p.extract_text() for p in pdf.pages)
        for expected in ('Encryption at rest', 'PASS', 'NonCompliant', 'SYNTHETIC EVIDENCE', 'Observations', 'Criterion'):
            self.assertIn(expected, text)

    def test_historical_view_is_verified_and_not_rebuilt(self):
        store = MemoryStore()
        saved = source(store)
        manifest = publish(store, saved['manifest']['run_id'], topic=ENCRYPTION)
        with patch('cloud_governance.evidence_report.build', side_effect=AssertionError('No rebuild')):
            self.assertEqual('Encryption at rest', load(store, manifest['report_id'])['report']['title'])
        store.objects[manifest['objects']['report.json']['key']] += b' '
        with self.assertRaises(ValueError):
            load(store, manifest['report_id'])

    def test_cli_publishes_successful_evidence_even_when_findings_exist(self):
        with tempfile.TemporaryDirectory() as folder:
            saved = source(FileStore(folder))
            with patch('sys.stdout', new_callable=StringIO) as out:
                code = main(['evidence-report', '--store', folder, '--run-id', saved['manifest']['run_id'], '--family', 'CM'])
            self.assertEqual(0, code)
            manifest = json.loads(out.getvalue())
            self.assertEqual('complete', manifest['state'])
            self.assertGreater(load(FileStore(folder), manifest['report_id'])['report']['summary']['finding_count'], 0)

    def test_failed_publication_stays_unreadable(self):
        store = MemoryStore()
        saved = source(store)
        store.fail_suffix = '/report.md'
        with self.assertRaises(OSError):
            publish(store, saved['manifest']['run_id'])
        report_id = next(k.split('/')[1] for k in store.objects if k.startswith('evidence-reports/'))
        with self.assertRaises(ValueError):
            load(store, report_id)
