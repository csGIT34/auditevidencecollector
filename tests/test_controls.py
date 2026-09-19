import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pypdf import PdfReader
from azure_at_rest.controls import CHECKS, for_type, validate_policy
from azure_at_rest.collector import Collector, FixtureTransport, endpoint, INVENTORY_API
from azure_at_rest.catalog import RULES
from azure_at_rest.workflow import assess_snapshot
from azure_at_rest.snapshot import validate_snapshot
from azure_at_rest.archive import save_run, load_run, publish_pdf, validate_pair
from azure_at_rest.report import markdown, exit_code
from tests.helpers import resource, SUB
from tests.test_archive import MemoryStore


def setpath(obj,path,value):
    for part in path.split('.')[:-1]:
        obj = obj.setdefault(part,{})
    obj[path.split('.')[-1]] = value



def sample(check, negative=False):
    if check.kind=='labels':return ['category:Different' if negative else 'category:AuditEvent']
    if check.kind=='resource_ids':return [resource('Microsoft.Storage/storageAccounts','other' if negative else 'approved')['id'].lower()]
    if check.kind=='tokens':return ['Pending' if negative else 'Approved'] if check.id=='PE-approval' else ['file' if negative else 'blob']
    if check.kind=='federation':return [{'issuer':'https://other.example.invalid' if negative else 'https://issuer.example.invalid','subject':'system:serviceaccount:audit:collector','audiences':['api://AzureADTokenExchange']}]
    return check.values[-1 if negative else 0] if check.values else 60 if negative else 30


def fixture():
    resources=[]; responses={}; criteria={}
    for number, rt in enumerate(sorted({c.resource_type for c in CHECKS.values() if not c.resource_type.startswith('graph.')})):
        parts = rt.split('/')[1:]
        row=resource(rt, '/'.join('demo'+str(number) for _ in parts))
        row['kind']='functionapp' if rt.startswith('microsoft.web/') else 'unspecified'
        row['properties']['provisioningState']='Succeeded'
        resources.append(row)
        checks=for_type(rt)
        rule=RULES.get(rt)
        api=rule.api if rule and rule.api else checks[0].api
        responses[endpoint(row['id'],api)]=row
        for c in checks:
            value=sample(c)
            criteria[c.id]={'operator':'equals','value':value}
            if c.operation == 'private_endpoint':
                row['properties']['privateLinkServiceConnections']=[{'properties':{'privateLinkServiceId':sample(CHECKS['PE-targets'])[0],'groupIds':['blob'],'privateLinkServiceConnectionState':{'status':'Approved'}}}]
                row['properties']['manualPrivateLinkServiceConnections']=[]
                continue
            if c.operation == 'federation':
                responses[endpoint(row['id']+c.suffix,c.api)]={'value':[{'id':row['id']+c.suffix+'/safe','properties':{**value[0],'secretCanary':'DO-NOT-ARCHIVE-SECRET'}}]}
                continue
            if c.operation == 'diagnostics':
                responses[endpoint(row['id']+c.suffix,c.api)]={'value':[{'id':row['id']+c.suffix+'/safe','properties':{'logs':[{'category':'AuditEvent','enabled':True}], 'secretCanary':'DO-NOT-ARCHIVE-SECRET'}}]}
                continue
            if c.suffix:
                target=responses.setdefault(endpoint(row['id']+c.suffix,c.api),{'id':row['id']+c.suffix,'properties':{}})
            else:target=row
            setpath(target['properties'],c.path,value)
            target['properties']['secretCanary']='DO-NOT-ARCHIVE-SECRET'
        if rule:
            for suffix,_ in rule.children:
                responses[endpoint(row['id']+'/'+suffix,rule.api)]={'value':[]}
    responses[endpoint(f'/subscriptions/{SUB}/resources',INVENTORY_API)]={'value':resources}
    return responses, {'schema_version':'1.0','id':'synthetic-only','version':'1','status':'approved','checks':criteria}


def collect(responses):
    return Collector(FixtureTransport(responses),mode='offline_fixture').collect([SUB])


