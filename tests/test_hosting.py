from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from io import BytesIO
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

from cloud_governance.archive import load_run, publish_pdf, save_run
from cloud_governance.collector import FixtureTransport, SUBSCRIPTIONS_API, endpoint
from cloud_governance.hosting import ConfigurationError, ExecutionError, LOCKS, Settings, execute, resources, schedule
from tests.test_archive import evidence, MemoryStore
from tests.test_azure_adapters import CLIENT, TENANT, SUB, URL, FakeContainer, HAS_AZURE

ROOT=Path(__file__).resolve().parents[1]
HAS_HOST=HAS_AZURE and all(importlib.util.find_spec(n) for n in ('azure.functions','reportlab','pypdf'))


def environment():
    return {'CG_COLLECTION_ENABLED':'true','CG_REPORT_ENABLED':'true', 'CG_COLLECTION_SCHEDULE':'0 0 3 * * *',
            'CG_TENANT_ID':TENANT,'CG_MANAGED_IDENTITY_CLIENT_ID':CLIENT,'CG_SUBSCRIPTION_IDS':SUB,
            'CG_EVIDENCE_ACCOUNT_URL':URL,'CG_EVIDENCE_CONTAINER':'evidence','CG_EVIDENCE_PREFIX':'project',
            'CG_RUNTIME_STORAGE_ACCOUNT':'fixtureruntime','AzureWebJobsStorage__accountName':'fixtureruntime'}


class ConfigurationTests(unittest.TestCase):
    def test_default_is_disabled_and_does_not_touch_credentials_or_store(self):
        factory=Mock(side_effect=AssertionError('no resources'))
        self.assertEqual('disabled',execute('collect',env={},factory=factory)['state'])
        self.assertEqual('disabled',execute('report',env={},factory=factory)['state'])
        self.assertEqual('',schedule({}));factory.assert_not_called()

    def test_explicit_scope_and_separate_runtime_storage_are_required(self):
        valid=environment();s=Settings.parse(valid)
        self.assertEqual((SUB,),s.subscriptions);self.assertFalse(s.development)
        for key,value in [('CG_TENANT_ID',''),('CG_SUBSCRIPTION_IDS',''),('CG_SUBSCRIPTION_IDS',SUB+',bad'),
                          ('CG_MANAGED_IDENTITY_CLIENT_ID','system'),('CG_EVIDENCE_ACCOUNT_URL',URL+'?sig=SECRET'),
                          ('CG_EVIDENCE_PREFIX','../x'),('CG_RUNTIME_STORAGE_ACCOUNT','fixturestore'),
                          ('AzureWebJobsStorage__accountName','different'),('AzureWebJobsStorage','SECRET'),
                          ('CG_COLLECTION_BUDGET_SECONDS','9999'),('CG_REPORT_BUDGET_SECONDS','231'),('CG_LOCK_WAIT_SECONDS','-1')]:
            with self.subTest(key=key),self.assertRaises(ConfigurationError):Settings.parse({**valid,key:value})
        with self.assertRaises(ConfigurationError):schedule({'CG_COLLECTION_ENABLED':'true'})
        with self.assertRaises(ConfigurationError):schedule({'CG_COLLECTION_SCHEDULE':'@everyminute'})
        for cron in ('99 * * * * *', '*/0 * * * * *', '0 0 0 0 * *', '0 0 0 5-2 * *'):
            with self.assertRaises(ConfigurationError):schedule({'CG_COLLECTION_SCHEDULE':cron})

    def test_cli_development_credentials_cannot_be_selected_on_azure_host(self):
        env={**environment(),'CG_AUTH_MODE':'azure_cli','CG_LOCAL_DEVELOPMENT':'true'}
        self.assertTrue(Settings.parse(env).development)
        self.assertIsNone(Settings.parse({**env,'CG_MANAGED_IDENTITY_CLIENT_ID':''}).client_id)
        for flag in ('WEBSITE_HOSTNAME','WEBSITE_INSTANCE_ID'):
            with self.assertRaises(ConfigurationError):Settings.parse({**env,flag:'host'})
        with self.assertRaises(ConfigurationError):Settings.parse({**env,'CG_LOCAL_DEVELOPMENT':'false'})

    def test_early_failures_are_sanitized_and_stage_identified(self):
        for env in ({'CG_COLLECTION_ENABLED':'true'}, environment()):
            @contextmanager
            def broken(*args):
                raise RuntimeError('SECRET SDK BODY')
                yield
            with self.assertLogs('cloud_governance',level='INFO') as logs,self.assertRaises(ExecutionError) as caught:
                execute('collect',env=env,factory=broken)
            self.assertNotIn('SECRET',str(caught.exception));self.assertNotIn('SECRET',''.join(logs.output))
            self.assertEqual('failed',caught.exception.outcome['state'])
            self.assertIn('started',''.join(logs.output))

    def test_resources_always_close_credential_when_blob_close_fails(self):
        from cloud_governance.workflow import Deadline
        credential, store = Mock(), Mock()
        store.close.side_effect = RuntimeError('synthetic cleanup failure')
        with patch('cloud_governance.hosting.token_credential', return_value=credential), patch('cloud_governance.hosting.BlobStore', return_value=store):
            with self.assertRaisesRegex(RuntimeError, 'synthetic cleanup failure'):
                with resources(Settings.parse(environment()), Deadline(30), 'report'):
                    pass
        store.close.assert_called_once_with()
        credential.close.assert_called_once_with()

    def test_resources_close_credential_when_store_construction_fails(self):
        from cloud_governance.workflow import Deadline
        credential = Mock()
        with patch('cloud_governance.hosting.token_credential', return_value=credential), patch('cloud_governance.hosting.BlobStore', side_effect=ValueError('synthetic')):
            with self.assertRaises(ValueError):
                with resources(Settings.parse(environment()), Deadline(30), 'report'):
                    self.fail('must not enter')
        credential.close.assert_called_once_with()

    def test_overlap_rejected_and_configured_wait_is_bounded(self):
        LOCKS['collect'].acquire()
        try:
            with self.assertLogs('cloud_governance'),self.assertRaises(ExecutionError) as caught:execute('collect',env=environment(),factory=Mock())
            self.assertEqual('operation_busy',caught.exception.outcome['code'])
        finally:LOCKS['collect'].release()
        self.assertEqual(2,Settings.parse({**environment(),'CG_LOCK_WAIT_SECONDS':'2'}).lock_wait)


