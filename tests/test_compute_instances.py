import copy
import json
import unittest
from azure_at_rest.compute_instances import collect
from azure_at_rest.collector import FixtureTransport,endpoint
from azure_at_rest.controls import CHECKS
from azure_at_rest.workflow import assess_snapshot
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
            results=assess_snapshot(collect_arm(responses),criteria=policy)['configuration_assessment']['results']
            self.assertEqual('FAIL',next(row for row in results if row['check_id']==self.check.id)['result'])
