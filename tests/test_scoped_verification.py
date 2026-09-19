import json
import unittest
from unittest.mock import patch

from azure_at_rest.archive import load_run, publish_pdf, save_run
from azure_at_rest.collector import Collector, FixtureTransport, INVENTORY_API, endpoint
from azure_at_rest.verification import direct_commands
from azure_at_rest.workflow import assess_snapshot
from tests.helpers import SUB, resource
from tests.test_archive import MemoryStore


class ScopedVerificationTests(unittest.TestCase):
    def collected(self, scoped=True):
        rows = [resource('Microsoft.ManagedIdentity/userAssignedIdentities', 'identity'),
                resource('Microsoft.Web/serverfarms', 'plan')]
        path = f'/subscriptions/{SUB}' + ('/resourceGroups/audit-demo' if scoped else '') + '/resources'
        transport = FixtureTransport({endpoint(path, INVENTORY_API): {'value': rows}})
        snapshot = Collector(transport, mode='azure_live').collect([SUB], resource_group='audit-demo' if scoped else None)
        return snapshot, transport

    def test_saved_group_limits_inventory_verification_and_preserves_unscoped_behavior(self):
        for scoped in (True, False):
            with self.subTest(scoped=scoped):
                snapshot, transport = self.collected(scoped)
                report = assess_snapshot(snapshot)
                for row in report['results']:
                    commands = row['verification_commands']
                    self.assertEqual(['inventory_lookup'], [c['kind'] for c in commands])
                    self.assertEqual(transport.calls[:1], [c['url'] for c in commands])  # Legacy encryption lookup; configuration reads are separate.
                    self.assertTrue(all('/subscriptions/'+SUB+'/' in u for u in transport.calls))
                    if scoped:
                        self.assertIn('/resourceGroups/audit-demo/resources?', commands[0]['url'])
                        self.assertIn('recorded resource-group', commands[0]['verifies'])
                self.assertNotIn('CLI identity', ' '.join(report['limitations']))
                self.assertIn('scopes recorded in this report', ' '.join(report['limitations']))

    def test_scoped_commands_reject_a_different_or_invalid_group(self):
        snapshot, _ = self.collected()
        for record in snapshot['resources']:
            for group in ('other-group', '../audit-demo', ''):
                with self.subTest(group=group), self.assertRaises(ValueError):
                    direct_commands(record, 'azure_live', resource_group=group)

    def test_historical_scoped_archive_keeps_original_commands_and_bytes(self):
        snapshot, _ = self.collected()
        old_report = assess_snapshot(snapshot)
        # Reproduce the historical report's wider verification suggestions, without executing them.
        for row, record in zip(old_report['results'], snapshot['resources']):
            row['verification_commands'] = direct_commands(record, 'azure_live')
        store = MemoryStore()
        run = save_run(store, snapshot, old_report)
        original = dict(store.objects)
        with patch('azure_at_rest.verification.inventory_command', side_effect=AssertionError('Historical commands must remain frozen')):
            publication = publish_pdf(store, run['run_id'])
            saved = load_run(store, run['run_id'])
        self.assertEqual(old_report, saved['assessment'])
        self.assertEqual(original, {k: store.objects[k] for k in original})
        self.assertEqual('complete', publication['state'])
        self.assertTrue(all('/subscriptions/'+SUB+'/resources?' in r['verification_commands'][0]['url'] for r in saved['assessment']['results']))
