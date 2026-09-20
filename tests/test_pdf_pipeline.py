import contextlib
import copy
from io import BytesIO, StringIO
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cloud_governance.archive import digest, encode, load_run, publish_pdf, save_run, snapshot_digest
from cloud_governance.cli import main
from cloud_governance.collector import Collector, FixtureTransport
from cloud_governance.storage import FileStore
from cloud_governance.assessment import assess
from tests.test_archive import evidence, MemoryStore

ROOT=Path(__file__).resolve().parents[1]
HAS_PDF=all(importlib.util.find_spec(name) for name in ('reportlab','pypdf'))


def invoke(args):
    out=StringIO()
    with contextlib.redirect_stdout(out),contextlib.redirect_stderr(out):
        code=main(args)
    return code,out.getvalue()


class ArchiveCliTests(unittest.TestCase):
    def test_collection_archives_failures_and_preserves_previous_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=['collect','--fixture',str(ROOT/'examples/demo-fixture.json'),'--store',tmp]
            with patch('cloud_governance.collector.AzureCliCredential.get_token',side_effect=AssertionError('No cloud')):
                code,out=invoke(args)
                self.assertEqual(1,code);self.assertIn('Local archive complete',out)
                store=FileStore(tmp);old={k:store.read(k) for k in store.keys('runs/')}
                self.assertEqual(1,invoke(args)[0])
            self.assertEqual(old,{k:store.read(k) for k in old})
            code,out=invoke(['runs','--store',tmp]);runs=json.loads(out)
            self.assertEqual(0,code);self.assertEqual(2,len(runs))
            self.assertTrue(all(r['coverage_incomplete'] and r['assessment_conclusion']=='FAILURES_FOUND' for r in runs))

    def test_invalid_saved_run_does_not_trigger_collection(self):
        with tempfile.TemporaryDirectory() as tmp,patch('cloud_governance.collector.Collector.collect',side_effect=AssertionError('No recollection')):
            code,out=invoke(['pdf','--store',tmp,'--run-id','latest'])
            self.assertEqual(3,code)

    def test_missing_pdf_dependency_is_actionable_and_preserves_evidence(self):
        s,r=evidence()
        with tempfile.TemporaryDirectory() as tmp:
            store=FileStore(tmp);m=save_run(store,s,r);old={k:store.read(k) for k in store.keys('runs/')}
            with patch('cloud_governance.pdf_report.renderer_dependencies',side_effect=RuntimeError('PDF_DEPENDENCY_MISSING')):
                code,out=invoke(['pdf','--store',tmp,'--run-id',m['run_id']])
            self.assertEqual(3,code);self.assertIn('[pdf] extra',out)
            self.assertEqual(old,{k:store.read(k) for k in old});self.assertEqual([],store.keys('reports/'))


