from cloud_governance import report_model
import io
import json
import unittest
from cloud_governance.collector import ArmTransport,CollectionError,Collector,MAX_RESPONSE_BYTES,INVENTORY_API,endpoint
from cloud_governance.graph import GraphTransport
from cloud_governance.snapshot import validate_snapshot
from cloud_governance.workflow import assess_snapshot
from cloud_governance.archive import save_run,load_run,publish_pdf
from tests.test_archive import MemoryStore
from tests.helpers import SUB


class Credential:
    def get_token(self):return 'fixture-token'


class TrackedResponse(io.BytesIO):
    def __init__(self,value):super().__init__(value);self.read_sizes=[]
    def read(self,size=-1):self.read_sizes.append(size);return super().read(size)


class Opener:
    def __init__(self,payload):self.response=TrackedResponse(payload);self.calls=0
    def open(self,request,timeout):self.calls+=1;return self.response


class TransportBoundsTests(unittest.TestCase):
    def test_arm_and_graph_read_at_most_limit_plus_one_close_and_do_not_retry_oversize(self):
        for cls,url in [(ArmTransport,endpoint('/subscriptions/'+SUB+'/resources',INVENTORY_API)),
                        (GraphTransport,'https://graph.microsoft.com/v1.0/organization')]:
            opener=Opener(b'{"SECRET-CANARY":"'+b'x'*200+b'"}')
            with self.assertRaises(CollectionError) as caught:
                cls(Credential(),opener=opener,max_response_bytes=64).get(url)
            self.assertEqual('response_size_limit',caught.exception.code)
            self.assertEqual([65],opener.response.read_sizes);self.assertTrue(opener.response.closed)
            self.assertEqual(1,opener.calls);self.assertNotIn('SECRET',str(caught.exception))

    def test_exact_boundary_valid_json_succeeds_and_invalid_limits_fail_early(self):
        payload=b'{"value":[]}'
        opener=Opener(payload);transport=ArmTransport(Credential(),opener=opener,max_response_bytes=len(payload))
        self.assertEqual({'value':[]},transport.get(endpoint('/subscriptions',INVENTORY_API)))
        quoted={'text':'[{}]'+chr(92)+chr(34)+'['*200}
        payload=json.dumps(quoted).encode()
        self.assertEqual(quoted,ArmTransport(Credential(),opener=Opener(payload)).get(endpoint('/subscriptions',INVENTORY_API)))
        for limit in (None,False,0,-1,MAX_RESPONSE_BYTES+1):
            with self.assertRaises(ValueError):ArmTransport(Credential(),max_response_bytes=limit)

    def test_duplicate_nonfinite_bad_encoding_and_deep_json_are_safe_errors(self):
        for payload in (b'{"value":[],"value":["SECRET-CANARY"]}',b'{"nested":{"enabled":true,"enabled":false}}',
                        b'{"x":NaN}',b'{"x":1e999}',b'{"x":Infinity}',b'{"x":-Infinity}',b'\xff',b'{"x":'+b'['*2000+b'0'+b']'*2000+b'}'):
            opener=Opener(payload)
            with self.assertRaises(CollectionError) as caught:ArmTransport(Credential(),opener=opener).get(endpoint('/subscriptions',INVENTORY_API))
            self.assertEqual('malformed_response',caught.exception.code);self.assertTrue(opener.response.closed)

    def test_oversized_inventory_retains_incomplete_error_through_archive_and_pdf(self):
        transport=ArmTransport(Credential(),opener=Opener(b'{"value":['+b' '*200+b']}'),max_response_bytes=64)
        snapshot=Collector(transport,mode='offline_fixture').collect([SUB]);validate_snapshot(snapshot)
        self.assertFalse(snapshot['inventory']['complete']);self.assertEqual('response_size_limit',snapshot['errors'][0]['code'])
        report=assess_snapshot(snapshot);self.assertTrue(report_model.overall(report)['coverage_incomplete'])
        store=MemoryStore();run=save_run(store,snapshot,report)['run_id'];before=dict(store.objects);pdf=publish_pdf(store,run)
        from pypdf import PdfReader
        text=' '.join(page.extract_text() for page in PdfReader(io.BytesIO(store.read(pdf['pdf']['key']))).pages)
        self.assertIn('response_size_limit',text)
        self.assertEqual(report,load_run(store,run)['assessment']);self.assertTrue(all(store.objects[k]==v for k,v in before.items()))
