import copy
import io
import json
import time
import unittest
from contextlib import contextmanager
from unittest.mock import Mock,patch
from urllib.error import HTTPError
from azure_at_rest.archive import encode,save_run
from azure_at_rest.collector import CollectionError
from azure_at_rest.hosting import Settings,execute,ExecutionError
from azure_at_rest.kubernetes_collect import target,listing,collect,KubernetesTransport,AUDIENCE
from azure_at_rest.kubernetes_evidence import load,publish
from azure_at_rest.workflow import Deadline,assess_snapshot
from tests.test_kubernetes_evidence import document,criteria,AS_OF
from tests.test_controls import fixture,collect as fixture_collect
from tests.test_archive import MemoryStore
from tests.test_hosting import environment

class KubernetesCollectionTests(unittest.TestCase):
    def setUp(self):
        responses,policy=fixture();self.snapshot=fixture_collect(responses);self.snapshot['mode']='azure_live'
        self.cluster=next(r['id'].lower() for r in self.snapshot['resources'] if r['type'].lower()=='microsoft.containerservice/managedclusters')
        self.store=MemoryStore();self.run=save_run(self.store,self.snapshot,assess_snapshot(self.snapshot,criteria=policy))['run_id']
        self.config={'cluster_id':self.cluster,'endpoint':'https://aks.example.test','ca_pem':'-----BEGIN CERTIFICATE-----\nTEST\n-----END CERTIFICATE-----',
            'namespace':'example','criteria':criteria(),'max_age_seconds':3600}
        self.arm=Mock();self.arm.get.return_value={'id':self.cluster,'properties':{'fqdn':'aks.example.test','aadProfile':{'managed':True}}}
        self.provenance=Settings.parse(environment()).provenance('workload-collect','a'*32)
        doc=document(self.cluster)
        self.pods=doc['pods'];self.nodes=doc['nodes']
        for item in (self.pods,self.nodes):item.setdefault('metadata',{})['resourceVersion']='123'

    def test_authenticated_collection_projects_and_archives_without_secrets(self):
        transport=Mock();transport.get.side_effect=[self.pods,self.nodes];factory=Mock(return_value=transport)
        manifest=collect(self.store,self.run,self.config,self.arm,Mock(),Deadline(30),provenance=self.provenance,transport_factory=factory)
        saved=load(self.store,manifest['evidence_id'])
        self.assertEqual(8,saved['report']['summary']['counts']['PASS'])
        self.assertEqual('azure_live',saved['report']['mode'])
        self.assertEqual('complete',saved['report']['collection_source']['pods']['state'])
        self.assertNotIn('SECRET-CANARY',b''.join(self.store.objects.values()).decode())
        self.assertEqual(['/api/v1/namespaces/example/pods','/api/v1/nodes'],[c.args[0] for c in transport.get.call_args_list])

    def test_unverified_endpoint_and_cluster_never_request_kubernetes_token(self):
        for alteration in ('fqdn','id','aad'):
            arm=copy.deepcopy(self.arm.get.return_value)
            if alteration=='fqdn':arm['properties']['fqdn']='other.example.test'
            elif alteration=='id':arm['id']+='/other'
            else:arm['properties']['aadProfile']['managed']=False
            self.arm.get.return_value=arm;factory=Mock();before=dict(self.store.objects)
            with self.assertRaises(ValueError):collect(self.store,self.run,self.config,self.arm,Mock(),Deadline(30),provenance=self.provenance,transport_factory=factory)
            factory.assert_not_called();self.assertEqual(before,self.store.objects)

    def test_import_cannot_claim_authenticated_collection(self):
        doc=document(self.cluster);doc['mode']='azure_live'
        with self.assertRaises(ValueError):publish(self.store,self.run,encode(doc),criteria=criteria(),as_of=AS_OF,max_age_seconds=3600)

    def test_denied_listing_archives_incomplete_result(self):
        transport=Mock();transport.get.side_effect=[CollectionError('http_error',403),self.nodes]
        manifest=collect(self.store,self.run,self.config,self.arm,Mock(),Deadline(30),provenance=self.provenance,transport_factory=Mock(return_value=transport))
        report=load(self.store,manifest['evidence_id'])['report']
        self.assertTrue(report['summary']['coverage_incomplete']);self.assertEqual('INCOMPLETE',report['summary']['conclusion'])
        self.assertEqual(403,report['collection_source']['pods']['http_status'])

    def test_pages_preserve_snapshot_and_detect_cycles_version_changes_and_limits(self):
        first=copy.deepcopy(self.pods);first['metadata']['continue']='opaque+/token'
        second=copy.deepcopy(self.pods);second['items']=[]
        transport=Mock();transport.get.side_effect=[first,second]
        result,state=listing(transport,'pods','PodList',max_pages=3,max_items=1000)
        self.assertEqual('complete',state['state']);self.assertEqual(1,len(result['items']))
        self.assertEqual('opaque+/token',transport.get.call_args_list[1].args[1])
        for last,expected in [(first,'pagination_cycle'),({**second,'metadata':{'resourceVersion':'124'}},'resource_version_changed')]:
            transport.get.side_effect=[first,last]
            result,state=listing(transport,'pods','PodList',max_pages=3,max_items=1000)
            self.assertEqual(expected,state['state']);self.assertTrue(result['metadata']['continue'])
        transport.get.side_effect=[first]
        self.assertEqual('page_limit',listing(transport,'pods','PodList',max_pages=1,max_items=1000)[1]['state'])
        transport.get.side_effect=[first]
        self.assertEqual('population_limit',listing(transport,'pods','PodList',max_pages=1,max_items=0)[1]['state'])

    def test_transport_get_only_fixed_paths_aks_audience_and_bounded_retries(self):
        credential=Mock();credential.get_token.return_value=Mock(token='PRIVATE-TOKEN',expires_on=time.time()+300)
        opener=Mock();response=io.BytesIO(encode(self.pods));opener.open.return_value=response
        deadline=Mock();deadline.remaining.return_value=30
        with patch('azure_at_rest.kubernetes_collect.ssl.create_default_context') as tls:
            transport=KubernetesTransport(self.config,credential,deadline,opener=opener)
            tls.assert_called_once_with(cadata=self.config['ca_pem'])
        for path in ('/api/v1/secrets','https://evil.test','/api/v1/pods'):
            with self.assertRaises(ValueError):transport.get(path,'')
        credential.get_token.assert_not_called()
        transport.get('/api/v1/namespaces/example/pods','a+/b')
        credential.get_token.assert_called_once_with(AUDIENCE)
        req=opener.open.call_args.args[0];self.assertEqual('GET',req.method)
        self.assertIn('continue=a%2B%2Fb',req.full_url)
        error=HTTPError(req.full_url,429,'PRIVATE',{},io.BytesIO(b'SECRET'))
        opener.open.side_effect=[error,io.BytesIO(encode(self.pods))]
        transport.get('/api/v1/namespaces/example/pods','');deadline.sleep.assert_called_once_with(1)
        opener.open.side_effect=[HTTPError(req.full_url,403,'PRIVATE',{},io.BytesIO(b'SECRET'))]
        with self.assertRaises(CollectionError) as caught:transport.get('/api/v1/namespaces/example/pods','')
        self.assertEqual('http_error',str(caught.exception));self.assertEqual(403,caught.exception.status)

    def test_configuration_rejects_arbitrary_urls_and_private_keys(self):
        for url in ('http://aks.example.test','https://aks.example.test@evil.test','https://aks.example.test:443','https://aks.example.test/path','https://aks.example.test?token=x','https://127.0.0.1/#x'):
            with self.assertRaises(ValueError):target({**self.config,'endpoint':url})
        with self.assertRaises(ValueError):target({**self.config,'ca_pem':'-----BEGIN PRIVATE KEY-----'})
        with self.assertRaises(Exception):KubernetesTransport(self.config,Mock(),Deadline(30))

    def test_host_opt_in_scope_and_safe_failure(self):
        factory=Mock();self.assertEqual('disabled',execute('workload-collect',env={},factory=factory)['state']);factory.assert_not_called()
        config=self.config;env={**environment(),'CG_KUBERNETES_COLLECTION_ENABLED':'true','CG_KUBERNETES_TARGET_JSON':json.dumps(config)}
        env['CG_SUBSCRIPTION_IDS']=self.cluster.split('/')[2]
        @contextmanager
        def resources(*args):yield self.store,self.arm
        with patch('azure_at_rest.hosting.verify_tenant'),patch('azure_at_rest.kubernetes_collect.collect') as operation:
            operation.return_value={'evidence_id':'k-'+'b'*32,'source_run_id':self.run,'generated_at':AS_OF,'summary':{}}
            result=execute('workload-collect',run_id=self.run,env=env,factory=resources)
            self.assertEqual('complete',result['state']);operation.assert_called_once()
            operation.reset_mock()
            with self.assertRaises(ExecutionError):execute('workload-collect',run_id=self.run,env={**env,'CG_RESOURCE_GROUP':'other'},factory=resources)
            operation.assert_not_called()

    def test_denied_collection_pdf_exposes_failure_state_and_preserves_archive(self):
        from azure_at_rest.kubernetes_evidence import publish_pdf
        from pypdf import PdfReader
        transport=Mock();transport.get.side_effect=[CollectionError('http_error',403),self.nodes]
        manifest=collect(self.store,self.run,self.config,self.arm,Mock(),Deadline(30),provenance=self.provenance,transport_factory=Mock(return_value=transport))
        before=dict(self.store.objects)
        pdf=publish_pdf(self.store,manifest['evidence_id'])
        text=' '.join(p.extract_text() for p in PdfReader(io.BytesIO(self.store.read(pdf['pdf']['key']))).pages)
        self.assertIn('403',text);self.assertIn('http_error',text);self.assertIn('INCOMPLETE',text)
        for key,value in before.items():self.assertEqual(value,self.store.objects[key])

    def test_invalid_token_and_oversize_response_never_leak_provider_details(self):
        credential=Mock();credential.get_token.return_value=Mock(token='PRIVATE-TOKEN',expires_on=0)
        opener=Mock()
        with patch('azure_at_rest.kubernetes_collect.ssl.create_default_context'):
            transport=KubernetesTransport(self.config,credential,Deadline(30),opener=opener)
        with self.assertRaises(CollectionError) as caught:transport.get('/api/v1/nodes','')
        self.assertEqual('authentication_failed',str(caught.exception));opener.open.assert_not_called()
        credential.get_token.return_value.expires_on=time.time()+300
        opener.open.return_value=io.BytesIO(b'x'*(4*1024*1024+1))
        with self.assertRaises(CollectionError) as caught:transport.get('/api/v1/nodes','')
        self.assertEqual('response_size_limit',str(caught.exception))
