import json
from pathlib import Path
import tempfile
import unittest
from azure_at_rest.control_register import CONTROLS, STATUSES, build, markdown, validate_purview
from azure_at_rest.cli import main
from tests.test_controls import collect, fixture
from azure_at_rest.workflow import assess_snapshot

ROOT = Path(__file__).resolve().parents[1]


def report():
    responses, policy = fixture()
    return assess_snapshot(collect(responses), criteria=policy)


def purview(disposition='IN_SCOPE', status='approved', control='AC-6', **extra):
    return {'schema_version': '1.0', 'id': 'example-purview', 'version': '1', 'status': status,
            'controls': {control: {'disposition': disposition, 'owner': 'Platform security', **extra}}}


def row(register, control):
    return next(r for r in register['controls'] if r['control'] == control)


class ControlRegisterTests(unittest.TestCase):
    def test_both_evidence_kinds_are_indexed_under_their_declared_controls(self):
        register = build(report())
        self.assertEqual(189, register['summary']['controls'])
        encryption = row(register, 'SC-28(1)')
        self.assertTrue(any(item['kind'] == 'encryption_rule' for item in encryption['evidence']))
        access = row(register, 'AC-6')
        self.assertTrue(all(item['kind'] == 'configuration_predicate' for item in access['evidence']))
        self.assertEqual(access['counts']['PASS'], access['evidence_count'])
        # Every indexed item keeps its originating reference for traceability.
        self.assertTrue(all(item['reference'] for item in access['evidence']))

    def test_no_status_asserts_that_a_control_is_satisfied(self):
        register = build(report())
        self.assertNotIn('SATISFIED', ' '.join(STATUSES))
        for entry in register['controls']:
            self.assertIn(entry['status'], STATUSES)
        collected = [e for e in register['controls'] if e['status'] == 'AUTOMATED_EVIDENCE_COLLECTED']
        self.assertTrue(collected)
        for entry in collected:
            self.assertTrue(any('Assessor determination' in gap for gap in entry['gaps']))

    def test_failed_and_incomplete_observations_reach_their_controls(self):
        source = report()
        source['configuration_assessment']['results'][0]['result'] = 'FAIL'
        controls = source['configuration_assessment']['results'][0]['control_refs']
        register = build(source)
        self.assertEqual('FINDINGS_PRESENT', row(register, controls[0])['status'])
        source['configuration_assessment']['results'][0]['result'] = 'UNKNOWN'
        self.assertEqual('INCOMPLETE_EVIDENCE', row(build(source), controls[0])['status'])

    def test_controls_without_any_evidence_are_explicitly_not_assessed(self):
        register = build(report())
        physical = row(register, 'PE-3')
        self.assertEqual('NOT_ASSESSED', physical['status'])
        self.assertEqual(0, physical['evidence_count'])
        self.assertTrue(any('No automated observation' in gap for gap in physical['gaps']))
        self.assertEqual('UNDECLARED', physical['purview'])

    def test_approved_exclusion_is_honored_and_a_draft_exclusion_is_not(self):
        source = report()
        approved = build(source, purview('EXCLUDED', 'approved', 'PE-3', rationale='Provider datacenter control',
                                         approver='Security officer'))
        self.assertEqual('EXCLUDED', row(approved, 'PE-3')['status'])
        draft = build(source, purview('EXCLUDED', 'draft', 'PE-3', rationale='Provider datacenter control',
                                      approver='Security officer'))
        entry = row(draft, 'PE-3')
        self.assertEqual('NOT_ASSESSED', entry['status'])
        self.assertTrue(any('not honored' in gap for gap in entry['gaps']))

    def test_claimed_inheritance_records_a_gap_until_assurance_is_referenced(self):
        source = report()
        bare = build(source, purview('INHERITED', 'approved', 'PE-2', rationale='Azure datacenter'))
        entry = row(bare, 'PE-2')
        self.assertEqual('INHERITED_CLAIMED', entry['status'])
        self.assertTrue(any('assurance reference' in gap for gap in entry['gaps']))
        cited = build(source, purview('INHERITED', 'approved', 'PE-2', rationale='Azure datacenter',
                                      assurance_reference='SOC 2 Type II 2026, section 4'))
        self.assertFalse(any('assurance reference' in gap for gap in row(cited, 'PE-2')['gaps']))

    def test_invalid_purview_documents_are_rejected(self):
        cases = [purview(control='AC-6') | {'schema_version': '2.0'},
                 purview(control='AC-6') | {'status': 'signed'},
                 {**purview(), 'controls': {'NOPE-9': {'disposition': 'IN_SCOPE', 'owner': 'x'}}},
                 {**purview(), 'controls': {'AC-6': {'disposition': 'MAYBE', 'owner': 'x'}}},
                 {**purview(), 'controls': {'AC-6': {'disposition': 'EXCLUDED', 'owner': 'x', 'rationale': 'r'}}},
                 {**purview(), 'controls': {'AC-6': {'disposition': 'INHERITED', 'owner': 'x'}}}]
        for document in cases:
            with self.assertRaises(ValueError):
                validate_purview(document)
        self.assertIsNone(validate_purview(None))

    def test_attributed_records_are_kept_distinct_from_automated_observations(self):
        operational = {'records': [{'id': 'IR-drill-2026Q3', 'title': 'Tabletop exercise', 'scope': 'tenant',
                                    'control_refs': ['IR-3']}]}
        entry = row(build(report(), None, operational), 'IR-3')
        self.assertEqual('ATTRIBUTED_EVIDENCE_ONLY', entry['status'])
        self.assertEqual(1, entry['counts']['ATTRIBUTED'])
        self.assertEqual(0, entry['counts']['PASS'])

    def test_markdown_shows_every_family_and_keeps_its_limitations(self):
        text = markdown(build(report()))
        for family in ('AC —', 'PE —', 'PM —', 'SR —'):
            self.assertIn(family, text)
        self.assertIn('NOT DECLARED', text)
        self.assertIn('no status in this register means a control is satisfied'.lower(), text.lower())

    def test_cli_indexes_a_saved_assessment_without_touching_its_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            source = path / 'report.json'
            source.write_text(json.dumps(report()))
            before = source.read_text()
            code = main(['control-register', '--input', str(source), '--json', str(path / 'register.json'),
                         '--report', str(path / 'register.md')])
            self.assertEqual(0, code)
            self.assertEqual(before, source.read_text())
            saved = json.loads((path / 'register.json').read_text())
            self.assertEqual(189, saved['summary']['controls'])
            self.assertFalse(saved['purview']['declared'])
            self.assertIn('# Control-indexed evidence register', (path / 'register.md').read_text())
            # Refusing to overwrite the input is reported as a failure code, not a traceback.
            self.assertNotEqual(0, main(['control-register', '--input', str(source), '--json', str(source)]))
            self.assertEqual(before, source.read_text())

    def test_packaged_control_index_matches_the_reviewed_catalog(self):
        import subprocess
        import sys
        subprocess.run([sys.executable, str(ROOT / 'docs/audit/export_control_index.py'), '--check'],
                       check=True, cwd=ROOT)
        self.assertEqual(208, len(CONTROLS))