@unittest.skipUnless(HAS_HOST,'Hosted tests require azure/pdf/test extras')
class HostingTests(unittest.TestCase):
    def fixture_factory(self,store):
        fixture=json.loads((ROOT/'examples/demo-fixture.json').read_text())
        fixture['responses'][endpoint('/subscriptions/'+SUB,SUBSCRIPTIONS_API)]={'subscriptionId':SUB,'tenantId':TENANT,'state':'Enabled'}
        @contextmanager
        def factory(settings,deadline,operation):
            yield store,FixtureTransport(fixture['responses']) if operation=='collect' else None
        return factory

    def test_hosted_fixture_through_blob_adapter_preserves_failures_and_exact_history(self):
        from cloud_governance.azure_adapters import BlobStore
        from pypdf import PdfReader
        client=FakeContainer();store=BlobStore(URL,'evidence',None,'project',client=client)
        factory=self.fixture_factory(store)
        with patch('subprocess.run',side_effect=AssertionError('No CLI')):
            first=execute('collect',env=environment(),factory=factory)
            original=dict(client.objects)
            second=execute('collect',env=environment(),factory=factory)
            self.assertNotEqual(first['run_id'],second['run_id'])
            self.assertEqual('complete',first['state']);self.assertEqual('FAILURES_FOUND',first['assessment_conclusion'])
            self.assertEqual(3,first['counts']['FAIL'])
            with patch('cloud_governance.collector.Collector.collect',side_effect=AssertionError('No recollect')),patch('cloud_governance.assessment.assess',side_effect=AssertionError('No reassess')),patch('cloud_governance.archive.make_context',side_effect=AssertionError('No fresh context')):
                a=execute('report',run_id=first['run_id'],env=environment(),factory=factory)
                b=execute('report',run_id=first['run_id'],env=environment(),factory=factory)
        self.assertNotEqual(a['report_id'],b['report_id'])
        self.assertEqual(original,{k:client.objects[k] for k in original})
        text=''.join(p.extract_text() for p in PdfReader(BytesIO(store.read(a['pdf_key']))).pages)
        self.assertIn(TENANT,text);self.assertIn('azure_blob',text);self.assertIn('not_verified',text)
        self.assertNotIn('The local store prevents',text)
        context=load_run(store,first['run_id'])['context']
        self.assertEqual('arm_subscription_metadata',context['execution_provenance']['tenant_validation'])

    def test_preflight_mismatch_prevents_any_evidence_write(self):
        store=MemoryStore()
        @contextmanager
        def factory(*args):yield store,Mock(get=Mock(return_value={'subscriptionId':SUB,'tenantId':CLIENT,'state':'Enabled'}))
        with self.assertLogs('cloud_governance'),self.assertRaises(ExecutionError) as caught:execute('collect',env=environment(),factory=factory)
        self.assertEqual('tenant_preflight',caught.exception.outcome['stage']);self.assertEqual({},store.objects)

    def test_registered_http_is_key_protected_post_and_timer_has_no_startup_run(self):
        import function_app
        with patch.dict('os.environ',{},clear=True):
            module=importlib.reload(function_app)
            funcs=module.app.get_functions()
            self.assertEqual(['GenerateReport'],[f.get_function_name() for f in funcs])
            trigger=json.loads(funcs[0].get_function_json())['bindings'][0]
            self.assertEqual('FUNCTION',trigger['authLevel']);self.assertEqual(['POST'],trigger['methods'])
        with patch.dict('os.environ',environment(),clear=True):
            module=importlib.reload(function_app)
            triggers=[b for f in module.app.get_functions() for b in json.loads(f.get_function_json())['bindings']]
            timer=next(b for b in triggers if b['type']=='timerTrigger')
            self.assertFalse(timer['runOnStartup']);self.assertTrue(timer['useMonitor'])
            with patch.object(module,'execute',return_value={'state':'complete','assessment_conclusion':'FAILURES_FOUND'}) as action:
                module.collect_evidence(None)
                action.assert_called_once_with('collect')
        with patch.dict('os.environ',{},clear=True):importlib.reload(function_app)

    def test_report_trigger_requires_exact_id_and_never_creates_anonymous_route(self):
        import azure.functions as func
        import function_app
        module=importlib.reload(function_app)
        for body in ({},{'run_id':'latest'},{'run_id':'r-'+'a'*32,'automatic':True}):
            req=func.HttpRequest('POST','https://fixture/api/reports',body=json.dumps(body).encode())
            with patch.object(module,'execute',side_effect=AssertionError('must reject')):
                self.assertEqual(400,module.generate_report(req).status_code)
        req=func.HttpRequest('POST','https://fixture/api/reports',body=json.dumps({'run_id':'r-'+'a'*32}).encode())
        with patch.object(module,'execute',return_value={'state':'disabled'}):self.assertEqual(503,module.generate_report(req).status_code)
        with patch.object(module,'execute',return_value={'state':'complete','report_id':'p-'+'b'*32}):
            response=module.generate_report(req);self.assertEqual(201,response.status_code)
            self.assertEqual('no-store',response.headers['Cache-Control'])

    def test_http_maps_structured_errors_without_parsing_exception_text(self):
        import azure.functions as func
        import function_app
        request = func.HttpRequest('POST', 'https://fixture/api/reports', body=json.dumps({'run_id':'r-'+'a'*32}).encode())
        for code, status in [('operation_busy', 409), ('operation_failed', 500)]:
            outcome = {'operation':'report', 'state':'failed', 'invocation_id':'a'*32, 'stage':'overlap_guard', 'code':code}
            error = ExecutionError(outcome)
            self.assertEqual(code, str(error))
            with patch.object(function_app, 'execute', side_effect=error):
                response = function_app.generate_report(request)
            self.assertEqual(status, response.status_code)
            self.assertEqual(outcome, json.loads(response.get_body()))
            self.assertEqual('no-store', response.headers['Cache-Control'])

    def test_concurrent_pdf_generations_keep_old_run_and_readable_embedded_fonts(self):
        from pypdf import PdfReader
        snapshot,report=evidence();store=MemoryStore();run=save_run(store,snapshot,report);old=dict(store.objects)
        with ThreadPoolExecutor(max_workers=4) as pool:
            reports=list(pool.map(lambda _:publish_pdf(store,run['run_id']),range(4)))
        self.assertEqual(4,len({r['report_id'] for r in reports}))
        self.assertEqual(old,{k:store.objects[k] for k in old})
        for result in reports:
            reader=PdfReader(BytesIO(store.read(result['pdf']['key'])))
            self.assertIn('safe-store',''.join(p.extract_text() for p in reader.pages))

    def test_budget_expiry_after_render_leaves_failure_without_completed_report(self):
        from cloud_governance.workflow import DeadlineExceeded
        snapshot,report=evidence();store=MemoryStore();run=save_run(store,snapshot,report);old=dict(store.objects)
        class Budget:
            expired=False
            def check(self):
                if self.expired:raise DeadlineExceeded('execution_budget_exceeded')
        budget=Budget()
        def render(*args):budget.expired=True;return b'%PDF-1.4\n%%EOF'
        with patch('cloud_governance.pdf_report.render_pdf',side_effect=render),self.assertRaises(RuntimeError):
            publish_pdf(store,run['run_id'],deadline=budget)
        self.assertEqual(old,{k:store.objects[k] for k in old})
        reports=[k for k in store.objects if k.startswith('reports/')]
        self.assertTrue(any(k.endswith('/failure.json') for k in reports))
        self.assertFalse(any(k.endswith(('/manifest.json','/report.pdf')) for k in reports))

    def test_packaging_allowlist_excludes_local_data_and_contains_runtime_inputs(self):
        from scripts.package_functions import package
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'function.zip';package(path)
            names=zipfile.ZipFile(path).namelist()
            self.assertTrue({'function_app.py','host.json','requirements.txt','constraints.txt','cloud_governance/program_scope.json'} <= set(names))
            self.assertFalse(any(n.startswith(('tests/','examples/','evidence/','output/','.git','local.settings')) for n in names))
            with self.assertRaises(FileExistsError):package(path)

    def test_hosted_all_service_configuration_and_graph_pipeline(self):
        from cloud_governance.graph import FixtureGraphTransport
        from tests.test_graph import TENANT as GRAPH_TENANT
        from tests.helpers import SUB as GRAPH_SUB
        source=ROOT/'examples/control-suite'
        arm=json.loads((source/'arm-fixture.json').read_text())['responses']
        graph=json.loads((source/'graph-fixture.json').read_text())['responses']
        arm[endpoint('/subscriptions/'+GRAPH_SUB,SUBSCRIPTIONS_API)]={'subscriptionId':GRAPH_SUB,'tenantId':GRAPH_TENANT,'state':'Enabled'}
        store=MemoryStore()
        @contextmanager
        def factory(settings,deadline,operation):
            transport=FixtureTransport(arm)
            transport.graph_transport=FixtureGraphTransport(graph)
            yield store,transport
        env={**environment(),'CG_GRAPH_ENABLED':'true','CG_TENANT_ID':GRAPH_TENANT,'CG_SUBSCRIPTION_IDS':GRAPH_SUB,
             'CG_ASSESSMENT_CRITERIA_JSON':(source/'criteria.json').read_text()}
        outcome=execute('collect',env=env,factory=factory)
        self.assertEqual('complete',outcome['state'])
        from cloud_governance.controls import CHECKS
        self.assertEqual({'PASS':len(CHECKS)-1,'FAIL':1,'UNKNOWN':0,'ERROR':0},outcome['configuration_summary']['counts'])
        saved=load_run(store,outcome['run_id'])
        self.assertTrue(saved['snapshot']['identity_evidence']['verified_tenant'])
        self.assertEqual(23,len({r['catalog_ref'].split('-')[0] for r in saved['assessment']['configuration_assessment']['results']}))

    def test_invalid_criteria_and_missing_graph_transport_fail_before_archive(self):
        for values in ({'CG_ASSESSMENT_CRITERIA_JSON':'{"checks":{},"checks":{}}'},{'CG_GRAPH_ENABLED':'yes'}):
            with self.assertRaises(ConfigurationError):Settings.parse({**environment(),**values})
        store=MemoryStore()
        with self.assertLogs('cloud_governance'),self.assertRaises(ExecutionError):
            execute('collect',env={**environment(),'CG_GRAPH_ENABLED':'true'},factory=self.fixture_factory(store))
        self.assertEqual({},store.objects)
