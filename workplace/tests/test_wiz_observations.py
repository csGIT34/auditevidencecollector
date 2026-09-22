import copy
import json
from pathlib import Path
import unittest

from cloud_governance.archive import encode
from cloud_governance.evidence_report import ENCRYPTION, load, publish
from cloud_governance.wiz import import_export, load_export, validate_export
from tests.test_archive import MemoryStore
from tests.test_evidence_report import source

ROOT = Path(__file__).resolve().parents[1]


def example():
    return json.loads((ROOT / 'examples/wiz/observations-export.json').read_text())


class WizObservationTests(unittest.TestCase):
    def test_v2_retains_positive_negative_observations_and_scans_with_no_issues(self):
        document = example()
        self.assertIs(document, validate_export(document))
        store = MemoryStore()
        saved = source(store)
        imported = import_export(store, encode(document))
        original = dict(store.objects)
        published = publish(store, saved['manifest']['run_id'], wiz_import_id=imported['wiz_import_id'])
        view = load(store, published['report_id'])['report']
        rows = [r for r in view['records'] if r['kind'] == 'wiz_evaluation']
        self.assertEqual({'PASS', 'FAIL'}, {r['result'] for r in rows})
        self.assertTrue(any(r['kind'] == 'wiz_observation' for r in view['records']))
        self.assertEqual(document['scans'], view['wiz_scans'])
        self.assertEqual(original, {k: store.objects[k] for k in original})

    def test_topic_uses_explicit_wiz_rule_map_and_does_not_treat_issues_as_passes(self):
        store = MemoryStore()
        saved = source(store)
        imported = import_export(store, encode(example()))
        topic = {**copy.deepcopy(ENCRYPTION), 'wiz_rules': ['synthetic-encryption']}
        report = publish(store, saved['manifest']['run_id'], topic=topic, wiz_import_id=imported['wiz_import_id'])
        rows = load(store, report['report_id'])['report']['records']
        self.assertEqual(['PASS'], [r['result'] for r in rows if r['kind'] == 'wiz_evaluation'])
        self.assertFalse(any(r['reference'] == 'synthetic-logging' for r in rows))

    def test_bad_native_data_cannot_enter_normalized_contract(self):
        mutations = [lambda d: d['observations'][0]['values'].update(password='SECRET-CANARY'),
                     lambda d: d['evaluations'][0].update(result='RESOLVED'),
                     lambda d: d['evaluations'][0].update(resource_id=None),
                     lambda d: d['evaluations'][0]['observed'].update(encryption_at_rest_enabled='true'),
                     lambda d: d['evaluations'].append(copy.deepcopy(d['evaluations'][0])),
                     lambda d: d['scans'][0].update(evaluated_rules=[]),
                     lambda d: d['scans'][0].update(status='failed'),
                     lambda d: d['scans'][0].update(target_id='latest'),
                     lambda d: d['observations'][0].update(observed_at='2027-01-01T00:00:00Z')]
        for mutate in mutations:
            document = example()
            mutate(document)
            with self.assertRaises(ValueError):
                validate_export(document)

    def test_partial_scan_is_retained_and_reports_missing_coverage(self):
        store = MemoryStore()
        saved = source(store)
        document = example()
        document['scans'][0].update(status='failed', evaluated_rules=[], results_complete=False, result_counts={})
        imported = import_export(store, encode(document))
        published = publish(store, saved['manifest']['run_id'], wiz_import_id=imported['wiz_import_id'])
        view = load(store, published['report_id'])['report']
        self.assertTrue(any('scans failed' in s for s in view['gaps']))
        self.assertEqual('failed', view['wiz_scans'][0]['status'])

    def test_original_v1_import_still_loads_and_corruption_is_detected_in_new_report(self):
        store = MemoryStore()
        saved = source(store)
        original = (ROOT / 'examples/wiz/normalized-export.json').read_bytes()
        imported = import_export(store, original)
        self.assertEqual('1.0', load_export(store, imported['wiz_import_id'])['document']['schema_version'])
        publication = publish(store, saved['manifest']['run_id'], wiz_import_id=imported['wiz_import_id'])
        self.assertTrue(load(store, publication['report_id'])['report']['wiz_source'])
        store.objects[imported['object']['key']] += b' '
        with self.assertRaises(ValueError):
            load(store, publication['report_id'])

    def test_scope_mismatch_is_rejected_before_report_publication(self):
        store = MemoryStore()
        saved = source(store)
        document = example()
        document['source']['scope']['resource_group'] = 'audit-demo'
        imported = import_export(store, encode(document))
        original = dict(store.objects)
        with self.assertRaises(ValueError):
            publish(store, saved['manifest']['run_id'], wiz_import_id=imported['wiz_import_id'])
        self.assertEqual(original, store.objects)
