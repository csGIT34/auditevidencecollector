import copy
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from cloud_governance.archive import encode, load_run, save_run
from cloud_governance.cli import main
from cloud_governance.reconciliation import load_comparison, publish_comparison, reconcile
from cloud_governance.storage import FileStore
from cloud_governance.wiz import MAX_INPUT_BYTES, decode, import_export, load_export, validate_export
from tests.test_archive import evidence, MemoryStore
from tests.test_azure_adapters import SUB, TENANT


def document(snapshot):
    observed = snapshot['completed_at']
    rid = snapshot['resources'][0]['id']
    return {'schema_version':'1.0', 'kind':'wiz_evidence',
            'source':{'system':'wiz', 'mode':'synthetic', 'export_id':'synthetic-export-1',
                      'exported_at':observed, 'tenant_id':TENANT, 'mapping_version':'1.0',
                      'scope':{'subscription_ids':[SUB], 'resource_group':None},
                      'inventory_complete':True, 'findings_complete':True},
            'resources':[{'wiz_id':'synthetic-resource-1', 'resource_id':rid, 'observed_at':observed}],
            'findings':[{'finding_id':'synthetic-finding-1', 'resource_id':rid, 'rule_id':'wiz-example-unrelated-rule',
                         'severity':'HIGH', 'status':'OPEN', 'observed_at':observed}]}


def setup(store):
    snapshot, assessment = evidence()
    run = save_run(store, snapshot, assessment)
    exported = document(snapshot)
    imported = import_export(store, encode(exported))
    return run, imported, exported


def compare(store, run, imported, **kwargs):
    saved = load_run(store, run['run_id'])
    params = {'as_of':saved['snapshot']['completed_at'], 'max_age_hours':24, 'max_skew_hours':1, **kwargs}
    return reconcile(saved, load_export(store, imported['wiz_import_id']), **params)