@unittest.skipUnless(HAS_PDF,'PDF tests require optional reportlab and pypdf dependencies')
class PdfPipelineTests(unittest.TestCase):
    def text(self,pdf):
        from pypdf import PdfReader
        reader=PdfReader(BytesIO(pdf))
        return reader,'\n'.join(p.extract_text() for p in reader.pages)

    def test_full_fixture_self_contained_pdf_has_facts_failures_scope_and_provenance(self):
        fixture=json.loads((ROOT/'examples/demo-fixture.json').read_text())
        snapshot=Collector(FixtureTransport(fixture['responses']),mode='offline_fixture').collect()
        report=assess(snapshot);report['snapshot_sha256']=snapshot_digest(snapshot);report['reassessed_from_snapshot']=False
        store=MemoryStore();run=save_run(store,snapshot,report)
        with patch('cloud_governance.collector.Collector.collect',side_effect=AssertionError('No recollection')),patch('cloud_governance.assessment.assess',side_effect=AssertionError('No reassessment')):
            manifest=publish_pdf(store,run['run_id'])
        pdf=store.read(manifest['pdf']['key']);reader,text=self.text(pdf)
        compact=''.join(text.split())
        self.assertGreater(len(reader.pages),10)
        for row in report['results']:
            self.assertIn(''.join(row['id'].split()),compact)
            self.assertIn(''.join(row['reason'].split()),compact)
            for k,v in row['evidence'].items():self.assertIn(k,compact)
        for name in load_run(store,run['run_id'])['context']['program_scope']['services']:
            self.assertIn(''.join(name['name'].split()),compact)
        for required in ['SYNTHETIC EXAMPLE','FAILURES_FOUND','NOT COLLECTED / NOT ASSESSED','Collection errors',
                         'SC-28(1)','PDF generated','documented service guarantees','not signatures','retention','DO NOT RUN',
                         'Observed field','Saved criterion','Read methods','E001']:
            self.assertIn(''.join(required.split()),compact)
        self.assertEqual(digest(pdf),manifest['pdf']['sha256'])
        self.assertEqual(run['objects'],manifest['source_objects'])
        self.assertTrue(reader.outline)
        # A self-contained report must not rely on a viewer's substitute fonts.
        def check_text_font(value, cm, tm, font, size):
            if value.strip():
                descriptor = font.get('/FontDescriptor')
                self.assertIsNotNone(descriptor)
                self.assertIn('/FontFile2', descriptor.get_object())
        for page in reader.pages:
            page.extract_text(visitor_text=check_text_font)
        self.assertNotIn('file://',text)

    def test_regeneration_uses_exact_old_run_and_creates_distinct_reports(self):
        s,r=evidence();store=MemoryStore();first=save_run(store,s,r);before=dict(store.objects)
        # A second, later saved population must never replace the explicit first selection.
        s2,r2=evidence();s2['resources'][0]['name']='second-name';s2['resources'][0]['id']=s2['resources'][0]['id'].replace('safe-store','second-name')
        s2['resources'][0]['request_path']=s2['resources'][0]['id'];r2=assess(s2);r2['snapshot_sha256']=snapshot_digest(s2);r2['reassessed_from_snapshot']=False
        save_run(store,s2,r2)
        with (patch('cloud_governance.archive.make_context',side_effect=AssertionError('No current catalog')),
             patch.dict('cloud_governance.catalog.RULES',{},clear=True)):
            a=publish_pdf(store,first['run_id']);b=publish_pdf(store,first['run_id'])
        self.assertNotEqual(a['report_id'],b['report_id']);self.assertNotEqual(a['pdf']['key'],b['pdf']['key'])
        self.assertEqual(before,{k:store.objects[k] for k in before})
        for m in [a,b]:
            text=self.text(store.read(m['pdf']['key']))[1]
            self.assertIn('safe-store',text);self.assertNotIn('second-name',text)

    def test_render_and_each_publication_failure_leave_no_complete_report(self):
        for suffix in ('report.pdf','manifest.json',None):
            s,r=evidence();store=MemoryStore();run=save_run(store,s,r);original=dict(store.objects)
            store.fail_suffix=suffix
            manager=patch('cloud_governance.pdf_report.render_pdf',side_effect=RuntimeError('TOP-SECRET')) if suffix is None else contextlib.nullcontext()
            with manager,self.assertRaises(RuntimeError):publish_pdf(store,run['run_id'])
            self.assertEqual(original,{k:store.objects[k] for k in original})
            reports={k:v for k,v in store.objects.items() if k.startswith('reports/')}
            self.assertTrue(any(k.endswith('/failure.json') for k in reports))
            self.assertFalse(any(k.endswith('/manifest.json') for k in reports))
            self.assertFalse(any(b'TOP-SECRET' in v for v in reports.values()))

    def test_pdf_export_never_overwrites_and_archived_version_survives_export_failure(self):
        s,r=evidence()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);store=FileStore(root/'store');run=save_run(store,s,r)
            output=root/'report.pdf';output.write_bytes(b'keep-me')
            code,out=invoke(['pdf','--store',str(store.root),'--run-id',run['run_id'],'--export',str(output)])
            self.assertEqual(3,code);self.assertIn('PDF is archived',out);self.assertEqual(b'keep-me',output.read_bytes())
            self.assertEqual(1,len([k for k in store.keys('reports/') if k.endswith('manifest.json')]))

    def test_empty_scope_and_long_evidence_render_without_false_all_clear(self):
        from tests.helpers import Scenario
        scenario=Scenario([]);r=scenario.run();r['snapshot_sha256']=snapshot_digest(scenario.snapshot);r['reassessed_from_snapshot']=False
        store=MemoryStore();m=save_run(store,scenario.snapshot,r);pdf=publish_pdf(store,m['run_id'])
        text=self.text(store.read(pdf['pdf']['key']))[1]
        self.assertIn('INCOMPLETE',text);self.assertIn('Empty inventory',text)
        s,r=evidence();r['results'][0]['gaps']=['Missing dependency evidence. '*200 + ' \u4e2d']
        r['summary']['coverage_incomplete']=True;r['summary']['conclusion']='INCOMPLETE'
        m=save_run(store,s,r);pdf=publish_pdf(store,m['run_id'])
        rendered, rendered_text = self.text(store.read(pdf['pdf']['key']))
        self.assertTrue(rendered.pages)
        self.assertIn('[U+4E2D]', rendered_text)


class PackagedScopeTests(unittest.TestCase):
    def test_program_scope_matches_research_catalog(self):
        source=ROOT/'docs/audit/catalog.json';d=json.loads(source.read_text())
        packaged=json.loads((ROOT/'cloud_governance/program_scope.json').read_text())
        self.assertEqual(digest(source.read_bytes()),packaged['catalog_sha256'])
        self.assertEqual([s['name'] for s in d['services']],[s['name'] for s in packaged['services']])
        self.assertEqual(d['domains'],packaged['domains'])
        self.assertEqual(d['catalog_version'],packaged['catalog_version'])
