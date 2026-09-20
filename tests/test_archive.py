import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from cloud_governance.archive import encode, save_run, load_run, list_runs, snapshot_digest
from cloud_governance.storage import FileStore
from tests.helpers import Scenario, resource


def evidence():
    scenario = Scenario([resource('Microsoft.Storage/storageAccounts', 'safe-store')])
    report = scenario.run()
    report['snapshot_sha256'] = snapshot_digest(scenario.snapshot)
    report['reassessed_from_snapshot'] = False
    return scenario.snapshot, report


class MemoryStore:
    def __init__(self, fail_suffix=None):
        self.objects = {}
        self.fail_suffix = fail_suffix
    def put_new(self, key, data):
        if self.fail_suffix and key.endswith(self.fail_suffix):
            raise OSError('sensitive error payload must not appear in state')
        if key in self.objects:
            raise FileExistsError(key)
        self.objects[key] = data
    def read(self, key):
        if key not in self.objects:
            raise FileNotFoundError(key)
        return self.objects[key]
    def keys(self, prefix):
        return sorted(k for k in self.objects if k.startswith(prefix))


class FileStoreTests(unittest.TestCase):
    def test_immutable_concurrent_publish_and_private_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=FileStore(Path(tmp)/'root')
            def publish(value):
                try:
                    store.put_new('runs/example/object.json', value)
                    return value
                except FileExistsError:
                    return None
            with ThreadPoolExecutor(max_workers=8) as pool:
                outcomes=list(pool.map(publish,[bytes([x])*1000 for x in range(8)]))
            winners=[x for x in outcomes if x is not None]
            self.assertEqual(1,len(winners))
            self.assertEqual(winners[0],store.read('runs/example/object.json'))
            self.assertEqual(['runs/example/object.json'],store.keys('runs/'))
            self.assertEqual(0o600,(store.root/'runs/example/object.json').stat().st_mode & 0o777)
            self.assertEqual(0o700,(store.root/'runs/example').stat().st_mode & 0o777)
            self.assertFalse(list(store.root.rglob('.pending-*')))

    def test_traversal_symlinks_and_nonregular_objects_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);store=FileStore(root/'store');outside=root/'outside';outside.mkdir()
            for key in ['../escape','/absolute','a//b','a/../b','a/./b','a\\b','a/%2f','a/space name']:
                with self.subTest(key=key),self.assertRaises(ValueError):store.put_new(key,b'no')
            (store.root/'link').symlink_to(outside,target_is_directory=True)
            with self.assertRaises(OSError):store.put_new('link/object',b'no')
            self.assertEqual([],list(outside.iterdir()))
            store.put_new('runs/file',b'original')
            (store.root/'runs/alias').symlink_to(store.root/'runs/file')
            with self.assertRaises(OSError):store.read('runs/alias')
            with self.assertRaises(ValueError):store.keys('runs/')
            with self.assertRaises(ValueError):FileStore(store.root/'link')

    def test_failed_publication_does_not_leave_visible_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=FileStore(tmp)
            with patch('cloud_governance.storage.os.link',side_effect=OSError('disk full')):
                with self.assertRaises(OSError):store.put_new('runs/r/object',b'payload')
            self.assertEqual([],store.keys('runs/'))
            self.assertFalse(list(Path(tmp).rglob('.pending-*')))


