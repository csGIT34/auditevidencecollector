from cloud_governance import report_model
import copy
import json
import unittest
from cloud_governance.compute_instances import collect
from cloud_governance.collector import FixtureTransport,endpoint
from cloud_governance.controls import CHECKS
from cloud_governance.workflow import assess_snapshot
from tests.helpers import resource
from tests.test_controls import fixture,collect as collect_arm

class ComputeInstanceTests(unittest.TestCase):
    def setUp(self):
        self.check=CHECKS['VMSS-instance-models'];self.rid=resource(self.check.resource_type,'scale')['id']
        self.url=endpoint(self.rid+self.check.suffix,self.check.api)
        self.parent={'properties':{'orchestrationMode':'Uniform'}}
        self.row={'id':self.rid+'/virtualMachines/0','properties':{'latestModelApplied':True,'osProfile':{'adminPassword':'SECRET-CANARY'},'customData':'SECRET-CANARY'}}

    def read(self,response):
        return collect(FixtureTransport({self.url:response}),self.rid,self.check,10,self.parent)

    def test_actual_instances_keep_false_and_exclude_sensitive_properties(self):
        other=copy.deepcopy(self.row);other['id']=self.rid+'/virtualMachines/1';other['properties']['latestModelApplied']=False
        result=self.read({'value':[other,self.row]})
        self.assertEqual('observed',result['state'])
        self.assertEqual([True,False],[r['latest_model_applied'] for r in result['value']])
        self.assertNotIn('SECRET-CANARY',json.dumps(result))

    def test_denied_truncated_duplicate_wrong_parent_and_missing_facts_do_not_complete(self):
        wrong=copy.deepcopy(self.row);wrong['id']=self.rid+'-other/virtualMachines/0'
        missing=copy.deepcopy(self.row);missing['properties'].pop('latestModelApplied')
        invalid=copy.deepcopy(self.row);invalid['properties']['latestModelApplied']=1
        for response in ({'fixture_error':403},{'value':[self.row],'nextLink':self.url+'&$skiptoken=missing'},
                         {'value':[self.row,self.row]},{'value':[wrong]},{'value':[missing]},{'value':[invalid]}):
            self.assertEqual('partial',self.read(response)['state'])

    def test_flexible_missing_and_denied_parent_do_not_claim_empty_uniform_population(self):
        class NoRequests:
            def get(self,url):raise AssertionError('must not list wrong orchestration mode')
        for parent in (None,{}, {'properties':{'orchestrationMode':'Flexible'}}):
            self.assertEqual({'state':'missing'},collect(NoRequests(),self.rid,self.check,10,parent))

    def test_instance_model_drift_and_missing_expected_vm_fail_policy(self):
        for mutation in ('drift','missing'):
            responses,policy=fixture();url=next(k for k in responses if '/virtualMachines?api-version=2026-03-01' in k)
            if mutation=='drift':responses[url]['value'][0]['properties']['latestModelApplied']=False
            else:responses[url]['value']=[]
            results=report_model.configuration_results(assess_snapshot(collect_arm(responses),criteria=policy))
            self.assertEqual('FAIL',next(row for row in results if row['check_id']==self.check.id)['result'])

    def test_flexible_membership_uses_declared_parent_and_discovers_vm_dependencies(self):
        from cloud_governance.collector import INVENTORY_API
        from tests.helpers import SUB
        responses,policy=fixture()
        vm_url=next(u for u,v in responses.items() if isinstance(v,dict) and v.get('type')=='microsoft.compute/virtualmachines')
        vm=responses[vm_url]
        parent_url=next(u for u,v in responses.items() if isinstance(v,dict) and v.get('type')=='microsoft.compute/virtualmachinescalesets')
        parent=responses[parent_url];parent['properties']['orchestrationMode']='Flexible'
        vm['properties']['virtualMachineScaleSet']={'id':parent['id']};vm['properties']['customData']='SECRET-CANARY'
        inventory_url=endpoint('/subscriptions/'+SUB+'/resources',INVENTORY_API)
        responses[inventory_url]['value']=[v for v in responses[inventory_url]['value'] if v['id']!=vm['id']]
        listing=endpoint('/subscriptions/'+SUB+'/providers/Microsoft.Compute/virtualMachines','2026-03-01')
        responses[listing]={'value':[vm]}
        policy['checks']['VMSS-instance-members']={'operator':'equals','value':{'orchestration':'Flexible','scope':'subscription','members':[vm['id'].lower()]}}
        snapshot=collect_arm(responses);rows={r['id']:r for r in snapshot['resources']}
        self.assertIn(vm['id'],rows);self.assertEqual('ok',rows[vm['id']]['collection_status'])
        observed=rows[parent['id']]['configuration']['VMSS-instance-members']
        self.assertEqual('observed',observed['state']);self.assertNotIn('SECRET-CANARY',json.dumps(snapshot))
        report=assess_snapshot(snapshot,criteria=policy)
        decision=next(r for r in report_model.configuration_results(report) if r['check_id']=='VMSS-instance-members')
        self.assertEqual('PASS',decision['result']);self.assertEqual(listing.split('?')[0].removeprefix('https://management.azure.com'),decision['request_path'])
        from cloud_governance.archive import save_run,load_run
        from tests.test_archive import MemoryStore
        store=MemoryStore();run=save_run(store,snapshot,report)['run_id'];self.assertEqual(snapshot,load_run(store,run)['snapshot'])
        from cloud_governance.guest_evidence import population
        expected,complete=population(load_run(store,run),[parent['id'].lower()])
        self.assertEqual({vm['id'].lower():'VMSS'},expected);self.assertTrue(complete)

    def test_flexible_listing_scope_denials_and_missing_association_are_explicit(self):
        from cloud_governance.compute_instances import collect_members
        from tests.helpers import SUB
        check=CHECKS['VMSS-instance-members'];parent={'properties':{'orchestrationMode':'Flexible'}}
        vm=resource('Microsoft.Compute/virtualMachines','member');vm['properties']['virtualMachineScaleSet']={'id':self.rid}
        group=vm['id'].split('/')[4]
        url=endpoint('/subscriptions/'+SUB+'/resourceGroups/'+group+'/providers/Microsoft.Compute/virtualMachines',check.api)
        for response,expected in [({'value':[vm]},'observed'),({'fixture_error':403},'partial'),({'value':[vm,vm]},'partial'),({'value':[{'id':vm['id']}]},'partial')]:
            transport=FixtureTransport({url:response})
            result,members=collect_members(transport,self.rid,check,10,parent,{},group)
            self.assertEqual(expected,result['state']);self.assertEqual([url],transport.calls)
            self.assertEqual('resource_group',result['value']['scope'])
        outside=copy.deepcopy(vm);outside['id']=outside['id'].replace('/resourceGroups/'+group+'/', '/resourceGroups/other/')
        result,_=collect_members(FixtureTransport({url:{'value':[outside]}}),self.rid,check,10,parent,{},group)
        self.assertEqual('partial',result['state']);self.assertEqual([],result['value']['members'])

    def test_uniform_membership_reuses_model_population_without_additional_requests(self):
        from cloud_governance.compute_instances import collect_members
        class NoRequests:
            def get(self,url):raise AssertionError('No duplicate instance read')
        models=self.read({'value':[self.row]})
        result,raw=collect_members(NoRequests(),self.rid,CHECKS['VMSS-instance-members'],10,self.parent,models)
        self.assertEqual('observed',result['state']);self.assertEqual([self.row['id'].lower()],result['value']['members']);self.assertEqual([],raw)