class ConfigurationTests(unittest.TestCase):
    def test_every_predicate_collects_and_passes_exact_criterion(self):
        responses,policy=fixture(); snapshot=collect(responses); validate_snapshot(snapshot)
        report=assess_snapshot(snapshot,criteria=policy)
        results=report['configuration_assessment']['results']
        self.assertEqual({c.id for c in CHECKS.values() if not c.resource_type.startswith('graph.')},{r['check_id'] for r in results})
        self.assertTrue(all(r['result']=='PASS' for r in results))
        self.assertNotIn('DO-NOT-ARCHIVE-SECRET',json.dumps(snapshot))
        self.assertNotIn('DO-NOT-ARCHIVE-SECRET',json.dumps(report))
        catalog=json.loads((Path(__file__).parents[1]/'docs/audit/catalog.json').read_text())
        self.assertLessEqual({c.catalog_ref for c in CHECKS.values()},{r['id'] for r in catalog['checks']})

    def test_every_predicate_fails_mismatched_criterion(self):
        responses,policy=fixture()
        for cid,c in CHECKS.items():
            if cid not in policy['checks']:continue
            policy['checks'][cid]['value']=sample(c,True)
        results=assess_snapshot(collect(responses),criteria=policy)['configuration_assessment']['results']
        self.assertTrue(all(r['result']=='FAIL' for r in results))

    def test_every_predicate_missing_null_invalid_is_unknown_and_redacted(self):
        for value in (None, {'secret':'DO-NOT-ARCHIVE-SECRET'}, 'DO-NOT-ARCHIVE-SECRET'):
            responses,policy=fixture()
            for c in CHECKS.values():
                for raw in responses.values():
                    if isinstance(raw,dict) and 'properties' in raw and (raw.get('type','').lower()==c.resource_type if not c.suffix else raw.get('id','').endswith(c.suffix)):
                        setpath(raw['properties'],c.path,value)
            for url in list(responses):
                if '/diagnosticSettings?' in url or '/federatedIdentityCredentials?' in url:responses[url]={'value':[{'properties':{'logs':value}}]}
                elif '/privateendpoints/' in url and 'properties' in responses[url]:responses[url]['properties']['privateLinkServiceConnections']=None
            snapshot=collect(responses);validate_snapshot(snapshot)
            results=assess_snapshot(snapshot,criteria=policy)['configuration_assessment']['results']
            self.assertTrue(all(r['result']=='UNKNOWN' for r in results))
            self.assertNotIn('DO-NOT-ARCHIVE-SECRET',json.dumps(snapshot))

    def test_absent_or_draft_criteria_never_pass(self):
        responses,policy=fixture();snapshot=collect(responses)
        for criteria in (None,{**policy,'status':'draft'},{**policy,'checks':{}}):
            report=assess_snapshot(snapshot,criteria=criteria)
            self.assertTrue(all(r['result']=='UNKNOWN' for r in report['configuration_assessment']['results']))
            self.assertEqual(2,exit_code(report))

    def test_supplemental_denial_is_local_to_affected_checks(self):
        responses,policy=fixture()
        for url in list(responses):
            if '/config/web?' in url:responses[url]={'fixture_error':403}
        snapshot=collect(responses);validate_snapshot(snapshot)
        report=assess_snapshot(snapshot,criteria=policy)
        for row in report['configuration_assessment']['results']:
            self.assertEqual('ERROR' if '/config/web' in row['request_path'] else 'PASS',row['result'])
        self.assertTrue(all(r['collection_status']=='ok' for r in snapshot['resources']))

    def test_wrong_supplemental_identity_cannot_pass(self):
        responses,policy=fixture()
        for url,raw in responses.items():
            if '/config/web?' in url:raw['id'] += '-wrong'
        results=assess_snapshot(collect(responses),criteria=policy)['configuration_assessment']['results']
        self.assertTrue(all(r['result']=='ERROR' for r in results if '/config/web' in r['request_path']))

    def test_policy_rejects_arbitrary_values_and_boolean_integer_confusion(self):
        _,policy=fixture()
        for cid,criterion in [('ST-https',{'operator':'equals','value':1}),('ST-tls',{'operator':'at_least','value':'TLS1_2'}),('LA-retention',{'operator':'equals','value':True}),('ST-https',{'operator':'equals','value':'secret'})]:
            bad=copy.deepcopy(policy);bad['checks'][cid]=criterion
            with self.assertRaises(ValueError):validate_policy(bad)
        for key,value in [('status','trusted'),('checks',{'missing':{}}),('extra','secret')]:
            bad=copy.deepcopy(policy);bad[key]=value
            with self.assertRaises(ValueError):validate_policy(bad)

    def test_numeric_threshold_and_explicit_enum_set(self):
        responses,policy=fixture()
        policy['checks']['LA-retention']={'operator':'at_least','value':29}
        policy['checks']['ST-tls']={'operator':'one_of','value':['TLS1_0','TLS1_2']}
        results=assess_snapshot(collect(responses),criteria=policy)['configuration_assessment']['results']
        self.assertTrue(all(r['result']=='PASS' for r in results))

    def test_archive_pdf_and_markdown_include_frozen_controls(self):
        responses,policy=fixture();snapshot=collect(responses)
        report=assess_snapshot(snapshot,criteria=policy);store=MemoryStore()
        manifest=save_run(store,snapshot,report)
        original=dict(store.objects)
        with patch('azure_at_rest.controls.evaluate',side_effect=AssertionError('historical re-evaluation')):
            saved=load_run(store,manifest['run_id'])
            pdf=publish_pdf(store,manifest['run_id'])
        self.assertEqual(report,saved['assessment'])
        self.assertTrue(all(store.read(k)==v for k,v in original.items()))
        pages=[p.extract_text() for p in PdfReader(io.BytesIO(store.read(pdf['pdf']['key']))).pages]
        extracted=' '.join(pages)
        normalized=[' '.join(page.split()) for page in pages]
        for row in report['configuration_assessment']['results']:
            heading=' '.join((row['check_id']+' | '+row['result']+' | '+row['title']).split())
            self.assertTrue(any(heading in page for page in normalized),row['check_id']+' heading split across pages')
        for term in ('Configuration control assessments','ST-https','LA-retention','synthetic-only','Saved criterion'):
            self.assertIn(term,extracted)
        self.assertIn('ST-https',markdown(report))
        self.assertNotIn('DO-NOT-ARCHIVE-SECRET',extracted)

    def test_archive_rejects_changed_observation_or_summary(self):
        responses,policy=fixture();snapshot=collect(responses);report=assess_snapshot(snapshot,criteria=policy)
        bad=copy.deepcopy(report);bad['configuration_assessment']['results'][0]['observation']={'state':'missing'}
        with self.assertRaises(ValueError):validate_pair(snapshot,bad)
        bad=copy.deepcopy(report);bad['configuration_assessment']['summary']['check_count']+=1
        with self.assertRaises(ValueError):validate_pair(snapshot,bad)

    def test_snapshot_rejects_injected_configuration_payload(self):
        responses,_=fixture();snapshot=collect(responses)
        raw=next(r for r in snapshot['resources'] if r['configuration'])
        cid=next(iter(raw['configuration']));raw['configuration'][cid]['password']='secret'
        with self.assertRaises(ValueError):validate_snapshot(snapshot)

    def test_per_resource_override_is_frozen_and_other_resources_keep_baseline(self):
        responses,policy=fixture();snapshot=collect(responses)
        row=next(r for r in snapshot['resources'] if r['type'].lower()=='microsoft.storage/storageaccounts')
        policy['checks']['ST-https']={'operator':'equals','value':True}
        policy['overrides']={row['id'].lower():{'ST-https':{'operator':'equals','value':False}}}
        report=assess_snapshot(snapshot,criteria=policy)
        result=next(r for r in report['configuration_assessment']['results'] if r['check_id']=='ST-https')
        self.assertEqual('PASS',result['result']);self.assertEqual(False,result['criterion']['value'])
        store=MemoryStore();manifest=save_run(store,snapshot,report)
        self.assertEqual(policy,load_run(store,manifest['run_id'])['assessment']['configuration_assessment']['policy'])

    def test_duplicate_or_nonfinite_criteria_json_is_rejected(self):
        from azure_at_rest.controls import decode_policy
        for text in ('{"checks":{},"checks":{}}','{"value":NaN}','{"value":Infinity}'):
            with self.assertRaises(ValueError):decode_policy(text)

    def test_diagnostic_pagination_and_denial_preserve_completeness(self):
        responses,policy=fixture()
        url=next(u for u in responses if '/diagnosticSettings?' in u)
        responses[url]['nextLink']=url+'&$skiptoken=page2'
        responses[url+'&$skiptoken=page2']={'fixture_error':403}
        snapshot=collect(responses);validate_snapshot(snapshot)
        report=assess_snapshot(snapshot,criteria=policy)
        rows=[r for r in report['configuration_assessment']['results'] if r['observation'].get('collection',{}).get('errors')]
        self.assertEqual(1,len(rows));self.assertEqual('ERROR',rows[0]['result'])
        self.assertEqual(['category:AuditEvent'],rows[0]['observation']['value'])
        self.assertEqual(1,rows[0]['observation']['collection']['pages'])
        self.assertFalse(rows[0]['observation']['collection']['complete'])

    def test_federation_issuer_with_query_is_not_archived_or_accepted(self):
        responses,policy=fixture()
        url=next(u for u in responses if '/federatedIdentityCredentials?' in u)
        responses[url]['value'][0]['properties']['issuer']='https://issuer.example.invalid?sig=SECRET'
        snapshot=collect(responses);validate_snapshot(snapshot)
        report=assess_snapshot(snapshot,criteria=policy)
        row=next(r for r in report['configuration_assessment']['results'] if r['check_id']=='UAMI-federation-trust')
        self.assertEqual('UNKNOWN',row['result']);self.assertNotIn('sig=SECRET',json.dumps(snapshot))

    def test_failed_provisioning_does_not_produce_positive_root_predicates(self):
        responses,policy=fixture()
        for raw in responses.values():
            if isinstance(raw,dict) and raw.get('type','').lower()=='microsoft.keyvault/vaults':raw['properties']['provisioningState']='Failed'
        rows=assess_snapshot(collect(responses),criteria=policy)['configuration_assessment']['results']
        self.assertTrue(all(r['result']=='UNKNOWN' for r in rows if r['check_id'].startswith('KV-') and r['check_id']!='KV-diagnostic-logs'))

    def test_schema_versions_prevent_old_readers_omitting_new_findings(self):
        responses,policy=fixture();snapshot=collect(responses);report=assess_snapshot(snapshot,criteria=policy)
        store=MemoryStore();manifest=save_run(store,snapshot,report)
        self.assertEqual('1.1',snapshot['schema_version']);self.assertEqual('1.1',report['schema_version']);self.assertEqual('1.1',manifest['schema_version'])
        old=copy.deepcopy(snapshot);old['schema_version']='1.0'
        for row in old['resources']:row.pop('configuration',None)
        validate_snapshot(old)
        reassessed=assess_snapshot(old,criteria=policy)
        self.assertFalse(any(r['result']=='PASS' for r in reassessed['configuration_assessment']['results']))

    def test_new_archive_cannot_omit_predicates_or_forge_mapping(self):
        from azure_at_rest.controls import overall_summary
        responses,policy=fixture();snapshot=collect(responses);report=assess_snapshot(snapshot,criteria=policy)
        for change in ('missing','mapping'):
            bad=copy.deepcopy(report);cfg=bad['configuration_assessment']
            if change=='missing':
                cfg['results'].pop();cfg['summary']['check_count']-=1;cfg['summary']['counts']['PASS']-=1
                bad['overall_summary']=overall_summary(bad)
            else:cfg['results'][0]['control_refs']=['UNREVIEWED']
            store=MemoryStore()
            with self.assertRaises(ValueError):save_run(store,snapshot,bad)
            self.assertEqual({},store.objects)


