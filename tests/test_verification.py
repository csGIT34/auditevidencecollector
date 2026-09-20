from cloud_governance import report_model
import copy
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cloud_governance.assessment import assess
from cloud_governance.catalog import RULES
from cloud_governance.report import markdown
from cloud_governance.snapshot import validate_snapshot
from cloud_governance.verification import direct_commands
from tests.helpers import SUB, Scenario, resource


class VerificationTests(unittest.TestCase):
    def scenario(self, row):
        s = Scenario([row]); s.run()
        return s

    def command(self, s, row, kind):
        return next(c for c in s.result(row)['verification_commands'] if c['kind'] == kind)

    def test_storage_exact_url_projection_and_documented_interpretation(self):
        row=resource('Microsoft.Storage/storageAccounts','store',{'encryption':{'keySource':'Microsoft.Storage'}})
        s=self.scenario(row); c=self.command(s,row,'resource_get')
        self.assertEqual('https://management.azure.com/subscriptions/'+SUB+'/resourceGroups/audit-demo/providers/Microsoft.Storage/storageAccounts/store?api-version=2023-05-01',c['url'])
        self.assertIn('properties."encryption"."keySource"',c['query'])
        self.assertEqual('Microsoft.Storage',c['expected_fields']['properties.encryption.keySource'])
        self.assertIn('not cryptographic proof',c['interpretation'])
        self.assertTrue(c['sources'])

    def test_sql_and_managed_instance_tde_use_actual_endpoint(self):
        for kind in ('Microsoft.Sql/servers/databases','Microsoft.Sql/managedInstances/databases'):
            row=resource(kind,'sql/db'); s=Scenario([row]).tde(row,'Disabled'); s.run()
            c=self.command(s,row,'tde_get')
            self.assertEqual('https://management.azure.com'+row['id']+'/transparentDataEncryption/current?api-version=2023-08-01',c['url'])
            self.assertEqual('{"id": id, "state": properties.state}',c['query'])
            self.assertEqual('Disabled',c['expected_fields']['properties.state'])
            self.assertIn('Disabled fails',c['interpretation'])

    def test_synapse_uses_status_not_sql_state(self):
        row=resource('Microsoft.Synapse/workspaces/sqlPools','ws/pool'); s=Scenario([row]).tde(row); s.run()
        c=self.command(s,row,'tde_get')
        self.assertEqual('https://management.azure.com'+row['id']+'/transparentDataEncryption/current?api-version=2021-06-01',c['url'])
        self.assertEqual('{"id": id, "status": properties.status}',c['query'])

    def test_sql_parent_has_child_list_and_child_tde_commands(self):
        server=resource('Microsoft.Sql/servers','sql'); db=resource('Microsoft.Sql/servers/databases','sql/db')
        s=Scenario([server]).children(server,'databases',[db]).tde(db); s.run()
        listing=self.command(s,server,'list_databases')
        self.assertEqual('https://management.azure.com'+server['id']+'/databases?api-version=2023-08-01',listing['url'])
        self.assertTrue(listing['paginated']); self.assertIn('more_pages',listing['query'])
        tde=self.command(s,server,'tde_get')
        self.assertEqual(db['id'],tde['resource_id']); self.assertEqual('databases',tde['relation'])
        self.assertIn('Traverse every page',listing['interpretation'])

    def test_master_has_no_fabricated_tde_read(self):
        row=resource('Microsoft.Sql/servers/databases','sql/master'); s=self.scenario(row)
        self.assertNotIn('tde_get',[c['kind'] for c in s.result(row)['verification_commands']])

    def test_unsupported_and_network_get_inventory_only(self):
        for kind in ('MongoDB.Atlas/organizations','Microsoft.Network/virtualNetworks'):
            row=resource(kind); s=self.scenario(row); commands=s.result(row)['verification_commands']
            self.assertEqual(['inventory_lookup'],[c['kind'] for c in commands])
            self.assertEqual('https://management.azure.com/subscriptions/'+SUB+'/resources?api-version=2021-04-01',commands[0]['url'])
            self.assertIn('Identity only',commands[0]['interpretation'])
            self.assertIn('not a PASS',commands[0]['interpretation'])

    def test_denied_read_keeps_error_and_offers_only_known_read(self):
        row=resource('Microsoft.Storage/storageAccounts'); s=Scenario([row])
        url=next(u for u in s.responses if row['id'] in u)
        s.responses[url]={'fixture_error':403}; s.run()
        self.assertEqual('ERROR',s.result(row)['result'])
        self.assertEqual(url,self.command(s,row,'resource_get')['url'])
        self.assertIn('Saved result: ERROR',s.result(row)['verification_notes'][0])

    def test_unresolved_dependency_does_not_guess_api(self):
        workspace=resource('Microsoft.OperationalInsights/workspaces','missing')
        app=resource('Microsoft.Insights/components','app',{'WorkspaceResourceId':workspace['id']})
        s=self.scenario(app)
        self.assertEqual('UNKNOWN',s.result(app)['result'])
        self.assertTrue(all(c['resource_id']==app['id'] for c in s.result(app)['verification_commands']))
        self.assertTrue(any('no configuration command is fabricated' in n for n in s.result(app)['verification_notes']))

    def test_resolved_dependency_and_eventhub_namespace_commands(self):
        storage=resource('Microsoft.Storage/storageAccounts','store'); ns=resource('Microsoft.EventHub/namespaces','events')
        hub=resource('Microsoft.EventHub/namespaces/eventhubs','events/hub',{'captureDescription':{'enabled':True,'destination':{'properties':{'storageAccountResourceId':storage['id']}}}})
        s=Scenario([ns,storage]).children(ns,'eventhubs',[hub]); s.run()
        commands=s.result(hub)['verification_commands']
        self.assertTrue(any(c['resource_id']==ns['id'] and c['relation']=='owning_namespace' for c in commands))
        self.assertTrue(any(c['resource_id']==storage['id'] and c['relation']=='capture_storage' for c in commands))
        self.assertTrue(all(c['url'] in s.transport.calls for c in commands))

    def test_recorded_api_used_after_rule_catalog_changes(self):
        row=resource('Microsoft.Storage/storageAccounts'); s=self.scenario(row)
        record=s.snapshot['resources'][0]
        record['api_version']='2022-09-01'
        c=direct_commands(record,'azure_live')[0]
        self.assertTrue(c['url'].endswith('api-version=2022-09-01'))
        self.assertFalse(c['synthetic'])

    def test_unsafe_resource_ids_paths_and_api_versions_rejected(self):
        row=resource('Microsoft.Storage/storageAccounts'); s=self.scenario(row); original=s.snapshot['resources'][0]
        for suffix in ("'; echo BAD",'$(echo BAD)','`echo BAD`',';echo BAD','\nBAD','?sig=BAD','/../bad'):
            bad=copy.deepcopy(original); bad['id']+=suffix
            with self.subTest(suffix=suffix), self.assertRaises(ValueError): direct_commands(bad,'azure_live')
        for version in ('2023-05-01;echo BAD', '2023-05-01&access_token=BAD','2023-99-99',None, ['2023-05-01']):
            bad=copy.deepcopy(s.snapshot); bad['resources'][0]['api_version']=version
            with self.assertRaises(ValueError): validate_snapshot(bad)
        bad=copy.deepcopy(s.snapshot); bad['resources'][0]['request_path']=row['id']+'/listKeys'
        with self.assertRaises(ValueError): validate_snapshot(bad)
        with self.assertRaises(ValueError): direct_commands(bad['resources'][0],'azure_live')

    def test_shell_quoting_preserves_one_invocation_with_spaces_and_literals(self):
        row=resource('Microsoft.NewService/dataStores','name (test)',group='group with spaces')
        s=self.scenario(row); c=s.result(row)['verification_commands'][0]
        self.assertEqual(c['argv'],shlex.split(c['command']))
        with tempfile.TemporaryDirectory() as tmp:
            fake=Path(tmp)/'az'
            fake.write_text('#!'+sys.executable+'\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
            fake.chmod(0o700)
            env={**os.environ,'PATH':tmp,'PYTHONDONTWRITEBYTECODE':'1'}
            proc=subprocess.run(['/bin/sh','-c',c['command']],env=env,capture_output=True,text=True,check=True)
            self.assertEqual(c['argv'][1:],json.loads(proc.stdout)); self.assertEqual('',proc.stderr)

    def test_all_generated_commands_are_get_only_and_collector_urls(self):
        fixture=json.loads((Path(__file__).resolve().parents[1]/'examples/demo-fixture.json').read_text())
        from cloud_governance.collector import Collector, FixtureTransport
        transport=FixtureTransport(fixture['responses']); snapshot=Collector(transport,mode='offline_fixture').collect()
        with patch('subprocess.run',side_effect=AssertionError('Rendering must not execute commands')):
            report=assess(snapshot); md=markdown(report)
        for row in report_model.resource_results(report):
            self.assertTrue(row['verification_commands'])
            for c in row['verification_commands']:
                self.assertTrue(c['synthetic']); self.assertEqual(c['argv'],shlex.split(c['command']))
                self.assertEqual(['az','rest','--method','get'],c['argv'][:4])
                self.assertIn(c['url'],transport.calls); self.assertIn(c['command'],md)
                self.assertFalse(any(v in c['url'].lower() for v in ('listkeys','listsecrets','appsettings','access_token','sig=')))
                self.assertNotIn('--headers',c['argv']); self.assertNotIn('--body',c['argv'])
                self.assertNotIn('--debug',c['argv'])
        self.assertIn('SYNTHETIC EXAMPLE — DO NOT RUN',md)
        self.assertIn('CURRENT state, not historical proof',md)
        self.assertIn('metadata read rights',md)

    def test_projections_exclude_app_secrets_connection_strings_and_sas(self):
        rows=[resource('Microsoft.Web/sites','app'),resource('Microsoft.Cache/Redis','cache'),
              resource('Microsoft.Synapse/workspaces','ws',{'defaultDataLakeStorage':{'accountUrl':'https://store.blob.core.windows.net/?sig=SECRET'}})]
        s=Scenario(rows); s.run()
        commands=json.dumps([r['verification_commands'] for r in report_model.resource_results(s.report)])
        for forbidden in ('appSettings','connectionString','defaultDataLakeStorage.accountUrl','sig=SECRET','administratorLoginPassword'):
            self.assertNotIn(forbidden,commands)
        redis=s.result(rows[1])['verification_commands'][0]['query']
        self.assertIn('"rdb-backup-enabled"',redis)
        self.assertNotIn('rdb-storage-connection-string',redis)

    def test_live_context_is_explicit_without_running_live(self):
        row=resource('Microsoft.Storage/storageAccounts'); s=self.scenario(row)
        s.snapshot['mode']='azure_live'; report=assess(s.snapshot); md=markdown(report)
        self.assertFalse(report_model.resource_results(report)[0]['verification_commands'][0]['synthetic'])
        self.assertIn('CURRENT-STATE READ — requires authorized sign-in',md)


try:
    import jmespath
except ImportError:
    jmespath = None


@unittest.skipUnless(jmespath, 'Optional offline projection validation needs Azure CLI\'s installed jmespath package')
class ProjectionTests(unittest.TestCase):
    def test_all_demo_projections_parse_and_exclude_sensitive_payload_fields(self):
        from cloud_governance.collector import Collector, FixtureTransport
        fixture=json.loads((Path(__file__).resolve().parents[1]/'examples/demo-fixture.json').read_text())
        transport=FixtureTransport(fixture['responses'])
        report=assess(Collector(transport,mode='offline_fixture').collect())
        for row in report_model.resource_results(report):
            for c in row['verification_commands']:
                with self.subTest(kind=c['kind'],resource=c['resource_id']):
                    raw=copy.deepcopy(fixture['responses'][c['url']])
                    raw['accessToken']='DO-NOT-PRINT'
                    props=raw.setdefault('properties',{})
                    props.update({'administratorLoginPassword':'DO-NOT-PRINT','connectionString':'DO-NOT-PRINT',
                                  'siteConfig':{'appSettings':[{'name':'password','value':'DO-NOT-PRINT'}]},
                                  'configuration':{'secrets':[{'name':'password','value':'DO-NOT-PRINT'}]}})
                    actual=jmespath.search(c['query'],raw)
                    self.assertIsInstance(actual,dict)
                    self.assertNotIn('DO-NOT-PRINT',json.dumps(actual))
                    if c['kind']=='tde_get':
                        field='status' if '/Microsoft.Synapse/' in c['url'] else 'state'
                        self.assertEqual(raw['properties'].get(field),actual[field])
                    if c['paginated']:
                        self.assertIs(type(actual['more_pages']),bool)
                    if c['resource_id'].endswith('/registries/registry'):
                        self.assertEqual('disabled',actual['encryption.status'])
