import importlib
import json
import unittest
from contextlib import contextmanager
from unittest.mock import Mock, patch
from cloud_governance.archive import encode, save_run
from cloud_governance.hosting import execute
from tests.test_archive import MemoryStore
from tests.test_controls import fixture, collect
from tests.test_operational import document
from tests.test_hosting import environment
from cloud_governance.workflow import assess_snapshot


class OperationalHostingTests(unittest.TestCase):
    def test_disabled_operations_do_not_open_storage(self):
        factory=Mock(side_effect=AssertionError('unexpected access'))
        for operation in ('operational-import','operational-report'):
            self.assertEqual('disabled',execute(operation,env={},factory=factory)['state'])
        factory.assert_not_called()

    def test_hosted_import_and_report_preserve_source(self):
        responses,policy=fixture();snapshot=collect(responses);store=MemoryStore()
        run=save_run(store,snapshot,assess_snapshot(snapshot,criteria=policy))['run_id']
        original=dict(store.objects)
        @contextmanager
        def factory(*args):yield store,None
        env={**environment(),'CG_OPERATIONAL_ENABLED':'true'}
        first=execute('operational-import',env=env,factory=factory,run_id=run,document=encode(document()),as_of='2026-09-19T21:00:00Z',max_age_hours=24)
        second=execute('operational-report',env=env,factory=factory,evidence_id=first['evidence_id'])
        self.assertEqual('complete',second['state'])
        self.assertTrue(store.read(second['pdf_key']).startswith(b'%PDF'))
        self.assertEqual(original,{k:store.objects[k] for k in original})

    def test_routes_opt_in_post_key_protected_and_reject_invalid_envelopes(self):
        import azure.functions as func
        import function_app
        try:
            with patch.dict('os.environ',{'CG_OPERATIONAL_ENABLED':'true'},clear=True):
                module=importlib.reload(function_app)
                functions=module.app.get_functions()
                self.assertEqual({'GenerateReport','ImportOperationalEvidence','GenerateOperationalReport'},{f.get_function_name() for f in functions})
                for function in functions:
                    trigger=json.loads(function.get_function_json())['bindings'][0]
                    self.assertEqual('FUNCTION',trigger['authLevel']);self.assertEqual(['POST'],trigger['methods'])
                for handler in (module.import_operational_evidence,module.generate_operational_report):
                    for body in (b'{}',b'{',b'{"evidence_id":"x","evidence_id":"y"}'):
                        with patch.object(module,'execute',side_effect=AssertionError('must reject')):
                            self.assertEqual(400,handler(func.HttpRequest('POST','https://example/api',body=body)).status_code)
                body={'run_id':'r-'+'a'*32,'document':document(),'as_of':'2026-09-19T21:00:00Z','max_age_hours':24}
                with patch.object(module,'execute',return_value={'state':'complete'}) as action:
                    response=module.import_operational_evidence(func.HttpRequest('POST','https://example/api',body=encode(body)))
                    self.assertEqual(201,response.status_code)
                    self.assertEqual('no-store',response.headers['Cache-Control'])
                    self.assertEqual('operational-import',action.call_args.args[0])
        finally:
            with patch.dict('os.environ',{},clear=True):importlib.reload(function_app)
