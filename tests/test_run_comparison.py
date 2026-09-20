import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from cloud_governance.archive import save_run, load_run
from cloud_governance.cli import main
from cloud_governance.run_comparison import compare, publish, load
from cloud_governance.storage import FileStore
from cloud_governance.workflow import assess_snapshot
from tests.test_archive import MemoryStore
from tests.test_controls import fixture, collect


class SavedRunComparisonTests(unittest.TestCase):
    def setUp(self):
        self.responses, self.policy = fixture()
        self.snapshot = collect(self.responses)
        self.store = MemoryStore()
        self.before = self.save(self.snapshot, self.policy)

    def save(self, snapshot, policy):
        return save_run(self.store, snapshot, assess_snapshot(snapshot, criteria=policy))['run_id']

    def changed_row(self, report, check='ST-https'):
        return next(row for row in report['checks'] if row['check_id'] == check)

    def test_identical_facts_different_collection_time_are_unchanged(self):
        after_snapshot = copy.deepcopy(self.snapshot)
        for row in after_snapshot['resources']:
            row['collected_at'] = '2026-09-19T20:00:00+00:00'
        after = self.save(after_snapshot, self.policy)
        report = compare(load_run(self.store, self.before), load_run(self.store, after))
        self.assertEqual(set(report['counts']), {'UNCHANGED'})
        self.assertTrue(report['same_declared_scope'])

    def test_criteria_change_is_distinct_from_observation_change(self):
        policy = copy.deepcopy(self.policy)
        policy['checks']['ST-https']['value'] = not policy['checks']['ST-https']['value']
        after = self.save(self.snapshot, policy)
        row = self.changed_row(compare(load_run(self.store, self.before), load_run(self.store, after)))
        self.assertEqual(row['changes'], ['CRITERIA_OR_RULE_CHANGED', 'RESULT_CHANGED'])
        self.assertEqual(row['before']['observation'], row['after']['observation'])

    def test_missing_and_failed_evidence_are_not_remediation(self):
        snapshot = copy.deepcopy(self.snapshot)
        target = next(r for r in snapshot['resources'] if 'ST-https' in r.get('configuration', {}))
        target['configuration']['ST-https'] = {'state': 'missing'}
        removed = snapshot['resources'].pop(0)['id']
        after = self.save(snapshot, self.policy)
        report = compare(load_run(self.store, self.before), load_run(self.store, after))
        self.assertIn('EVIDENCE_LOST', self.changed_row(report)['changes'])
        self.assertIn(removed.lower(), report['no_longer_observed_resources'])
        self.assertTrue(any('MISSING_OBSERVATION' in row['changes'] for row in report['checks']))

    def test_scope_difference_is_explicit(self):
        before = load_run(self.store, self.before)
        after = copy.deepcopy(before)
        after['snapshot']['inventory']['subscriptions'][0]['resource_group'] = 'different'
        self.assertFalse(compare(before, after)['same_declared_scope'])

    def test_publication_preserves_sources_and_historical_load_does_not_recompute(self):
        originals = dict(self.store.objects)
        result = publish(self.store, self.before, self.before)
        with patch('cloud_governance.run_comparison.compare', side_effect=AssertionError('recomputed')):
            saved = load(self.store, result['comparison_id'])
        self.assertEqual(saved['report']['counts'].keys(), {'UNCHANGED'})
        for key, value in originals.items():
            self.assertEqual(self.store.objects[key], value)
        key = result['objects']['comparison.json']['key']
        self.store.objects[key] += b' '
        with self.assertRaises(ValueError):
            load(self.store, result['comparison_id'])

    def test_source_tampering_is_rejected(self):
        result = publish(self.store, self.before, self.before)
        key = 'runs/' + self.before + '/snapshot.json'
        self.store.objects[key] += b' '
        with self.assertRaises(ValueError):
            load(self.store, result['comparison_id'])

    def test_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            store = FileStore(directory)
            run = save_run(store, self.snapshot, assess_snapshot(self.snapshot, criteria=self.policy))['run_id']
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(['compare-runs', '--store', directory, '--before', run, '--after', run]), 0)
            identity = json.loads(output.getvalue())['comparison_id']
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(['comparison-show', '--store', directory, '--comparison-id', identity]), 0)
            self.assertIn('Saved run comparison', output.getvalue())

    def test_new_and_old_archive_comparison_and_policy_approval_change(self):
        before = load_run(self.store, self.before)
        legacy = copy.deepcopy(before)
        legacy['assessment'].pop('configuration_assessment')
        result = compare(legacy, before)
        self.assertTrue(any(row['changes']==['NEW_OBSERVATION'] for row in result['checks']))
        policy = copy.deepcopy(self.policy)
        policy['status'] = 'draft'
        after = self.save(self.snapshot, policy)
        result = compare(before, load_run(self.store, after))
        self.assertIn('CRITERIA_OR_RULE_CHANGED', self.changed_row(result)['changes'])

    def test_incomplete_publication_cannot_be_read(self):
        self.store.fail_suffix = '/comparison.md'
        with self.assertRaises(OSError):
            publish(self.store, self.before, self.before)
        intent = next(key for key in self.store.objects if key.startswith('run-comparisons/') and key.endswith('/intent.json'))
        comparison_id = intent.split('/')[1]
        with self.assertRaises(FileNotFoundError):
            load(self.store, comparison_id)
