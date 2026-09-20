from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit, parse_qs

try:
    from azure.core import MatchConditions
    from azure.core.credentials import AccessToken
    from azure.core.exceptions import HttpResponseError, ResourceExistsError, ResourceNotFoundError, ServiceResponseError
    from azure.core.pipeline.transport import HttpTransport, HttpResponse
    from azure.storage.blob import ContainerClient
    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False

from cloud_governance.azure_adapters import ArmCredential, BlobStore, token_credential, verify_tenant
from cloud_governance.collector import CollectionError
from cloud_governance.workflow import Deadline, DeadlineExceeded

URL = 'https://fixturestore.blob.core.windows.net'
TENANT = '22222222-2222-2222-2222-222222222222'
CLIENT = '33333333-3333-3333-3333-333333333333'
SUB = '11111111-1111-1111-1111-111111111111'


class FakeContainer:
    def __init__(self):
        self.objects = {}
        self.lock = threading.Lock()
        self.lose_ack = False
        self.denied = False
        self.calls = []
        self.pages = None

    def get_blob_client(self, key):
        parent = self
        class Blob:
            def upload_blob(self, data, **kwargs):
                parent.calls.append((key, kwargs))
                with parent.lock:
                    if parent.denied:
                        raise HttpResponseError('SECRET', response=SimpleNamespace(status_code=403, reason='Forbidden', headers={}))
                    if key in parent.objects:
                        raise ResourceExistsError('SECRET', status_code=409)
                    parent.objects[key] = (data, kwargs['metadata'])
                if parent.lose_ack:
                    raise ServiceResponseError('SECRET lost acknowledgement')

            def get_blob_properties(self, **kwargs):
                if key not in parent.objects:
                    raise ResourceNotFoundError('SECRET', status_code=404)
                return SimpleNamespace(metadata=parent.objects[key][1])

            def download_blob(self, **kwargs):
                if key not in parent.objects:
                    raise ResourceNotFoundError('SECRET', status_code=404)
                return SimpleNamespace(readall=lambda: parent.objects[key][0])
        return Blob()

    def list_blobs(self, **kwargs):
        def pages():
            if self.pages is not None:
                yield from self.pages()
                return
            keys = sorted(k for k in self.objects if k.startswith(kwargs['name_starts_with']))
            for key in keys:
                yield [SimpleNamespace(name=key)]
        return SimpleNamespace(by_page=pages)

    def close(self):
        pass


