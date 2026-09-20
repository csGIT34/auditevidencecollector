import copy
import json
import unittest
from azure_at_rest.catalog import RULES
from azure_at_rest.collector import Collector,FixtureTransport,INVENTORY_API,endpoint
from azure_at_rest.snapshot import validate_snapshot
from azure_at_rest.assessment import assess
from tests.helpers import SUB,SUB2,Scenario,resource


class DiskDependencyTests(unittest.TestCase):
    def scenario(self,kind='Microsoft.Compute/virtualMachines',disk=None):
        disk=disk or resource('Microsoft.Compute/disks','backing',{'encryption':{'type':'EncryptionAtRestWithPlatformKey'}})
        profile={'osDisk':{'managedDisk':{'id':disk['id']}},'dataDisks':[{'managedDisk':{'id':disk['id']}}]}
        props={'storageProfile':profile} if kind.endswith('virtualMachines') else {'virtualMachineProfile':{'storageProfile':profile}}
        vm=resource(kind,'workload',props);scenario=Scenario([vm]);scenario.detail(disk)
        return scenario,vm,disk

    def test_direct_get_resolves_missing_inventory_disk_once_and_excludes_secrets(self):
        for kind in ('Microsoft.Compute/virtualMachines','Microsoft.Compute/virtualMachineScaleSets'):
            with self.subTest(kind=kind):
                s,vm,disk=self.scenario(kind)
                disk['properties']['diskAccessId']='SECRET-CANARY'
                disk['properties']['creationData']={'sourceUri':'https://example.invalid/SECRET-CANARY'}
                s.run();validate_snapshot(s.snapshot)
                row=next(r for r in s.snapshot['resources'] if r['id']==disk['id'])
                self.assertEqual('ok',row['collection_status']);self.assertEqual('eastus',row['location'])
                self.assertEqual(1,s.transport.calls.count(endpoint(disk['id'],RULES[disk['type'].lower()].api)))
                self.assertTrue(all(d['resolved'] and d['result']=='PASS' for d in s.result(vm)['dependencies']))
                self.assertEqual('UNKNOWN',s.result(vm)['result']) # Guest/temp storage remains unverified.
                self.assertEqual(1,s.snapshot['inventory']['subscriptions'][0]['items_received'])
                self.assertNotIn('SECRET-CANARY',json.dumps(s.snapshot))

    def test_denied_missing_and_mismatched_disk_details_preserve_error_dependency(self):
        for response in ({'fixture_error':403},{'fixture_error':404},resource('Microsoft.Compute/disks','wrong')):
            s,vm,disk=self.scenario();s.responses[endpoint(disk['id'],RULES[disk['type'].lower()].api)]=response
            s.run();validate_snapshot(s.snapshot)
            self.assertEqual('ERROR',s.result(disk)['result'])
            self.assertTrue(all(d['resolved'] and d['result']=='ERROR' for d in s.result(vm)['dependencies']))
            self.assertEqual('UNKNOWN',s.result(vm)['result'])

    def test_foreign_subscription_group_wrong_type_and_malformed_ids_never_fetched(self):
        for target in (resource('Microsoft.Compute/disks','outside')['id'].replace(SUB,SUB2),
                       resource('Microsoft.Compute/disks','outside',group='other')['id'],
                       resource('Microsoft.Storage/storageAccounts','wrongtype')['id'],
                       'https://example.invalid/SECRET-CANARY'):
            s,vm,disk=self.scenario();vm['properties']['storageProfile']={'osDisk':{'managedDisk':{'id':target}}}
            scoped=endpoint('/subscriptions/'+SUB+'/resourceGroups/audit-demo/resources',INVENTORY_API)
            s.responses[scoped]={'value':[vm]};transport=FixtureTransport(s.responses)
            snapshot=Collector(transport,mode='offline_fixture').collect([SUB],resource_group='audit-demo')
            validate_snapshot(snapshot)
            self.assertEqual([vm['id']],[r['id'] for r in snapshot['resources']])
            self.assertFalse(any(target in url for url in transport.calls))
            self.assertEqual('UNKNOWN',assess(snapshot)['results'][0]['result'])
            self.assertNotIn('SECRET-CANARY',json.dumps(snapshot))

    def test_selected_other_subscription_resolves_without_rewriting_inventory(self):
        s,vm,disk=self.scenario();disk2=copy.deepcopy(disk);disk2['id']=disk2['id'].replace(SUB,SUB2)
        vm['properties']['storageProfile']['osDisk']['managedDisk']['id']=disk2['id']
        vm['properties']['storageProfile']['dataDisks']=[];s.detail(disk2)
        s.responses[endpoint('/subscriptions/'+SUB2+'/resources',INVENTORY_API)]={'value':[]}
        transport=FixtureTransport(s.responses);snapshot=Collector(transport,mode='offline_fixture').collect([SUB,SUB2])
        validate_snapshot(snapshot)
        self.assertIn(disk2['id'],[r['id'] for r in snapshot['resources']])
        self.assertEqual([1,0],[s['items_received'] for s in snapshot['inventory']['subscriptions']])

    def test_existing_inventory_disk_is_not_read_twice(self):
        s,vm,disk=self.scenario();s.responses[s.inventory_url]['value'].append(disk)
        s.run();validate_snapshot(s.snapshot)
        self.assertEqual(1,s.transport.calls.count(endpoint(disk['id'],RULES[disk['type'].lower()].api)))
