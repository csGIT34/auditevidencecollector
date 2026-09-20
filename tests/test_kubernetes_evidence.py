import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from contextlib import contextmanager,redirect_stdout
from unittest.mock import patch,Mock
from pypdf import PdfReader
from cloud_governance.archive import encode,save_run
from cloud_governance.kubernetes_evidence import publish,load,publish_pdf,MAX_BYTES,CHECKS
from cloud_governance.workflow import assess_snapshot
from tests.test_controls import fixture,collect
from tests.test_archive import MemoryStore
from tests.test_hosting import environment

AS_OF='2026-09-20T02:00:00Z'


def document(cluster):
    return {'schema_version':'1.0','kind':'kubernetes_export','mode':'synthetic','cluster_id':cluster.lower(),
        'collected_at':'2026-09-20T01:30:00Z','scope':{'namespace':'example','pods_complete':True},
        'nodes':{'apiVersion':'v1','kind':'NodeList','items':[{'metadata':{'name':'node-1'},'status':{'nodeInfo':{'operatingSystem':'linux'},'addresses':[{'address':'SECRET-CANARY'}]}}]},
        'pods':{'apiVersion':'v1','kind':'PodList','metadata':{},'items':[{
            'apiVersion':'v1','kind':'Pod','metadata':{'uid':'pod-unique-1','name':'web-1','namespace':'example','annotations':{'password':'SECRET-CANARY'}},
            'spec':{'nodeName':'node-1','securityContext':{'runAsNonRoot':True},'containers':[{
                'name':'web','image':'example.azurecr.io/web@sha256:'+'a'*64,'env':[{'name':'PASSWORD','value':'SECRET-CANARY'}],
                'command':['SECRET-CANARY'],'args':['SECRET-CANARY'],'securityContext':{'allowPrivilegeEscalation':False,'readOnlyRootFilesystem':True}}]},
            'status':{'containerStatuses':[{'name':'web','imageID':'docker-pullable://example.azurecr.io/web@sha256:'+'a'*64,'state':{'running':{'secret':'SECRET-CANARY'}}}]}
        }]}}


def criteria():
    return {'schema_version':'1.0','id':'synthetic-example','version':'1','status':'approved',
        'checks':{key:key not in ('host_namespaces','privileged','allow_escalation') for key in CHECKS}}

