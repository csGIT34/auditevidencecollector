import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from pypdf import PdfReader
from azure_at_rest.operational import publish,load,publish_pdf,MAX_BYTES
from azure_at_rest.archive import save_run,encode
from azure_at_rest.workflow import assess_snapshot
from azure_at_rest.cli import main
from azure_at_rest.storage import FileStore
from tests.test_archive import MemoryStore
from tests.test_controls import fixture,collect


def document():
    return {'schema_version':'1.0','kind':'operational_evidence','mode':'synthetic','records':[{
        'record_id':'restore-1','evidence_type':'restore_test','objective_ids':['BV-B'],'scope_kind':'run','resource_ids':[],
        'period_start':'2026-09-01T00:00:00Z','period_end':'2026-09-19T19:00:00Z','observed_at':'2026-09-19T20:00:00Z',
        'owner':'recovery-team','reviewer':'reviewer-1','assertion':'SATISFIED',
        'summary':'Synthetic operator statement: a restore exercise completed. This fixture is not tenant evidence.',
        'reference_sha256':None}]}

class OperationalEvidenceTests(unittest.TestCase):
    def setUp(self):
        responses,policy=fixture();self.snapshot=collect(responses);self.assessment=assess_snapshot(self.snapshot,criteria=policy)
        self.store=MemoryStore();self.run=save_run(self.store,self.snapshot,self.assessment)['run_id']

    def publish(self,doc=None,as_of='2026-09-19T21:00:00Z',hours=24):
        return publish(self.store,self.run,encode(document() if doc is None else doc),as_of=as_of,max_age_hours=hours)

    def test_source_preserved_assertion_kept_separate_and_historical_load_frozen(self):
        originals=dict(self.store.objects);manifest=self.publish()
        with patch('azure_at_rest.operational.review',side_effect=AssertionError('recomputed')):
            saved=load(self.store,manifest['evidence_id'])
        row=saved['report']['records'][0]
        self.assertEqual('CURRENT',row['freshness']);self.assertEqual('SATISFIED',row['assertion'])
        self.assertNotIn('result',row)
        for key,value in originals.items():self.assertEqual(value,self.store.objects[key])

    def test_future_stale_and_expired_exceptions_remain_visible(self):
        for as_of,state in [('2026-09-19T19:00:00Z','FUTURE'),('2026-09-21T20:00:01Z','STALE')]:
            manifest=self.publish(as_of=as_of)
            self.assertEqual(state,load(self.store,manifest['evidence_id'])['report']['records'][0]['freshness'])
        doc=document();doc['records'][0]['evidence_type']='exception'
        manifest=self.publish(doc)
        self.assertEqual('EXPIRED_EXCEPTION',load(self.store,manifest['evidence_id'])['report']['records'][0]['freshness'])

    def test_invalid_records_scope_and_secret_fields_rejected_before_writes(self):
        for mutation in ('objective','resource','owner','period','extra','mode','assertion'):
            doc=document();row=doc['records'][0]
            if mutation=='objective':row['objective_ids']=['INVENTED']
            elif mutation=='resource':row.update(scope_kind='resources',resource_ids=['/not/selected'])
            elif mutation=='owner':row['owner']=''
            elif mutation=='period':row['period_end']='2027-01-01T00:00:00Z'
            elif mutation=='extra':row['password']='DO-NOT-SAVE-SECRET'
            elif mutation=='mode':doc['mode']='operator_supplied'
            else:row['assertion']='PASS'
            original=dict(self.store.objects)
            with self.assertRaises(ValueError):self.publish(doc)
            self.assertEqual(original,self.store.objects)

    def test_duplicate_input_size_and_invalid_limits_rejected(self):
        for data in (b'{"schema_version":"1.0","schema_version":"1.0"}',b' '* (MAX_BYTES+1)):
            with self.assertRaises(ValueError):publish(self.store,self.run,data,as_of='2026-09-19T21:00:00Z',max_age_hours=24)
        for hours in (True,0,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):self.publish(hours=hours)

    def test_tamper_and_partial_publication_are_not_readable(self):
        manifest=self.publish();key=manifest['objects']['review.json']['key'];self.store.objects[key]+=b' '
        with self.assertRaises(ValueError):load(self.store,manifest['evidence_id'])
        self.store.fail_suffix='/review.md'
        with self.assertRaises(OSError):self.publish()
        intents=[key for key in self.store.objects if key.startswith('operational/') and key.endswith('/intent.json')]
        incomplete=next(key.split('/')[1] for key in intents if key.rsplit('/',1)[0]+'/manifest.json' not in self.store.objects)
        with self.assertRaises(FileNotFoundError):load(self.store,incomplete)

    def test_pdf_contains_full_record_and_safe_text(self):
        doc=document();doc['records'][0]['summary']='<b>literal markup</b> & test \u6d4b\u8bd5'
        manifest=self.publish(doc);originals=dict(self.store.objects)
        pdf=publish_pdf(self.store,manifest['evidence_id'])
        content=self.store.read(pdf['pdf']['key']);reader=PdfReader(io.BytesIO(content))
        text=''.join(page.extract_text() for page in reader.pages)
        self.assertIn('restore-1',text);self.assertIn('SATISFIED',text)
        self.assertIn('<b>literal markup</b>',text);self.assertIn('not independently authenticated',text)
        self.assertEqual(2,len(reader.pages))
        for key,value in originals.items():self.assertEqual(value,self.store.objects[key])

    def test_cli_import_and_show(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);store=FileStore(root/'archive')
            run=save_run(store,self.snapshot,self.assessment)['run_id']
            source=root/'records.json';source.write_bytes(encode(document()));output=io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(0,main(['operational-import','--store',str(root/'archive'),'--run-id',run,'--input',str(source),
                                         '--as-of','2026-09-19T21:00:00Z','--max-age-hours','24']))
            evidence_id=json.loads(output.getvalue())['evidence_id'];output=io.StringIO()
            with redirect_stdout(output):self.assertEqual(0,main(['operational-show','--store',str(root/'archive'),'--evidence-id',evidence_id]))
            self.assertIn('restore-1',output.getvalue())

    def test_required_period_population_and_conflicts_are_explicit(self):
        doc=document();record=doc['records'][0]
        requirement={'requirement_id':'restore-required','evidence_type':'restore_test','objective_id':'BV-B',
                     'scope_kind':'run','resource_ids':[],'period_start':record['period_start'],'period_end':record['period_end']}
        doc['requirements']=[requirement]
        def state(value,as_of='2026-09-19T21:00:00Z'):
            manifest=self.publish(value,as_of=as_of)
            return load(self.store,manifest['evidence_id'])['report']['requirement_results'][0]['state']
        self.assertEqual('ASSERTED_SATISFIED',state(doc))
        self.assertEqual('MISSING',state({**doc,'records':[]}))
        self.assertEqual('NO_CURRENT_EVIDENCE',state(doc,'2026-09-21T21:00:00Z'))
        doc['records'].append({**record,'record_id':'restore-disputed','assertion':'NOT_SATISFIED'})
        self.assertEqual('CONFLICTING_ASSERTIONS',state(doc))
        doc['records']=doc['records'][1:]
        self.assertEqual('ASSERTED_NOT_SATISFIED',state(doc))
        requirement['period_start']='2026-08-01T00:00:00Z'
        self.assertEqual('MISSING',state(doc))

    def test_run_assertion_does_not_satisfy_required_resource(self):
        doc=document();rid=self.snapshot['resources'][0]['id'].lower()
        doc['requirements']=[{'requirement_id':'resource-restore','evidence_type':'restore_test','objective_id':'BV-B',
                             'scope_kind':'resources','resource_ids':[rid],'period_start':'2026-09-01T00:00:00Z','period_end':'2026-09-19T19:00:00Z'}]
        manifest=self.publish(doc)
        result=load(self.store,manifest['evidence_id'])['report']['requirement_results'][0]
        self.assertEqual('MISSING',result['state']);self.assertEqual(rid,result['resource_id'])
        doc['requirements'][0]['resource_ids']=['/not-selected']
        original=dict(self.store.objects)
        with self.assertRaises(ValueError):self.publish(doc)
        self.assertEqual(original,self.store.objects)
