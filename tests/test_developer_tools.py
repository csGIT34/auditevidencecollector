from pathlib import Path
import tempfile
import unittest
from scripts.check_docs import broken_links
from scripts.benchmark_pipeline import fixture, SUB
from azure_at_rest.collector import Collector, FixtureTransport


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
        from azure_at_rest.assessment import assess
        transport = FixtureTransport(fixture(101))
        snapshot = Collector(transport, mode='offline_fixture').collect([SUB])
        self.assertEqual(101, len(snapshot['resources']))
        self.assertEqual(2, snapshot['inventory']['subscriptions'][0]['pages'])
        counts = assess(snapshot)['summary']['counts']
        self.assertTrue(all(counts[k] > 0 for k in ('PASS','FAIL','UNKNOWN','ERROR','UNSUPPORTED','NOT_APPLICABLE')))