class WizContractTests(unittest.TestCase):
    def setUp(self):
        self.snapshot, _ = evidence()
        self.export = document(self.snapshot)

    def test_committed_example_satisfies_contract_and_documented_enums_match(self):
        from cloud_governance.wiz import SEVERITIES, STATUSES
        root = Path(__file__).resolve().parents[1]
        example = decode((root/'examples/wiz/normalized-export.json').read_bytes())
        validate_export(example)
        schema = json.loads((root/'docs/schemas/wiz-evidence-v1.schema.json').read_text())
        fields = schema['properties']['findings']['items']['properties']
        self.assertEqual(SEVERITIES, set(fields['severity']['enum']))
        self.assertEqual(STATUSES, set(fields['status']['enum']))

    def test_exact_input_bytes_are_preserved_and_imports_do_not_overwrite(self):
        data = json.dumps(self.export, indent=4).encode() + b'\n'
        store = MemoryStore()
        first = import_export(store, data)
        before = dict(store.objects)
        second = import_export(store, data)
        self.assertNotEqual(first['wiz_import_id'], second['wiz_import_id'])
        self.assertEqual(data, store.read(first['object']['key']))
        self.assertEqual(before, {k:store.objects[k] for k in before})
        self.assertEqual(self.export, load_export(store, first['wiz_import_id'])['document'])

    def test_native_payload_unknown_fields_and_secrets_fail_before_writes(self):
        cases = [{'data':{'cloudResources':[]}}, {**self.export, 'token':'SECRET'},
                 {**self.export, 'schema_version':'2.0'}]
        for section, name in [('source', 'client_secret'), ('resources', 'properties'), ('findings', 'description')]:
            doc = copy.deepcopy(self.export)
            target = doc[section] if section == 'source' else doc[section][0]
            target[name] = 'SECRET'
            cases.append(doc)
        for doc in cases:
            store = MemoryStore()
            with self.subTest(doc=doc), self.assertRaises(ValueError):import_export(store, encode(doc))
            self.assertEqual({}, store.objects)

    def test_ambiguous_json_and_oversized_inputs_are_rejected(self):
        for data in (b'{"x":1,"x":2}', b'{"x":NaN}', b'x' * (MAX_INPUT_BYTES + 1)):
            with self.assertRaises(ValueError):decode(data)

    def test_scope_timestamp_identity_enums_and_completeness_are_strict(self):
        mutations = [
            lambda d:d['source'].update(tenant_id='bad'),
            lambda d:d['source'].update(inventory_complete='true'),
            lambda d:d['source'].update(mapping_version='unknown'),
            lambda d:d['source']['scope'].update(subscription_ids=[TENANT]),
            lambda d:d['source']['scope'].update(subscription_ids=[SUB, SUB]),
            lambda d:d['source']['scope'].update(resource_group='other'),
            lambda d:d['resources'][0].update(resource_id='https://example.invalid/SECRET'),
            lambda d:d['resources'][0].update(observed_at='2026-01-01'),
            lambda d:d['resources'][0].update(observed_at='2999-01-01T00:00:00Z'),
            lambda d:d['findings'][0].update(status='PASS'),
            lambda d:d['findings'][0].update(severity='invented'),
            lambda d:d['findings'][0].update(resource_id=d['findings'][0]['resource_id']+'other'),
            lambda d:d['findings'][0].update(rule_id='line\nSECRET'),
            lambda d:d['resources'].append({**d['resources'][0], 'wiz_id':'another', 'resource_id':d['resources'][0]['resource_id'].upper()}),
            lambda d:d['resources'].append({**d['resources'][0], 'resource_id':d['resources'][0]['resource_id']+'2'}),
            lambda d:d['findings'].append(dict(d['findings'][0])),
        ]
        for mutate in mutations:
            doc = copy.deepcopy(self.export);mutate(doc)
            with self.assertRaises((ValueError, TypeError)):validate_export(doc)

    def test_corrupt_incomplete_failed_and_cross_import_archives_fail_closed(self):
        for mode in ('corrupt', 'missing', 'failed', 'cross_import'):
            store = MemoryStore();manifest = import_export(store, encode(self.export))
            key = manifest['object']['key'];prefix = key.rsplit('/', 1)[0]
            if mode == 'corrupt':store.objects[key] += b' '
            if mode == 'missing':del store.objects[key]
            if mode == 'failed':store.objects[prefix+'/failure.json'] = b'{}'
            if mode == 'cross_import':
                manifest['object']['key'] = 'external/wiz/w-'+'b'*32+'/export.json'
                store.objects[prefix+'/manifest.json'] = encode(manifest)
            with self.assertRaises((ValueError, KeyError, FileNotFoundError)):load_export(store, manifest['wiz_import_id'])

    def test_partial_import_never_reports_completion(self):
        for suffix in ('export.json', 'manifest.json'):
            store = MemoryStore(fail_suffix=suffix)
            with self.assertRaises(OSError):import_export(store, encode(self.export))
            self.assertTrue(any(k.endswith('/failure.json') for k in store.objects))
            self.assertFalse(any(k.endswith('/manifest.json') for k in store.objects))


