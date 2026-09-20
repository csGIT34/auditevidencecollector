import copy
import json
import unittest
from azure_at_rest.log_tables import collect,project,valid,valid_criterion,meets
from azure_at_rest.collector import FixtureTransport,endpoint
from azure_at_rest.controls import CHECKS,validate_policy
from azure_at_rest.workflow import assess_snapshot
from tests.helpers import resource
from tests.test_controls import fixture,collect as collect_arm
from tests.test_archive import MemoryStore
from azure_at_rest.archive import save_run,load_run,publish_pdf


def table(rid):
    return {'id':rid+'/tables/AuditTable','properties':{'plan':'Analytics','retentionInDays':30,
            'totalRetentionInDays':365,'archiveRetentionInDays':335,'retentionInDaysAsDefault':False,
            'totalRetentionInDaysAsDefault':False,'provisioningState':'Succeeded',
            'searchResults':{'query':'SECRET-CANARY'},'schema':{'description':'SECRET-CANARY'},'tags':{'secret':'SECRET-CANARY'}}}


def criterion(rid):
    return {'allow_unlisted':False,'tables':[{'table_id':(rid+'/tables/AuditTable').lower(),
            'allowed_plans':['Analytics'],'minimum_retention_days':30,'minimum_total_days':365}]}


class LogTableTests(unittest.TestCase):
    def setUp(self):
        self.check=CHECKS['LA-table-retention'];self.rid=resource(self.check.resource_type,'workspace')['id']
        self.url=endpoint(self.rid+'/tables',self.check.api)

    def read(self,response,max_pages=10):
        return collect(FixtureTransport({self.url:response}),self.rid,self.check,max_pages)

    def test_projects_retention_without_query_schema_or_payload_secrets(self):
        result=self.read({'value':[table(self.rid)]})
        self.assertEqual('observed',result['state']);self.assertTrue(valid(result['value']))
        self.assertNotIn('SECRET-CANARY',json.dumps(result));self.assertTrue(meets(result['value'],criterion(self.rid)))
        self.assertTrue(valid_criterion(criterion(self.rid)))

    def test_denied_truncated_duplicate_and_wrong_parent_reads_stay_incomplete(self):
        row=table(self.rid);wrong=table(self.rid+'-other')
        for response in ({'fixture_error':403},{'value':[row],'nextLink':self.url+'&next=2'},
                         {'value':[row,row]},{'value':[wrong]},{'value':[None]}):
            self.assertEqual('partial',self.read(response)['state'])

    def test_missing_inherited_sentinel_conflicting_unknown_plan_and_unstable_values_do_not_pass(self):
        for key,value in [('retentionInDays',None),('retentionInDays',-1),('retentionInDays',True),('retentionInDays',0),('totalRetentionInDaysAsDefault',True),
                          ('totalRetentionInDays',10),('archiveRetentionInDays',1),('plan','FuturePlan'),
                          ('provisioningState','Updating'),('retentionInDaysAsDefault',None)]:
            row=table(self.rid);row['properties'][key]=value
            self.assertEqual('partial',self.read({'value':[row]})['state'],(key,value))

    def test_threshold_plan_population_and_inheritance_baseline_cases(self):
        row=project(table(self.rid));policy=criterion(self.rid)
        self.assertFalse(meets([],policy))
        for key,value in [('plan','Basic'),('retention_days',29),('total_retention_days',364)]:
            changed={**row,key:value};self.assertFalse(meets([changed],policy))
        other={**row,'table_id':row['table_id']+'extra'}
        self.assertFalse(meets([row,other],policy));self.assertTrue(meets([row,other],{**policy,'allow_unlisted':True}))
        inherited={**row,'retention_inherited':True,'total_retention_inherited':False}
        self.assertTrue(meets([inherited],policy)) # Numeric returned values, never assumed defaults.
        for field in ('minimum_retention_days','minimum_total_days'):
            bad=copy.deepcopy(policy);bad['tables'][0][field]=True;self.assertFalse(valid_criterion(bad))
        self.assertFalse(valid_criterion({'allow_unlisted':True,'tables':[]}))

    def test_real_pipeline_freezes_failed_table_requirement_and_preserves_source(self):
        responses,policy=fixture();url=next(u for u in responses if '/tables?api-version=2025-07-01' in u)
        rid=responses[url]['value'][0]['id'].rsplit('/',2)[0]
        policy['checks'][self.check.id]={'operator':'table_retention','value':criterion(rid)}
        validate_policy(policy);responses[url]['value']=[]
        snapshot=collect_arm(responses);report=assess_snapshot(snapshot,criteria=policy)
        result=next(r for r in report['configuration_assessment']['results'] if r['check_id']==self.check.id)
        self.assertEqual('FAIL',result['result'])
        store=MemoryStore();run=save_run(store,snapshot,report)['run_id'];before=dict(store.objects)
        self.assertEqual(report,load_run(store,run)['assessment']);publish_pdf(store,run)
        self.assertTrue(all(store.objects[k]==v for k,v in before.items()))

    def test_missing_and_draft_criteria_remain_unknown(self):
        responses,policy=fixture();snapshot=collect_arm(responses)
        for value in (None,{**policy,'status':'draft'}):
            report=assess_snapshot(snapshot,criteria=value)
            self.assertEqual('UNKNOWN',next(r for r in report['configuration_assessment']['results'] if r['check_id']==self.check.id)['result'])