class ArchiveTests(unittest.TestCase):
    def test_separate_facts_results_context_and_new_run_each_time(self):
        snapshot,report=evidence();original=copy.deepcopy((snapshot,report));store=MemoryStore()
        first=save_run(store,snapshot,report);before=dict(store.objects)
        second=save_run(store,snapshot,report)
        self.assertNotEqual(first['run_id'],second['run_id'])
        self.assertEqual(before,{k:store.objects[k] for k in before})
        saved=load_run(store,first['run_id'])
        self.assertEqual(original,(saved['snapshot'],saved['assessment']))
        self.assertEqual(original,(snapshot,report))
        self.assertEqual(23,len(saved['context']['program_scope']['services']))
        self.assertEqual({'snapshot','assessment','context'},set(first['objects']))
        self.assertEqual(['complete','complete'],[r['archive_state'] for r in list_runs(store)])

    def test_historical_load_never_reassesses_or_uses_current_catalog(self):
        snapshot,report=evidence();store=MemoryStore();m=save_run(store,snapshot,report)
        with (patch('cloud_governance.assessment.assess',side_effect=AssertionError('reassessment forbidden')),
             patch('cloud_governance.archive.validate_snapshot',side_effect=AssertionError('current schema/rules forbidden')),
             patch('cloud_governance.archive.make_context',side_effect=AssertionError('current context forbidden'))):
            self.assertEqual(report,load_run(store,m['run_id'])['assessment'])

    def test_each_partial_run_stage_is_unreportable_and_listed_failed(self):
        snapshot,report=evidence()
        for suffix in ('snapshot.json','assessment.json','context.json','manifest.json'):
            with self.subTest(stage=suffix):
                store=MemoryStore(suffix)
                with self.assertRaises(OSError):save_run(store,snapshot,report)
                listing=list_runs(store);self.assertEqual('failed',listing[0]['archive_state'])
                with self.assertRaises(ValueError):load_run(store,listing[0]['run_id'])
                self.assertFalse(any(b'sensitive error payload must not appear in state' in value for value in store.objects.values()))

    def test_interrupted_run_without_failure_marker_is_incomplete(self):
        store=MemoryStore();run='r-'+'a'*32
        store.put_new('runs/'+run+'/intent.json',b'{}')
        self.assertEqual([{'run_id':run,'archive_state':'incomplete'}],list_runs(store))

    def test_missing_corrupt_and_cross_run_objects_fail_closed(self):
        snapshot,report=evidence()
        for mode in ('corrupt','missing','crossrun','metadata'):
            store=MemoryStore();m=save_run(store,snapshot,report);run=m['run_id']
            key=m['objects']['snapshot']['key']
            if mode=='corrupt':store.objects[key]+=b' '
            elif mode=='missing':del store.objects[key]
            else:
                if mode=='crossrun':m['objects']['snapshot']['key']='runs/r-'+'b'*32+'/snapshot.json'
                else:m['collection_started_at']='2099-01-01T00:00:00Z'
                store.objects['runs/'+run+'/manifest.json']=encode(m)
            with self.subTest(mode=mode),self.assertRaises((OSError,ValueError)):load_run(store,run)
            self.assertEqual('corrupt_or_incomplete',list_runs(store)[0]['archive_state'])

    def test_mismatched_saved_findings_and_summary_are_rejected_before_write(self):
        snapshot,report=evidence()
        for mutate in [lambda r:r.update(snapshot_sha256='0'*64),
                       lambda r:r['results'][0]['evidence'].update(password='bad'),
                       lambda r:r['summary'].update(coverage_incomplete=True),
                       lambda r:r['results'][0].update(result='FAIL')]:
            bad=copy.deepcopy(report);mutate(bad);store=MemoryStore()
            with self.assertRaises(ValueError):save_run(store,snapshot,bad)
            self.assertEqual({},store.objects)

    def test_identity_and_manifest_version_validation(self):
        for run in ['latest','../runs/other','r-'+'a'*31,'r-'+'A'*32]:
            with self.assertRaises(ValueError):load_run(MemoryStore(),run)
        s,r=evidence();store=MemoryStore();m=save_run(store,s,r)
        m['schema_version']='99';store.objects['runs/'+m['run_id']+'/manifest.json']=encode(m)
        with self.assertRaises(ValueError):load_run(store,m['run_id'])

    def test_id_collision_cannot_overwrite_existing_run(self):
        from uuid import UUID
        s,r=evidence();store=MemoryStore()
        with patch('cloud_governance.archive.uuid4',return_value=UUID(int=1)):
            save_run(store,s,r);original=dict(store.objects)
            with self.assertRaises(FileExistsError):save_run(store,s,r)
        self.assertEqual(original,store.objects)

    def test_failure_marker_overrides_uncertain_manifest_acknowledgement(self):
        s,r=evidence();store=MemoryStore();m=save_run(store,s,r)
        store.put_new('runs/'+m['run_id']+'/failure.json',encode({'stage':'completion_manifest','state':'failed'}))
        with self.assertRaises(ValueError):load_run(store,m['run_id'])
        self.assertEqual('failed',list_runs(store)[0]['archive_state'])
