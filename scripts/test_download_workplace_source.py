"""Offline transfer checks; not part of the downloaded application."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.download_workplace_source import download


class DownloadTests(unittest.TestCase):
    def run_download(self, directory, files, payloads):
        def fetch(url):
            if url.endswith('/docs/workplace-files.json'):
                return json.dumps({'schema_version': 1, 'files': files}).encode()
            return payloads[url.split('/workplace/', 1)[1]]
        with patch('scripts.download_workplace_source.fetch', side_effect=fetch):
            download(directory, 'a' * 40)

    def test_exact_payload_without_transfer_metadata(self):
        data = {'README.md': b'project\n', 'code/main.py': b'print(1)\n', '.gitignore': b'.venv/\n'}
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'project'
            self.run_download(target, {n: hashlib.sha256(b).hexdigest() for n, b in data.items()}, data)
            self.assertEqual(set(data), {str(p.relative_to(target)) for p in target.rglob('*') if p.is_file()})
            for name, payload in data.items():
                self.assertEqual(payload, (target/name).read_bytes())

    def test_hash_failure_does_not_publish_partial_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'project'
            with self.assertRaises(ValueError):
                self.run_download(target, {'README.md': '0'*64}, {'README.md': b'wrong'})
            self.assertEqual([], list(Path(tmp).iterdir()))

    def test_unsafe_paths_rejected_before_payload_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('../outside', '/absolute', '.git/config', 'a/../../outside', 'a\\outside'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    self.run_download(Path(tmp)/'project', {name: '0'*64}, {})
            self.assertEqual([], list(Path(tmp).iterdir()))

    def test_existing_destination_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'project'
            target.mkdir()
            (target/'keep').write_text('unchanged')
            with self.assertRaises(FileExistsError):
                self.run_download(target, {'README.md': '0'*64}, {})
            self.assertEqual('unchanged', (target/'keep').read_text())

    def test_exact_commit_required(self):
        with self.assertRaises(ValueError):
            download('/unused', 'main')