class FreshnessTests(unittest.TestCase):
    def test_stale_future_boundary_and_historical_replay(self):
        responses, policy = fixture()
        policy['max_observation_age_seconds'] = 3600
        snapshot = collect(responses)
        for resource in snapshot['resources']:
            resource['collected_at'] = '2026-09-19T12:00:00+00:00'
        for assessed_at, state in [('2026-09-19T13:00:00+00:00','fresh'),
                                   ('2026-09-19T13:00:01+00:00','stale'),
                                   ('2026-09-19T11:59:59+00:00','future')]:
            with patch('azure_at_rest.controls.now', return_value=assessed_at):
                report = assess_snapshot(snapshot, criteria=policy)
            rows = report['configuration_assessment']['results']
            self.assertTrue(all(row['freshness']['state'] == state for row in rows))
            self.assertTrue(all(row['result'] == ('PASS' if state == 'fresh' else 'UNKNOWN') for row in rows))
            store = MemoryStore()
            run = save_run(store, snapshot, report)
            with patch('azure_at_rest.controls.now', side_effect=AssertionError('historical clock called')):
                self.assertEqual(load_run(store,run['run_id'])['assessment'], report)

    def test_invalid_freshness_limits_and_forged_fresh_result(self):
        responses, policy = fixture()
        for value in (True, 0, -1, 31536001, 1.5, '3600'):
            policy['max_observation_age_seconds'] = value
            with self.assertRaises(ValueError):
                validate_policy(policy)
        policy['max_observation_age_seconds'] = 3600
        snapshot = collect(responses)
        with patch('azure_at_rest.controls.now',return_value='2040-01-01T00:00:00+00:00'):
            report = assess_snapshot(snapshot,criteria=policy)
        report['configuration_assessment']['results'][0]['freshness']['state'] = 'fresh'
        with self.assertRaises(ValueError):
            validate_pair(snapshot,report)


class OverallCoverageTests(unittest.TestCase):
    def test_failure_does_not_hide_unknown_configuration_coverage(self):
        from azure_at_rest.controls import overall_summary
        report = {'summary':{'counts':{'FAIL':0},'coverage_incomplete':False},
                  'configuration_assessment':{'identity_complete':True,'summary':{
                      'conclusion':'FAILURES_FOUND','counts':{'FAIL':1,'UNKNOWN':1,'ERROR':0}}}}
        self.assertEqual(overall_summary(report),{'conclusion':'FAILURES_FOUND','failed_check_count':1,'coverage_incomplete':True})
        report['configuration_assessment']['summary']['counts']['UNKNOWN']=0
        report['configuration_assessment']['identity_complete']=False
        self.assertTrue(overall_summary(report)['coverage_incomplete'])
