import copy
import io
import json
import unittest
from unittest.mock import patch
from azure_at_rest.archive import encode,save_run
from azure_at_rest.guest_evidence import publish,load,publish_pdf,CHECKS,BOOL
from azure_at_rest.workflow import assess_snapshot
from tests.test_archive import MemoryStore
from tests.test_controls import fixture,collect
from pypdf import PdfReader

AS_OF='2026-09-20T02:00:00Z'

def criteria():
    return {'schema_version':'1.0','id':'synthetic','version':'1','status':'approved','checks':{key:(key!='reboot_pending' if key in BOOL else 3600 if key.endswith('_seconds') else 0) for key in CHECKS}}

def record(rid,source='synthetic'):
    return {'record_id':'record-1','resource_id':rid,'source':source,'observed_at':'2026-09-20T01:50:00Z','os':'linux',
            'patch':{'assessed_at':'2026-09-20T01:40:00Z','state':'succeeded','missing_critical':0,'missing_security':0,'reboot_pending':False},
            'protection':{'reported_at':'2026-09-20T01:40:00Z','enabled':True,'healthy':True},
            'vulnerabilities':{'scanned_at':'2026-09-20T01:40:00Z','state':'succeeded','critical':0,'high':0}}

class GuestEvidenceTests(unittest.TestCase):
    def setUp(self):
        responses,policy=fixture();self.snapshot=collect(responses)
        vm=next(r for r in self.snapshot['resources'] if r['type'].lower()=='microsoft.compute/virtualmachines')
        vmss=next(r for r in self.snapshot['resources'] if r['type'].lower()=='microsoft.compute/virtualmachinescalesets')
        self.vm=vm['id'].lower();self.vmss=vmss['id'].lower();self.instance=vmss['configuration']['VMSS-instance-models']['value'][0]['instance_id']
        self.store=MemoryStore();self.run=save_run(self.store,self.snapshot,assess_snapshot(self.snapshot,criteria=policy))['run_id']
        self.document={'schema_version':'1.0','kind':'guest_export','mode':'synthetic','resource_ids':[self.vm,self.vmss],
                       'records':[record(self.vm),record(self.instance)]}
    def save(self,doc=None,policy=None,as_of=AS_OF):
        return publish(self.store,self.run,encode(doc or self.document),criteria=criteria() if policy is None else policy,as_of=as_of,max_age_seconds=3600)

    def test_vm_and_saved_vmss_instances_assess_all_measurements(self):
        report=load(self.store,self.save()['evidence_id'])['report']
        self.assertEqual({'PASS':20,'FAIL':0,'UNKNOWN':0},report['summary']['counts'])
        self.assertFalse(report['summary']['coverage_incomplete'])
        self.assertEqual({self.vm,self.instance},set(report['source_scope']['expected_guest_ids']))

    def test_missing_guest_is_not_silently_removed(self):
        doc=copy.deepcopy(self.document);doc['records']=doc['records'][:1]
        report=load(self.store,self.save(doc)['evidence_id'])['report']
        self.assertEqual(10,report['summary']['counts']['UNKNOWN']);self.assertTrue(report['summary']['coverage_incomplete'])
        self.assertEqual('missing',report['records'][1]['freshness'])

    def test_old_component_reports_cannot_pass_zero_counts(self):
        doc=copy.deepcopy(self.document)
        for row in doc['records']:
            for section,key in [('patch','assessed_at'),('protection','reported_at'),('vulnerabilities','scanned_at')]:row[section][key]='2026-09-19T01:00:00Z'
        summary=load(self.store,self.save(doc)['evidence_id'])['report']['summary']
        self.assertEqual(6,summary['counts']['FAIL']);self.assertEqual(14,summary['counts']['UNKNOWN'])
        self.assertTrue(summary['coverage_incomplete'])

    def test_failed_or_running_scan_and_patch_do_not_make_zero_counts_pass(self):
        for status in ('failed','in_progress','unknown'):
            doc=copy.deepcopy(self.document)
            for row in doc['records']:row['patch']['state']=row['vulnerabilities']['state']=status
            summary=load(self.store,self.save(doc)['evidence_id'])['report']['summary']
            self.assertEqual(14,summary['counts']['UNKNOWN']);self.assertTrue(summary['coverage_incomplete'])

    def test_conflicting_sources_do_not_hide_failure(self):
        doc=copy.deepcopy(self.document);extra=record(self.vm,'other-source');extra['protection']['enabled']=False;extra['vulnerabilities']['critical']=1
        doc['records'].append(extra);report=load(self.store,self.save(doc)['evidence_id'])['report']
        self.assertEqual(2,report['summary']['counts']['FAIL']);self.assertEqual('FAILURES_FOUND',report['summary']['conclusion'])
        self.assertEqual(3,len(report['records']))

    def test_invalid_identity_unknown_fields_duplicates_and_future_components_reject_before_write(self):
        for mutation in ('unknown','duplicate','extra','negative','boolean','future','mode'):
            doc=copy.deepcopy(self.document);row=doc['records'][0]
            if mutation=='unknown':row['resource_id']+='/not-in-source'
            elif mutation=='duplicate':doc['records'].append(copy.deepcopy(row))
            elif mutation=='extra':row['password']='SECRET-CANARY'
            elif mutation=='negative':row['patch']['missing_critical']=-1
            elif mutation=='boolean':row['vulnerabilities']['critical']=False
            elif mutation=='future':row['patch']['assessed_at']='2027-01-01T00:00:00Z'
            else:doc['mode']='operator_export'
            before=dict(self.store.objects)
            with self.assertRaises(ValueError):self.save(doc)
            self.assertEqual(before,self.store.objects)

    def test_stale_future_missing_and_draft_criteria_remain_unknown(self):
        for as_of in ('2026-09-20T01:00:00Z','2026-09-21T00:00:00Z'):
            summary=self.save(as_of=as_of)['summary'];self.assertEqual(20,summary['counts']['UNKNOWN'])
        for policy in ({**criteria(),'status':'draft'},{**criteria(),'checks':{}}):
            self.assertEqual(20,self.save(policy=policy)['summary']['counts']['UNKNOWN'])
        result=publish(self.store,self.run,encode(self.document),criteria=None,as_of=AS_OF,max_age_seconds=3600)
        self.assertEqual(20,result['summary']['counts']['UNKNOWN'])

    def test_archives_and_pdf_are_frozen_and_tampering_rejected(self):
        manifest=self.save();before=dict(self.store.objects)
        with patch('azure_at_rest.guest_evidence.assess',side_effect=AssertionError('No historical reassessment')):
            report=publish_pdf(self.store,manifest['evidence_id'])
        text=' '.join(p.extract_text() for p in PdfReader(io.BytesIO(self.store.read(report['pdf']['key']))).pages)
        self.assertIn('Guest and agent evidence',text);self.assertIn('missing_critical_patches',text)
        for key,value in before.items():self.assertEqual(value,self.store.objects[key])
        key=manifest['objects']['assessment.json']['key'];self.store.objects[key]+=b' '
        with self.assertRaises(ValueError):load(self.store,manifest['evidence_id'])

    def test_partial_vmss_population_remains_incomplete_with_passing_present_guests(self):
        for r in self.snapshot['resources']:
            if r['id'].lower()==self.vmss:r['configuration']['VMSS-instance-models']['state']='partial'
        self.run=save_run(self.store,self.snapshot,assess_snapshot(self.snapshot))['run_id']
        summary=self.save()['summary']
        self.assertEqual(20,summary['counts']['PASS']);self.assertTrue(summary['coverage_incomplete']);self.assertEqual('INCOMPLETE',summary['conclusion'])

    def test_hosted_import_and_report_opt_in(self):
        from contextlib import contextmanager
        from azure_at_rest.hosting import execute
        from tests.test_hosting import environment
        from unittest.mock import Mock
        factory=Mock();self.assertEqual('disabled',execute('guest-import',env={},factory=factory)['state']);factory.assert_not_called()
        @contextmanager
        def resources(*args):yield self.store,None
        env={**environment(),'CG_GUEST_ENABLED':'true'}
        result=execute('guest-import',run_id=self.run,document=encode(self.document),criteria=criteria(),as_of=AS_OF,max_age_seconds=3600,env=env,factory=resources)
        self.assertEqual('complete',result['state'])
        pdf=execute('guest-report',evidence_id=result['evidence_id'],env=env,factory=resources)
        self.assertEqual('complete',pdf['state']);self.assertTrue(self.store.read(pdf['pdf_key']).startswith(b'%PDF'))

    def test_cli_roundtrip(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from contextlib import redirect_stdout
        from azure_at_rest.cli import main
        with TemporaryDirectory() as directory:
            root=Path(directory);store=root/'archive'
            for key,value in self.store.objects.items():
                p=store/key;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value)
            (root/'input.json').write_bytes(encode(self.document));(root/'criteria.json').write_bytes(encode(criteria()))
            out=io.StringIO()
            with redirect_stdout(out):
                code=main(['guest-import','--store',str(store),'--run-id',self.run,'--input',str(root/'input.json'),'--criteria',str(root/'criteria.json'),'--as-of',AS_OF,'--max-age-seconds','3600'])
            self.assertEqual(0,code);evidence_id=json.loads(out.getvalue())['evidence_id']
            for command in ('guest-show','guest-pdf'):
                with redirect_stdout(io.StringIO()):self.assertEqual(0,main([command,'--store',str(store),'--evidence-id',evidence_id]))

    def test_interrupted_publication_never_loads_complete(self):
        original=self.store.put_new
        def fail(key,value):
            if key.startswith('guests/') and key.endswith('/manifest.json'):raise OSError('synthetic write failure')
            original(key,value)
        with patch.object(self.store,'put_new',side_effect=fail):
            with self.assertRaises(OSError):self.save()
        key=next(k for k in self.store.objects if k.startswith('guests/'))
        with self.assertRaises((KeyError,FileNotFoundError)):load(self.store,key.split('/')[1])