@unittest.skipUnless(HAS_AZURE, 'Azure adapter tests require azure extras')
class AzureAdapterTests(unittest.TestCase):
    def store(self, client=None, **kwargs):
        return BlobStore(URL, 'evidence', None, 'project', client=client or FakeContainer(), sleep=lambda _: None, **kwargs)

    def test_explicit_credential_selection_and_sdk_token_refresh(self):
        with patch('azure.identity.ManagedIdentityCredential') as managed, patch('azure.identity.AzureCliCredential') as cli:
            token_credential(CLIENT, TENANT)
            self.assertEqual(CLIENT, managed.call_args.kwargs['client_id']);cli.assert_not_called()
            token_credential(CLIENT, TENANT, development=True)
            self.assertEqual(TENANT, cli.call_args.kwargs['tenant_id'])
        provider=unittest.mock.Mock()
        provider.get_token.side_effect=[AccessToken('first',int(time.time())+60),AccessToken('refreshed',int(time.time())+90)]
        adapter=ArmCredential(provider)
        self.assertEqual('first',adapter.get_token());self.assertEqual('refreshed',adapter.get_token())
        self.assertEqual(('https://management.azure.com/.default',),provider.get_token.call_args.args)
        provider.get_token.side_effect=RuntimeError('SECRET')
        with self.assertRaisesRegex(CollectionError,'^authentication_failed$'):adapter.get_token()
        provider.get_token.side_effect=None;provider.get_token.return_value=AccessToken('expired',0)
        with self.assertRaises(CollectionError):adapter.get_token()

    def test_tenant_preflight_uses_subscription_metadata(self):
        transport=unittest.mock.Mock()
        transport.get.return_value={'subscriptionId':SUB,'tenantId':TENANT,'state':'Enabled'}
        verify_tenant(transport,[SUB],TENANT)
        self.assertIn('/subscriptions/'+SUB+'?',transport.get.call_args.args[0])
        for changed in ({'tenantId':CLIENT},{'subscriptionId':CLIENT},{'state':'Disabled'}):
            transport.get.return_value={'subscriptionId':SUB,'tenantId':TENANT,'state':'Enabled',**changed}
            with self.assertRaises(CollectionError):verify_tenant(transport,[SUB],TENANT)
        with self.assertRaises(ValueError):verify_tenant(transport,[],TENANT)

    def test_key_validation_exact_bytes_and_fully_paged_listing(self):
        store=self.store()
        for key in ('runs/a/snapshot.json','runs/b/snapshot.json'):
            store.put_new(key,b'\x00test\xff')
        self.assertEqual(['runs/a/snapshot.json','runs/b/snapshot.json'],store.keys('runs/'))
        self.assertEqual(b'\x00test\xff',store.read('runs/a/snapshot.json'))
        for bad in ('../x','/x','runs//x','runs/../x','https://evil.example/x','runs/a?sig=x'):
            with self.subTest(key=bad),self.assertRaises(ValueError):store.put_new(bad,b'x')
        for bad_url in ('https://evil.example','https://fixturestore.blob.core.windows.net/?sig=x','http://fixturestore.blob.core.windows.net'):
            with self.assertRaises(ValueError):BlobStore(bad_url,'evidence',None,client=FakeContainer())
        with self.assertRaises(FileNotFoundError):store.read('runs/missing.json')

    def test_create_only_conflict_even_for_identical_bytes_and_concurrent_writes(self):
        store=self.store()
        def put(_):
            try:store.put_new('runs/one.json',b'unchanged');return True
            except FileExistsError:return False
        with ThreadPoolExecutor(max_workers=8) as pool:outcomes=list(pool.map(put,range(8)))
        self.assertEqual(1,sum(outcomes));self.assertEqual(b'unchanged',store.read('runs/one.json'))
        for _,opts in store.client.calls:
            self.assertFalse(opts['overwrite']);self.assertEqual('BlockBlob',opts['blob_type'])
            self.assertEqual(MatchConditions.IfMissing,opts['match_condition'])

    def test_lost_ack_reconciles_only_same_write_and_exact_bytes(self):
        client=FakeContainer();client.lose_ack=True;store=self.store(client)
        store.put_new('runs/a.json',b'committed')
        self.assertEqual(1,len(client.calls))
        with self.assertRaises(FileExistsError):store.put_new('runs/a.json',b'committed')
        bad=client.get_blob_client('project/runs/b.json')
        original=bad.upload_blob
        def corrupt(data,**kwargs):
            try:original(data,**kwargs)
            except ServiceResponseError:
                client.objects['project/runs/b.json']=(b'corrupt',kwargs['metadata'])
                raise
        bad.upload_blob=corrupt
        with patch.object(client,'get_blob_client',return_value=bad),self.assertRaisesRegex(OSError,'reconciliation_mismatch'):
            store.put_new('runs/b.json',b'intended')

    def test_denied_and_partial_listing_fail_without_payload_leak(self):
        client=FakeContainer();client.denied=True;store=self.store(client)
        with self.assertRaises(PermissionError) as caught:store.put_new('runs/a.json',b'x')
        self.assertNotIn('SECRET',str(caught.exception));self.assertEqual({},client.objects)
        def pages():
            yield [SimpleNamespace(name='project/runs/a.json')]
            raise HttpResponseError('SECRET', response=SimpleNamespace(status_code=403, reason='Forbidden', headers={}))
        client.pages=pages
        with self.assertRaises(PermissionError):store.keys('runs/')
        client.pages=lambda: iter([[SimpleNamespace(name='other/runs/a.json')]])
        with self.assertRaises(ValueError):store.keys('runs/')

    def test_transient_reads_retry_bounded_and_deadline_is_checked(self):
        store=self.store(retries=2);blob=unittest.mock.Mock()
        blob.download_blob.side_effect=ServiceResponseError('SECRET')
        with patch.object(store.client,'get_blob_client',return_value=blob),self.assertRaises(OSError):store.read('runs/a.json')
        self.assertEqual(3,blob.download_blob.call_count)
        clock=unittest.mock.Mock(side_effect=[0,2]);store.deadline=Deadline(1,clock)
        with self.assertRaises(DeadlineExceeded):store.read('runs/a.json')

    def test_timeout_before_commit_retries_same_marker_and_never_relaxes_condition(self):
        client=FakeContainer();store=self.store(client)
        blob=client.get_blob_client('project/runs/a.json');original=blob.upload_blob;attempts=[]
        def upload(data,**kwargs):
            attempts.append(kwargs)
            if len(attempts)==1:raise ServiceResponseError('SECRET timeout before commit')
            return original(data,**kwargs)
        blob.upload_blob=upload
        with patch.object(client,'get_blob_client',return_value=blob):store.put_new('runs/a.json',b'saved')
        self.assertEqual(2,len(attempts))
        self.assertEqual(attempts[0]['metadata'],attempts[1]['metadata'])
        self.assertTrue(all(a['match_condition']==MatchConditions.IfMissing and not a['overwrite'] for a in attempts))

    def test_real_sdk_sends_conditional_single_and_block_commit_requests(self):
        class Response(HttpResponse):
            def __init__(self,request):
                super().__init__(request,None);self.status_code=201;self.reason='Created'
                self.headers={'ETag':'"fixture-etag"','Last-Modified':'Sat, 19 Sep 2026 00:00:00 GMT','x-ms-request-id':'fixture'}
                self.content_type='application/xml'
            def body(self):return b''
        class Transport(HttpTransport):
            def __init__(self):self.requests=[]
            def open(self):pass
            def close(self):pass
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def send(self,request,**kwargs):self.requests.append(request);return Response(request)
        for payload in (b'a',b'abcdefghijklmnop'):
            wire=Transport();credential=SimpleNamespace(get_token=lambda *args, **kwargs: AccessToken('offline-fixture-token',int(time.time())+3600))
            client=ContainerClient(URL,'evidence',credential=credential,transport=wire,retry_total=0,max_single_put_size=4,max_block_size=4)
            store=self.store(client);store.put_new('runs/a.json',payload)
            commits=[r for r in wire.requests if parse_qs(urlsplit(r.url).query).get('comp')!=['block']]
            self.assertEqual(1,len(commits));self.assertEqual('*',commits[0].headers['If-None-Match'])
            self.assertIn('x-ms-meta-cg_write_id',commits[0].headers)
            self.assertTrue(all(r.method=='PUT' for r in wire.requests))
            if len(payload)>4:self.assertGreater(len(wire.requests),2)
