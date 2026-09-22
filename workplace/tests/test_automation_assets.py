from cloud_governance import report_model
import copy
import json
import unittest
from cloud_governance.automation_assets import collect,project,baseline
from cloud_governance.collector import FixtureTransport,endpoint
from cloud_governance.controls import CHECKS
from cloud_governance.workflow import assess_snapshot
from cloud_governance.archive import save_run,load_run,publish_pdf
from tests.helpers import resource
from tests.test_controls import fixture,collect as collect_arm
from tests.test_archive import MemoryStore


def asset(rid,kind):
    props={'lastModifiedTime':'2026-09-01T00:00:00Z','contentLink':{'uri':'https://example.test/?sig=SECRET-CANARY'},'description':'SECRET-CANARY','parameters':{'password':{'defaultValue':'SECRET-CANARY'}},'draft':{'draftContentLink':{'uri':'SECRET-CANARY'}}}
    if kind=='runbooks':props.update(runbookType='PowerShell',state='Published',runtimeEnvironment='reviewed-runtime',logProgress=True,logVerbose=False)
    else:props.update(version='1.2.3',provisioningState='Succeeded',error={'message':'SECRET-CANARY'})
    return {'id':rid+'/'+kind+'/example','properties':props,'tags':{'owner':'SECRET-CANARY'}}

class AutomationAssetTests(unittest.TestCase):
    def setUp(self):self.rid=resource('Microsoft.Automation/automationAccounts','example')['id']
    def read(self,kind,response):
        check=CHECKS['AUTO-'+kind+'-metadata'];url=endpoint(self.rid+check.suffix,check.api);transport=FixtureTransport({url:response})
        result=collect(transport,self.rid,check,10);self.assertEqual([url],transport.calls);return result

    def test_metadata_projection_excludes_content_links_parameters_and_errors(self):
        for kind in ('runbooks','modules'):
            result=self.read(kind,{'value':[asset(self.rid,kind)]})
            self.assertEqual('observed',result['state']);self.assertNotIn('SECRET-CANARY',json.dumps(result))
            self.assertEqual(1,len(result['value']))

    def test_denied_duplicates_wrong_parent_invalid_and_missing_version_cannot_pass(self):
        for kind in ('runbooks','modules'):
            item=asset(self.rid,kind);wrong=asset(self.rid+'-other',kind)
            invalid=copy.deepcopy(item);invalid['properties']['lastModifiedTime']='SECRET-CANARY'
            future=copy.deepcopy(item);future['properties']['lastModifiedTime']='2099-01-01T00:00:00Z'
            for response in ({'value':[future]},{'fixture_error':403},{'value':[item,item]},{'value':[wrong]},{'value':[invalid]}):
                self.assertEqual('partial',self.read(kind,response)['state'])
        item=asset(self.rid,'modules');item['properties']['version']=None
        result=self.read('modules',{'value':[item]});self.assertEqual('partial',result['state']);self.assertIsNone(result['value'][0]['version'])

    def test_pagination_truncation_never_looks_complete(self):
        kind='runbooks';check=CHECKS['AUTO-runbooks-metadata'];url=endpoint(self.rid+check.suffix,check.api)
        transport=FixtureTransport({url:{'value':[asset(self.rid,kind)],'nextLink':url+'&$skiptoken=missing'}})
        result=collect(transport,self.rid,check,10);self.assertEqual('partial',result['state']);self.assertFalse(result['collection']['complete'])

    def test_baseline_reports_version_publication_and_population_drift(self):
        for kind,mutation in [('modules','version'),('runbooks','state'),('runbooks','population')]:
            responses,policy=fixture();cid='AUTO-'+kind+'-metadata';url=next(u for u in responses if '/'+kind+'?api-version=2024-10-23' in u)
            policy['checks'][cid]={'operator':'asset_baseline','value':baseline([project(responses[url]['value'][0],kind)])}
            if mutation=='population':responses[url]['value']=[]
            elif mutation=='version':responses[url]['value'][0]['properties']['version']='0.1.0'
            else:responses[url]['value'][0]['properties']['state']='Edit'
            snapshot=collect_arm(responses);report=assess_snapshot(snapshot,criteria=policy)
            row=next(r for r in report_model.configuration_results(report) if r['check_id']==cid)
            self.assertEqual('FAIL',row['result'])
            store=MemoryStore();run=save_run(store,snapshot,report)['run_id'];before=dict(store.objects)
            self.assertEqual(report,load_run(store,run)['assessment']);publish_pdf(store,run)
            for key,value in before.items():self.assertEqual(value,store.objects[key])

    def test_absent_and_draft_baselines_remain_unknown(self):
        responses,policy=fixture();snapshot=collect_arm(responses)
        for value in (None,{**policy,'status':'draft'}):
            report=assess_snapshot(snapshot,criteria=value)
            self.assertTrue(all(r['result']=='UNKNOWN' for r in report_model.configuration_results(report) if r['check_id'] in ('AUTO-runbooks-metadata','AUTO-modules-metadata')))

    def test_baseline_ignores_modification_time_but_keeps_typed_expected_fields(self):
        from cloud_governance.automation_assets import valid_criterion
        for kind in ('runbooks','modules'):
            value=project(asset(self.rid,kind),kind);expected=baseline([value]);self.assertTrue(valid_criterion(expected,kind))
            value['last_modified']='2026-09-02T00:00:00Z';self.assertEqual(expected,baseline([value]))
            self.assertFalse(valid_criterion([value],kind))
        expected[0]['version']=None;self.assertFalse(valid_criterion(expected,'modules'))


