import copy
import json
import unittest
from cloud_governance.blob_containers import collect
from cloud_governance.collector import FixtureTransport,endpoint
from cloud_governance.controls import CHECKS
from tests.helpers import resource


def container(rid):
    return {'id':rid+'/blobServices/default/containers/private','properties':{'publicAccess':'None','metadata':{'secret':'SECRET-CANARY'},'legalHold':{'tags':[{'upn':'SECRET-CANARY'}]}}}


def normalized(raw):return {'container_id':raw['id'].lower(),'public_access':raw['properties']['publicAccess']}

class BlobContainerTests(unittest.TestCase):
    def setUp(self):
        self.check=CHECKS['ST-container-access'];self.rid=resource(self.check.resource_type,'account')['id']
        self.url=endpoint(self.rid+self.check.suffix,self.check.api);self.row=container(self.rid)

    def read(self,response):return collect(FixtureTransport({self.url:response}),self.rid,self.check,10)

    def test_special_containers_and_public_levels_retained_without_metadata(self):
        public=copy.deepcopy(self.row);public['id']=self.rid+'/blobServices/default/containers/$web';public['properties']['publicAccess']='Blob'
        result=self.read({'value':[self.row,public]})
        self.assertEqual('observed',result['state']);self.assertEqual(['Blob','None'],[r['public_access'] for r in result['value']])
        self.assertNotIn('SECRET-CANARY',json.dumps(result))

    def test_invalid_scope_missing_flags_duplicates_denied_and_partial_do_not_pass(self):
        missing=copy.deepcopy(self.row);missing['properties'].pop('publicAccess')
        wrong=copy.deepcopy(self.row);wrong['id']=wrong['id'].replace('/account/','/other/')
        for response in ({'value':[missing]},{'value':[wrong]},{'value':[self.row,self.row]}, {'fixture_error':403},
                         {'value':[self.row],'nextLink':self.url+'&$skiptoken=missing'}):
            self.assertEqual('partial',self.read(response)['state'])

    def test_container_exposure_fails_even_when_account_disallows_public_access(self):
        from tests.test_controls import fixture,collect as collect_arm
        from cloud_governance.workflow import assess_snapshot
        responses,policy=fixture();url=next(k for k in responses if '/containers?' in k)
        policy['checks']['ST-container-access']={'operator':'allowed_access','value':['None']}
        for level,expected in [('None','PASS'),('Blob','FAIL'),('Container','FAIL')]:
            responses[url]['value'][0]['properties']['publicAccess']=level
            results=assess_snapshot(collect_arm(responses),criteria=policy)['configuration_assessment']['results']
            self.assertEqual(expected,next(r for r in results if r['check_id']==self.check.id)['result'])

    def test_empty_complete_listing_and_missing_criteria_are_distinct(self):
        from tests.test_controls import fixture,collect as collect_arm
        from cloud_governance.workflow import assess_snapshot
        responses,policy=fixture();url=next(k for k in responses if '/containers?' in k);responses[url]={'value':[]}
        policy['checks'][self.check.id]={'operator':'allowed_access','value':['None']}
        snapshot=collect_arm(responses)
        for supplied,result in ((policy,'PASS'),(None,'UNKNOWN')):
            rows=assess_snapshot(snapshot,criteria=supplied)['configuration_assessment']['results']
            self.assertEqual(result,next(r for r in rows if r['check_id']==self.check.id)['result'])
