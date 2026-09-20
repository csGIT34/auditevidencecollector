from cloud_governance import report_model
from pathlib import Path
import tempfile
import unittest
from scripts.check_docs import broken_links
from scripts.benchmark_pipeline import fixture, SUB
from cloud_governance.collector import Collector, FixtureTransport


class DeveloperToolTests(unittest.TestCase):
    def test_doc_links_detect_missing_targets_and_ignore_external_urls_and_examples(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'present file.md').write_text('ok')
            doc = root/'README.md'
            doc.write_text('[ok](present%20file.md#heading) [bad](missing.md) [external](https://example.invalid/x)\n'
                           '```sh\n[example](not-real.md)\n```\n[anchor](#local)\n')
            self.assertEqual(['README.md: missing relative target missing.md'], broken_links(root, [doc]))

    def test_scale_fixture_exercises_pagination_denial_and_mixed_outcomes(self):
        from cloud_governance.assessment import assess
        transport = FixtureTransport(fixture(101))
        snapshot = Collector(transport, mode='offline_fixture').collect([SUB])
        self.assertEqual(101, len(snapshot['resources']))
        self.assertEqual(2, snapshot['inventory']['subscriptions'][0]['pages'])
        counts = report_model.resource_summary(assess(snapshot))['counts']
        self.assertTrue(all(counts[k] > 0 for k in ('PASS','FAIL','UNKNOWN','ERROR','UNSUPPORTED','NOT_APPLICABLE')))

    def test_the_source_package_carries_every_data_file_the_package_imports(self):
        import zipfile, tempfile, subprocess, sys
        from pathlib import Path as P
        root = P(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            target = P(temp)/'source.zip'
            subprocess.run([sys.executable, str(root/'scripts/package_functions.py'), '--output', str(target)],
                           check=True, cwd=root, capture_output=True)
            names = set(zipfile.ZipFile(target).namelist())
        # Any JSON the package loads at import time must ship with it.
        for data in sorted(p.name for p in (root/'cloud_governance').glob('*.json')):
            self.assertIn('cloud_governance/'+data, names, data)