class WizReconciliationTests(unittest.TestCase):
    def test_open_wiz_finding_does_not_replace_saved_azure_pass(self):
        store = MemoryStore();run, imported, _ = setup(store)
        original = dict(store.objects)
        with patch('cloud_governance.assessment.assess', side_effect=AssertionError('no reassessment')), patch('cloud_governance.collector.Collector.collect', side_effect=AssertionError('no recollection')):
            result = compare(store, run, imported)
        self.assertEqual({'BOTH':1, 'AZURE_ONLY':0, 'WIZ_ONLY':0}, result['presence_counts'])
        self.assertEqual('PASS', result['resources'][0]['azure']['result'])
        self.assertEqual('OPEN', result['resources'][0]['wiz_findings'][0]['status'])
        self.assertIn('azure_tenant_not_recorded', result['gaps'])
        self.assertEqual(original, store.objects)

    def test_case_insensitive_identity_and_unmatched_rows(self):
        store = MemoryStore();run, _, exported = setup(store)
        exported['resources'][0]['resource_id'] = exported['resources'][0]['resource_id'].upper()
        imported = import_export(store, encode(exported))
        self.assertEqual(1, compare(store, run, imported)['presence_counts']['BOTH'])
        exported['resources'][0]['resource_id'] += '2'
        exported['findings'][0]['resource_id'] = exported['resources'][0]['resource_id']
        imported = import_export(store, encode(exported))
        result = compare(store, run, imported)
        self.assertEqual({'BOTH':0, 'AZURE_ONLY':1, 'WIZ_ONLY':1}, result['presence_counts'])
        self.assertTrue(all('inventory_difference_requires_review' in r['gaps'] for r in result['resources']))

    def test_partial_inventory_and_absent_findings_never_imply_pass(self):
        store = MemoryStore();run, _, exported = setup(store)
        exported['source'].update(inventory_complete=False, findings_complete=False)
        exported['findings'] = []
        result = compare(store, run, import_export(store, encode(exported)))
        self.assertEqual('REVIEW_REQUIRED', result['state'])
        self.assertTrue({'wiz_inventory_incomplete', 'wiz_findings_incomplete'} <= set(result['gaps']))
        self.assertEqual([], result['resources'][0]['wiz_findings'])
        from cloud_governance.reconciliation import markdown
        self.assertIn('None supplied; no PASS implied', markdown(result))

    def test_freshness_and_time_skew_include_findings(self):
        store = MemoryStore();run, _, exported = setup(store)
        current = datetime.fromisoformat(exported['source']['exported_at'])
        exported['resources'][0]['observed_at'] = (current - timedelta(hours=3)).isoformat()
        exported['findings'][0]['observed_at'] = (current - timedelta(hours=30)).isoformat()
        result = compare(store, run, import_export(store, encode(exported)))
        self.assertTrue({'observation_time_skew','wiz_finding_stale','finding_time_skew'} <= set(result['resources'][0]['gaps']))
        later = compare(store, run, import_export(store, encode(exported)), as_of=(current+timedelta(hours=25)).isoformat())
        self.assertIn('azure_observation_stale', later['resources'][0]['gaps'])
        self.assertIn('wiz_observation_stale', later['resources'][0]['gaps'])
        with self.assertRaises(ValueError):compare(store, run, import_export(store, encode(exported)), as_of=(current-timedelta(seconds=1)).isoformat())
        for value in (float('nan'), float('inf'), -1):
            with self.assertRaises(ValueError):compare(store, run, import_export(store, encode(exported)), max_skew_hours=value)

    def test_mismatched_scope_tenant_and_synthetic_boundary_are_rejected(self):
        store = MemoryStore();run, imported, _ = setup(store)
        saved = load_run(store, run['run_id']);external = load_export(store, imported['wiz_import_id'])
        variants = []
        changed = copy.deepcopy(external);changed['document']['source']['scope']['resource_group']='audit-demo';variants.append((saved, changed))
        changed = copy.deepcopy(external);changed['document']['source']['scope']['subscription_ids']=[TENANT];variants.append((saved, changed))
        changed = copy.deepcopy(external);changed['document']['source']['mode']='operator_export';variants.append((saved, changed))
        changed = copy.deepcopy(saved);changed['context']['execution_provenance']={'tenant_id':SUB};variants.append((changed, external))
        for direct, wiz in variants:
            with self.assertRaises(ValueError):reconcile(direct, wiz, as_of=saved['snapshot']['completed_at'], max_age_hours=24, max_skew_hours=1)

    def test_multiple_comparisons_preserve_originals_and_have_distinct_ids(self):
        store = MemoryStore();run, imported, exported = setup(store);before = dict(store.objects)
        params = {'as_of':exported['source']['exported_at'], 'max_age_hours':24, 'max_skew_hours':1}
        a = publish_comparison(store, run['run_id'], imported['wiz_import_id'], **params)
        b = publish_comparison(store, run['run_id'], imported['wiz_import_id'], **params)
        self.assertNotEqual(a['comparison_id'], b['comparison_id'])
        self.assertEqual(before, {k:store.objects[k] for k in before})
        text = store.read(a['objects']['comparison.md']['key']).decode()
        self.assertIn('synthetic-finding-1', text)
        self.assertIn('No finding does not mean PASS', text)
        self.assertIn(exported['source']['exported_at'], text)
        self.assertIn(a['source_run_manifest_sha256'], text)

    def test_common_blob_store_supports_import_comparison_and_verified_replay(self):
        from cloud_governance.azure_adapters import BlobStore
        from tests.test_azure_adapters import FakeContainer, URL
        store = BlobStore(URL, 'evidence', None, 'fixture', client=FakeContainer())
        run, imported, exported = setup(store)
        manifest = publish_comparison(store, run['run_id'], imported['wiz_import_id'], as_of=exported['source']['exported_at'], max_age_hours=24, max_skew_hours=1)
        self.assertEqual(1, load_comparison(store, manifest['comparison_id'])['report']['finding_count'])
        self.assertEqual('complete', load_run(store, run['run_id'])['manifest']['state'])

    def test_saved_comparison_verifies_both_sources_and_rejects_tampering(self):
        store = MemoryStore();run, imported, exported = setup(store)
        manifest = publish_comparison(store, run['run_id'], imported['wiz_import_id'], as_of=exported['source']['exported_at'], max_age_hours=24, max_skew_hours=1)
        with patch('cloud_governance.reconciliation.reconcile', side_effect=AssertionError('no recomputation')):
            self.assertEqual('REVIEW_REQUIRED', load_comparison(store, manifest['comparison_id'])['report']['state'])
        original = dict(store.objects)
        for key in (manifest['objects']['comparison.md']['key'], imported['object']['key'], run['objects']['snapshot']['key']):
            store.objects = dict(original);store.objects[key] += b'corrupt'
            with self.assertRaises(ValueError):load_comparison(store, manifest['comparison_id'])
        store.objects = dict(original)
        store.objects['comparisons/'+manifest['comparison_id']+'/failure.json'] = b'{}'
        with self.assertRaises(ValueError):load_comparison(store, manifest['comparison_id'])

    def test_failed_comparison_publication_preserves_sources(self):
        for suffix in ('comparison.json', 'comparison.md', 'manifest.json'):
            store = MemoryStore();run, imported, exported = setup(store);before = dict(store.objects)
            store.fail_suffix = suffix
            with self.assertRaises(OSError):publish_comparison(store, run['run_id'], imported['wiz_import_id'], as_of=exported['source']['exported_at'], max_age_hours=24, max_skew_hours=1)
            self.assertEqual(before, {k:store.objects[k] for k in before})
            keys = [k for k in store.objects if k.startswith('comparisons/')]
            self.assertTrue(any(k.endswith('/failure.json') for k in keys))
            self.assertFalse(any(k.endswith('/manifest.json') for k in keys))

    def test_cli_roundtrip_and_sanitized_rejection_make_no_network_calls(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);store = FileStore(root/'store')
            snapshot, assessment = evidence();run = save_run(store, snapshot, assessment)
            source = root/'wiz.json';source.write_bytes(encode(document(snapshot)))
            output = io.StringIO()
            with patch('socket.create_connection', side_effect=AssertionError('no network')), redirect_stdout(output):
                self.assertEqual(0, main(['wiz-import','--input',str(source),'--store',str(store.root)]))
                imported = json.loads(output.getvalue());output.seek(0);output.truncate()
                self.assertEqual(0, main(['wiz-reconcile','--store',str(store.root),'--run-id',run['run_id'],
                                          '--wiz-import-id',imported['wiz_import_id'],'--as-of',snapshot['completed_at'],
                                          '--max-age-hours','24','--max-skew-hours','1']))
            manifest = json.loads(output.getvalue())
            self.assertEqual('complete', manifest['state'])
            with redirect_stdout(io.StringIO()) as shown:
                self.assertEqual(0, main(['wiz-show','--store',str(store.root),'--comparison-id',manifest['comparison_id']]))
            self.assertIn('No finding does not mean PASS', shown.getvalue())
            source.write_text('{"token":"TOP-SECRET"}')
            error = io.StringIO()
            with redirect_stderr(error):self.assertEqual(3, main(['wiz-import','--input',str(source),'--store',str(store.root)]))
            self.assertNotIn('TOP-SECRET', error.getvalue())