def runtime_fixture(rid):
    check=CHECKS['AUTO-runtime-packages'];eid=rid+'/runtimeEnvironments/reviewed';pid=eid+'/packages/Example.Package'
    raw={'id':eid,'properties':{'runtime':{'language':'PowerShell','version':'7.4'},'defaultPackages':{'Az':'12.3.0'},'description':'SECRET-CANARY'}}
    package={'id':pid,'properties':{'version':'1.0.0','provisioningState':'Succeeded','contentLink':{'uri':'SECRET-CANARY'},'error':{'message':'SECRET-CANARY'}}}
    responses={endpoint(rid+check.suffix,check.api):{'value':[raw]},endpoint(eid.lower()+'/packages',check.api):{'value':[package]}}
    expected=[{'environment_id':eid.lower(),'language':'PowerShell','version':'7.4','default_packages':[{'name':'Az','version':'12.3.0'}],
               'packages':[{'package_id':pid.lower(),'version':'1.0.0','provisioning_state':'Succeeded'}]}]
    return responses,expected


class AutomationRuntimeTests(unittest.TestCase):
    def test_runtime_and_package_reads_keep_versions_without_links_or_messages(self):
        from cloud_governance.automation_assets import collect_runtimes
        rid=resource('Microsoft.Automation/automationAccounts','example')['id'];responses,expected=runtime_fixture(rid)
        transport=FixtureTransport(responses);result=collect_runtimes(transport,rid,CHECKS['AUTO-runtime-packages'],10)
        self.assertEqual('observed',result['state']);self.assertEqual(expected,result['value']);self.assertEqual(2,len(transport.calls))
        self.assertNotIn('SECRET-CANARY',json.dumps(result))

    def test_missing_denied_duplicate_and_wrong_environment_package_cannot_complete(self):
        from cloud_governance.automation_assets import collect_runtimes
        rid=resource('Microsoft.Automation/automationAccounts','example')['id']
        for mutation in ('denied','missing_version','duplicate','wrong_parent','missing_runtime'):
            responses,_=runtime_fixture(rid);key=next(u for u in responses if '/packages?' in u);package=responses[key]['value'][0]
            if mutation=='denied':responses[key]={'fixture_error':403}
            elif mutation=='missing_version':package['properties']['version']=None
            elif mutation=='duplicate':responses[key]['value'].append(copy.deepcopy(package))
            elif mutation=='wrong_parent':package['id']=package['id'].replace('/reviewed/','/wrong/')
            else:responses[next(u for u in responses if '/runtimeEnvironments?' in u)]['value'][0]['properties']['runtime']={}
            result=collect_runtimes(FixtureTransport(responses),rid,CHECKS['AUTO-runtime-packages'],10)
            self.assertEqual('partial',result['state'])
