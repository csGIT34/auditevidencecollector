import copy
import json
import unittest
from cloud_governance.container_revisions import collect
from cloud_governance.collector import FixtureTransport,endpoint
from cloud_governance.controls import CHECKS
from tests.helpers import resource


def revision(rid):
    return {'id':rid+'/revisions/revision-1','properties':{'active':True,'template':{
        'containers':[{'name':'web','image':'example.azurecr.io/web@sha256:'+'a'*64,'env':[{'name':'PASSWORD','value':'SECRET-CANARY'}]}],
        'initContainers':[{'name':'initialize','image':'example.azurecr.io/init:v1','command':['SECRET-CANARY']}]}}}


def normalized(raw):
    return {'revision_id':raw['id'].lower(),'active':raw['properties']['active'],
            'containers':[{'name':c['name'],'image':c['image'],'kind':kind} for key,kind in [('containers','app'),('initContainers','init')] for c in raw['properties']['template'].get(key,[])]}

class ContainerRevisionTests(unittest.TestCase):
    def setUp(self):
        self.check=CHECKS['ACA-revision-images'];self.rid=resource(self.check.resource_type,'app')['id']
        self.url=endpoint(self.rid+self.check.suffix,self.check.api);self.row=revision(self.rid)

    def read(self,response):return collect(FixtureTransport({self.url:response}),self.rid,self.check,10)

    def test_init_and_app_images_project_without_environment_or_commands(self):
        result=self.read({'value':[self.row]})
        self.assertEqual('observed',result['state']);self.assertEqual([normalized(self.row)],result['value'])
        self.assertNotIn('SECRET-CANARY',json.dumps(result))

    def test_wrong_revision_denied_incomplete_and_missing_images_are_partial(self):
        wrong=copy.deepcopy(self.row);wrong['id']=self.rid+'-other/revisions/revision-1'
        missing=copy.deepcopy(self.row);missing['properties']['template']['initContainers'][0].pop('image')
        for response in ({'fixture_error':403},{'value':[wrong]},{'value':[missing]},{'value':[self.row,self.row]},
                         {'value':[self.row],'nextLink':self.url+'&$skiptoken=missing'}):
            self.assertEqual('partial',self.read(response)['state'])

    def test_changed_image_or_activation_fails_saved_criteria(self):
        from tests.test_controls import fixture,collect as collect_arm
        from cloud_governance.workflow import assess_snapshot
        for change in ('image','active','missing'):
            responses,policy=fixture();url=next(k for k in responses if '/revisions?' in k)
            if change=='image':responses[url]['value'][0]['properties']['template']['initContainers'][0]['image']='example.azurecr.io/init:old'
            elif change=='active':responses[url]['value'][0]['properties']['active']=False
            else:responses[url]['value']=[]
            result=assess_snapshot(collect_arm(responses),criteria=policy)['configuration_assessment']['results']
            self.assertEqual('FAIL',next(r for r in result if r['check_id']==self.check.id)['result'])
