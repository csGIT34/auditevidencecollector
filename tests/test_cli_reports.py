import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from azure_at_rest.cli import main
from azure_at_rest.assessment import assess
from azure_at_rest.report import exit_code, markdown
from azure_at_rest.snapshot import validate_snapshot
from tests.helpers import Scenario, resource

ROOT = Path(__file__).resolve().parents[1]


class CliReportTests(unittest.TestCase):
    def invoke(self, args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            code = main(args)
        return code, output.getvalue()

    def test_complete_offline_demo_and_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            snapshot = path/'snapshot.json'; report = path/'report.json'; readable = path/'report.md'
            with patch('azure_at_rest.collector.AzureCliCredential.get_token', side_effect=AssertionError('Offline must not authenticate')):
                code, _ = self.invoke(['collect', '--fixture', str(ROOT/'examples/demo-fixture.json'), '--json', str(report), '--report', str(readable), '--snapshot', str(snapshot)])
            self.assertEqual(1, code)
            data = json.loads(report.read_text())
            self.assertEqual(35, data['summary']['resource_count'])
            self.assertEqual({'PASS':22, 'FAIL':3, 'ERROR':1, 'UNKNOWN':7, 'UNSUPPORTED':1, 'NOT_APPLICABLE':1}, data['summary']['counts'])
            self.assertEqual('offline_fixture', data['mode'])
            self.assertEqual(0o600, report.stat().st_mode & 0o777)
            md = readable.read_text()
            for text in ('Coverage incomplete: True', 'Microsoft service documentation', 'SC-28', 'Rule version:', 'Collection errors', 'Unsupported types:'):
                self.assertIn(text, md)
            for result in data['results']:
                self.assertIn(result['id'], md)
                self.assertTrue(result['collected_at'])
                self.assertTrue(result['rule_version'])
            replay = path/'replay.json'
            code, _ = self.invoke(['assess', '--input', str(snapshot), '--json', str(replay), '--report', str(path/'replay.md')])
            self.assertEqual(1, code)
            rerun=json.loads(replay.read_text())
            self.assertEqual(data['summary'], rerun['summary'])
            self.assertEqual(data['snapshot_sha256'], rerun['snapshot_sha256'])
            self.assertTrue(rerun['reassessed_from_snapshot'])

    def test_input_cannot_be_overwritten_or_outputs_collide(self):
        fixture=ROOT/'examples/demo-fixture.json'
        for args in (['collect','--fixture',str(fixture),'--json',str(fixture)], ['collect','--fixture',str(fixture),'--json','same.json','--report','same.json']):
            self.assertEqual(3,self.invoke(args)[0])

    def test_invalid_cli_inputs_never_print_raw_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'input.json'; p.write_text('{"password":"TOP-SECRET"}')
            for args in (['collect','--fixture',str(p)], ['assess','--input',str(p)], ['collect','--subscription','TOP-SECRET']):
                code, output=self.invoke(args)
                self.assertEqual(3,code)
                self.assertNotIn('TOP-SECRET',output)

    def test_exit_codes_do_not_mask_coverage(self):
        passrow=resource('Microsoft.Storage/storageAccounts')
        s=Scenario([passrow]); self.assertEqual(2,exit_code(s.run()))  # Encryption passes; broader criteria/evidence are absent.
        unknown=resource('Microsoft.Web/sites'); s=Scenario([unknown]); self.assertEqual(2,exit_code(s.run()))
        fail=resource('Microsoft.Kusto/clusters',properties={'enableDiskEncryption':False}); s=Scenario([fail]); self.assertEqual(1,exit_code(s.run()))
        s=Scenario([]); self.assertEqual(2,exit_code(s.run()))

    def test_snapshot_validation_rejects_inconsistent_inventory(self):
        s=Scenario([resource('Microsoft.Storage/storageAccounts')]); s.run()
        validate_snapshot(s.snapshot)
        bad=copy.deepcopy(s.snapshot); bad['inventory']['subscriptions'][0]['complete']=False
        with self.assertRaises(ValueError): validate_snapshot(bad)
        bad=copy.deepcopy(s.snapshot); bad['resources'][0]['evidence']['password']='secret'
        with self.assertRaises(ValueError): validate_snapshot(bad)
        bad=copy.deepcopy(s.snapshot); bad['resources'].append(bad['resources'][0])
        with self.assertRaises(ValueError): validate_snapshot(bad)

    def test_subscription_level_resource_identity_is_retained(self):
        row={'id':'/subscriptions/11111111-1111-1111-1111-111111111111/providers/Microsoft.Security/pricings/Default', 'type':'Microsoft.Security/pricings','properties':{}}
        s=Scenario([row]); data=s.run()
        self.assertTrue(data['summary']['inventory_complete'])
        self.assertEqual(1,data['summary']['counts']['UNSUPPORTED'])

    def test_malformed_replay_cannot_inject_state_or_metadata(self):
        s=Scenario([resource('Microsoft.Storage/storageAccounts')]); s.run()
        for mutate in (
            lambda d: d['resources'][0]['evidence'].update(provisioningState=123),
            lambda d: d['inventory'].update(password='TOP-SECRET'),
            lambda d: d['inventory']['subscriptions'][0].update(password='TOP-SECRET'),
            lambda d: d['resources'][0]['evidence'].update({'encryption.keySource':'TOP-SECRET'}),
        ):
            bad=copy.deepcopy(s.snapshot); mutate(bad)
            with self.assertRaises(ValueError): validate_snapshot(bad)
