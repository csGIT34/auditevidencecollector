import copy
import json
from pathlib import Path
import unittest
from azure_at_rest.collector import Collector, FixtureTransport, endpoint, INVENTORY_API
from azure_at_rest.hosting import Settings, ConfigurationError
from azure_at_rest.snapshot import validate_snapshot
from tests.test_hosting import environment

SID='11111111-1111-1111-1111-111111111111'
RG='lab-test'
SCOPE=f'/subscriptions/{SID}/resourceGroups/{RG}'


def resource(group=RG):
    return {'id':f'/subscriptions/{SID}/resourceGroups/{group}/providers/Microsoft.Storage/storageAccounts/teststore',
            'name':'teststore','type':'Microsoft.Storage/storageAccounts','location':'eastus','properties':{'provisioningState':'Succeeded'}}


class ResourceGroupScopeTests(unittest.TestCase):
    def test_scoped_inventory_never_lists_subscription_or_hydrates_outside_group(self):
        from azure_at_rest.catalog import RULES
        row=resource();url=endpoint(SCOPE+'/resources',INVENTORY_API)
        transport=FixtureTransport({url:{'value':[row,resource('unrelated')]},endpoint(row['id'],RULES['microsoft.storage/storageaccounts'].api):row})
        snapshot=Collector(transport).collect([SID],resource_group=RG)
        validate_snapshot(snapshot)
        self.assertEqual([row['id']],[r['id'] for r in snapshot['resources']])
        self.assertFalse(snapshot['inventory']['complete'])
        self.assertEqual(RG,snapshot['inventory']['subscriptions'][0]['resource_group'])
        self.assertEqual(2,len(transport.calls))
        self.assertNotIn(endpoint('/subscriptions/'+SID+'/resources',INVENTORY_API),transport.calls)

    def test_denied_group_is_valid_incomplete_evidence_without_fallback(self):
        url=endpoint(SCOPE+'/resources',INVENTORY_API)
        transport=FixtureTransport({url:{'fixture_error':403}})
        snapshot=Collector(transport).collect([SID],resource_group=RG)
        validate_snapshot(snapshot)
        self.assertFalse(snapshot['inventory']['complete'])
        self.assertEqual([url],transport.calls)
        self.assertEqual(SCOPE,snapshot['errors'][0]['scope'])

    def test_scope_changing_pagination_is_rejected_before_read(self):
        url=endpoint(SCOPE+'/resources',INVENTORY_API)
        transport=FixtureTransport({url:{'value':[],'nextLink':endpoint('/subscriptions/'+SID+'/resources',INVENTORY_API)}})
        snapshot=Collector(transport).collect([SID],resource_group=RG)
        validate_snapshot(snapshot)
        self.assertEqual([url],transport.calls)
        self.assertEqual('pagination_scope_changed',snapshot['errors'][0]['code'])

    def test_explicit_single_subscription_and_portable_name_required(self):
        for subs,rg in [(None,RG),([],RG),([SID,'22222222-2222-2222-2222-222222222222'],RG),([SID],'../other'),([SID],''),([SID],'x?api-version=x')]:
            with self.subTest(subs=subs,rg=rg),self.assertRaises(ValueError):Collector(FixtureTransport({})).collect(subs,resource_group=rg)
        valid={**environment(),'CG_RESOURCE_GROUP':RG}
        self.assertEqual(RG,Settings.parse(valid).resource_group)
        with self.assertRaises(ConfigurationError):Settings.parse({**valid,'CG_RESOURCE_GROUP':'a/b'})

    def test_saved_scope_rejects_out_of_group_rows_and_old_snapshots_still_validate(self):
        fixture=json.loads((Path(__file__).resolve().parents[1]/'examples/demo-fixture.json').read_text())
        old=Collector(FixtureTransport(fixture['responses'])).collect()
        validate_snapshot(old)
        altered=copy.deepcopy(old);altered['inventory']['subscriptions'][0]['resource_group']='different'
        with self.assertRaises(ValueError):validate_snapshot(altered)

    def test_workflow_and_host_pass_scope_through(self):
        from unittest.mock import patch,Mock
        from contextlib import contextmanager
        from azure_at_rest.hosting import execute
        @contextmanager
        def factory(*args):yield Mock(),Mock()
        with patch('azure_at_rest.hosting.verify_tenant'),patch('azure_at_rest.hosting.collect_run',return_value={}) as collect:
            execute('collect',env={**environment(),'CG_RESOURCE_GROUP':RG},factory=factory)
        self.assertEqual(RG,collect.call_args.kwargs['resource_group'])

    def test_scoped_saved_run_pdf_retains_group(self):
        from io import BytesIO
        from pypdf import PdfReader
        from azure_at_rest.workflow import collect_run
        from azure_at_rest.archive import publish_pdf,load_run
        from azure_at_rest.catalog import RULES
        from tests.test_archive import MemoryStore
        row=resource()
        transport=FixtureTransport({endpoint(SCOPE+'/resources',INVENTORY_API):{'value':[row]},endpoint(row['id'],RULES['microsoft.storage/storageaccounts'].api):row})
        store=MemoryStore();run=collect_run(store,transport,[SID],resource_group=RG)
        self.assertEqual(RG,load_run(store,run['run_id'])['snapshot']['inventory']['subscriptions'][0]['resource_group'])
        report=publish_pdf(store,run['run_id'])
        text=''.join(p.extract_text() for p in PdfReader(BytesIO(store.read(report['pdf']['key']))).pages)
        self.assertIn('resource_group',text);self.assertIn(RG,text)

    def test_reused_collector_does_not_carry_resources_across_scopes(self):
        from azure_at_rest.catalog import RULES
        first=resource('first');second=resource(RG)
        transport=FixtureTransport({
            endpoint(f'/subscriptions/{SID}/resourceGroups/first/resources',INVENTORY_API):{'value':[first]},
            endpoint(SCOPE+'/resources',INVENTORY_API):{'value':[second]},
            endpoint(first['id'],RULES['microsoft.storage/storageaccounts'].api):first,
            endpoint(second['id'],RULES['microsoft.storage/storageaccounts'].api):second})
        collector=Collector(transport)
        collector.collect([SID],resource_group='first')
        transport.calls.clear()
        final=collector.collect([SID],resource_group=RG)
        validate_snapshot(final)
        self.assertEqual([second['id']],[r['id'] for r in final['resources']])
        self.assertFalse(any('/first/' in u for u in transport.calls))