class KubernetesEvidenceTests(unittest.TestCase):
    def setUp(self):
        responses,policy=fixture();self.snapshot=collect(responses);self.report=assess_snapshot(self.snapshot,criteria=policy)
        self.cluster=next(r['id'] for r in self.snapshot['resources'] if r['type'].lower()=='microsoft.containerservice/managedclusters')
        self.store=MemoryStore();self.run=save_run(self.store,self.snapshot,self.report)['run_id']

    def save(self,doc=None,policy=None,as_of=AS_OF):
        return publish(self.store,self.run,encode(doc or document(self.cluster)),criteria=criteria() if policy is None else policy,as_of=as_of,max_age_seconds=3600)

    def test_projection_excludes_sensitive_fields_and_retains_exact_source_archive(self):
        original=dict(self.store.objects);m=self.save();saved=load(self.store,m['evidence_id'])
        self.assertEqual({'PASS':8,'FAIL':0,'UNKNOWN':0},saved['report']['summary']['counts'])
        self.assertFalse(saved['report']['summary']['coverage_incomplete'])
        self.assertNotIn('SECRET-CANARY',b' '.join(self.store.objects.values()).decode())
        self.assertFalse(any(key.endswith('/input.json') for key in self.store.objects if key.startswith('workloads/')))
        for key,data in original.items():self.assertEqual(data,self.store.objects[key])

    def test_init_and_ephemeral_containers_are_not_omitted(self):
        doc=document(self.cluster);pod=doc['pods']['items'][0]
        for key,status_key,name in [('initContainers','initContainerStatuses','init'),('ephemeralContainers','ephemeralContainerStatuses','debug')]:
            container=copy.deepcopy(pod['spec']['containers'][0]);container['name']=name;container['securityContext']['privileged']=True
            pod['spec'][key]=[container];pod['status'][status_key]=[{'name':name,'imageID':'containerd://sha256:'+'a'*64}]
        saved=load(self.store,self.save(doc)['evidence_id'])
        self.assertEqual({'app','init','ephemeral'},{r['container_kind'] for r in saved['report']['records']})
        self.assertEqual(4,saved['report']['summary']['counts']['FAIL'])

    def test_container_override_root_uid_and_admin_capability_cannot_hide_unsafe_settings(self):
        doc=document(self.cluster);security=doc['pods']['items'][0]['spec']['containers'][0]['securityContext']
        security.update(runAsNonRoot=True,runAsUser=0,capabilities={'add':['SYS_ADMIN']})
        checks=load(self.store,self.save(doc)['evidence_id'])['report']['records'][0]['checks']
        self.assertEqual('FAIL',checks['run_as_non_root']['result']);self.assertEqual('FAIL',checks['allow_escalation']['result'])

    def test_windows_unknown_or_conflicting_os_never_pass_linux_checks(self):
        for change in ('windows','unknown','conflict'):
            doc=document(self.cluster)
            if change=='unknown':doc['nodes']['items']=[]
            else:doc['nodes']['items'][0]['status']['nodeInfo']['operatingSystem']='windows'
            if change=='conflict':doc['pods']['items'][0]['spec']['os']={'name':'linux'}
            summary=load(self.store,self.save(doc)['evidence_id'])['report']['summary']
            self.assertEqual(4,summary['counts']['UNKNOWN']);self.assertTrue(summary['coverage_incomplete'])

    def test_tag_missing_runtime_status_and_digest_mismatch_are_distinct(self):
        for change,result in [('tag','FAIL'),('missing','UNKNOWN'),('mismatch','FAIL')]:
            doc=document(self.cluster);pod=doc['pods']['items'][0]
            if change=='tag':pod['spec']['containers'][0]['image']='sha256:'+'a'*64
            elif change=='missing':pod['status']['containerStatuses']=[]
            else:pod['status']['containerStatuses'][0]['imageID']='containerd://sha256:'+'b'*64
            row=load(self.store,self.save(doc)['evidence_id'])['report']['records'][0]
            key='declared_digest' if change=='tag' else 'runtime_digest_known' if change=='missing' else 'declared_runtime_digest_match'
            self.assertEqual(result,row['checks'][key]['result'])

    def test_stale_future_partial_and_empty_exports_do_not_claim_complete_coverage(self):
        for as_of in ('2026-09-20T04:00:00Z','2026-09-20T01:00:00Z'):
            summary=load(self.store,self.save(as_of=as_of)['evidence_id'])['report']['summary']
            self.assertEqual(8,summary['counts']['UNKNOWN'])
        for change in ('partial','empty'):
            doc=document(self.cluster)
            if change=='partial':doc['pods']['metadata']['continue']='DO-NOT-STORE-CONTINUATION'
            else:doc['pods']['items']=[]
            saved=load(self.store,self.save(doc)['evidence_id'])
            self.assertTrue(saved['report']['summary']['coverage_incomplete'])
            self.assertNotIn('DO-NOT-STORE-CONTINUATION',json.dumps(saved))

    def test_wrong_cluster_namespace_duplicates_modes_and_malformed_fields_fail_before_writes(self):
        for change in ('cluster','namespace','pod-duplicate','status-duplicate','unknown-status-container','mode','bad-spec'):
            doc=document(self.cluster);pod=doc['pods']['items'][0]
            if change=='cluster':doc['cluster_id']+='-other'
            elif change=='namespace':pod['metadata']['namespace']='outside'
            elif change=='pod-duplicate':doc['pods']['items'].append(copy.deepcopy(pod))
            elif change=='status-duplicate':pod['status']['containerStatuses']*=2
            elif change=='unknown-status-container':pod['status']['containerStatuses'][0]['name']='missing'
            elif change=='mode':doc['mode']='operator_export'
            else:pod['spec']=None
            original=dict(self.store.objects)
            with self.assertRaises(ValueError):self.save(doc)
            self.assertEqual(original,self.store.objects)

    def test_draft_absent_and_invalid_criteria_never_create_positive_results(self):
        doc=encode(document(self.cluster))
        for value in (None,{**criteria(),'status':'draft'},{**criteria(),'checks':{}}):
            m=publish(self.store,self.run,doc,criteria=value,as_of=AS_OF,max_age_seconds=3600)
            self.assertEqual(8,load(self.store,m['evidence_id'])['report']['summary']['counts']['UNKNOWN'])
        original=dict(self.store.objects)
        with self.assertRaises(ValueError):self.save(policy={**criteria(),'checks':{'privileged':0}})
        self.assertEqual(original,self.store.objects)
        with self.assertRaises(ValueError):publish(self.store,self.run,b' '*(MAX_BYTES+1),criteria=None,as_of=AS_OF,max_age_seconds=3600)

    def test_historical_pdf_uses_frozen_projection_and_excludes_secret_canaries(self):
        m=self.save();original=dict(self.store.objects)
        with patch('cloud_governance.kubernetes_evidence.project',side_effect=AssertionError('reprojection')),patch('cloud_governance.kubernetes_evidence.assess',side_effect=AssertionError('reassessment')):
            pdf=publish_pdf(self.store,m['evidence_id'])
        text=''.join(p.extract_text() for p in PdfReader(io.BytesIO(self.store.read(pdf['pdf']['key']))).pages)
        self.assertIn('Kubernetes workload evidence',text);self.assertIn('run_as_non_root',text)
        self.assertNotIn('SECRET-CANARY',text)
        for key,data in original.items():self.assertEqual(data,self.store.objects[key])
        key=m['objects']['projection.json']['key'];self.store.objects[key]+=b' '
        with self.assertRaises(ValueError):load(self.store,m['evidence_id'])

    def test_failed_publication_has_no_readable_complete_manifest(self):
        self.store.fail_suffix='/assessment.json'
        with self.assertRaises(OSError):self.save()
        key=next(k for k in self.store.objects if k.startswith('workloads/') and k.endswith('/intent.json'))
        with self.assertRaises(FileNotFoundError):load(self.store,key.split('/')[1])

    def test_hosted_import_report_and_disabled_gate(self):
        from cloud_governance.hosting import execute
        factory=Mock(side_effect=AssertionError('disabled should not open storage'))
        for op in ('workload-import','workload-report'):self.assertEqual('disabled',execute(op,env={},factory=factory)['state'])
        @contextmanager
        def active(*args):yield self.store,None
        env={**environment(),'CG_WORKLOAD_ENABLED':'true'}
        imported=execute('workload-import',env=env,factory=active,run_id=self.run,document=encode(document(self.cluster)),criteria=criteria(),as_of=AS_OF,max_age_seconds=3600)
        pdf=execute('workload-report',env=env,factory=active,evidence_id=imported['evidence_id'])
        self.assertEqual('complete',pdf['state']);self.assertTrue(self.store.read(pdf['pdf_key']).startswith(b'%PDF'))

    def test_cli_import_show_and_function_route_contracts(self):
        from cloud_governance.cli import main
        from cloud_governance.storage import FileStore
        import importlib
        import azure.functions as func
        import function_app
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);store=FileStore(root/'archive');run=save_run(store,self.snapshot,self.report)['run_id']
            source=root/'source.json';source.write_bytes(encode(document(self.cluster)));policy=root/'policy.json';policy.write_bytes(encode(criteria()))
            stdout=io.StringIO()
            with redirect_stdout(stdout):self.assertEqual(0,main(['kubernetes-import','--store',str(root/'archive'),'--run-id',run,'--input',str(source),'--criteria',str(policy),'--as-of',AS_OF,'--max-age-seconds','3600']))
            evidence_id=json.loads(stdout.getvalue())['evidence_id'];stdout=io.StringIO()
            with redirect_stdout(stdout):self.assertEqual(0,main(['kubernetes-show','--store',str(root/'archive'),'--evidence-id',evidence_id]))
            self.assertIn('run_as_non_root',stdout.getvalue());self.assertNotIn('SECRET-CANARY',stdout.getvalue())
        try:
            with patch.dict('os.environ',{'CG_WORKLOAD_ENABLED':'true'},clear=True):
                module=importlib.reload(function_app);functions=module.app.get_functions()
                self.assertEqual({'GenerateReport','ImportKubernetesEvidence','GenerateKubernetesReport'},{f.get_function_name() for f in functions})
                for function in functions:
                    binding=json.loads(function.get_function_json())['bindings'][0]
                    self.assertEqual('FUNCTION',binding['authLevel']);self.assertEqual(['POST'],binding['methods'])
                for handler in (module.import_kubernetes_evidence,module.generate_kubernetes_report):
                    with patch.object(module,'execute',side_effect=AssertionError('bad request must be rejected')):
                        self.assertEqual(400,handler(func.HttpRequest('POST','https://example/api',body=b'{}')).status_code)
                envelope={'run_id':self.run,'document':document(self.cluster),'criteria':criteria(),'as_of':AS_OF,'max_age_seconds':3600}
                with patch.object(module,'execute',return_value={'state':'complete'}) as action:
                    response=module.import_kubernetes_evidence(func.HttpRequest('POST','https://example/api',body=encode(envelope)))
                    self.assertEqual(201,response.status_code);self.assertEqual('workload-import',action.call_args.args[0])
        finally:
            with patch.dict('os.environ',{},clear=True):importlib.reload(function_app)
