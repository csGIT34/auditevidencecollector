from pathlib import Path
import unittest
from scripts.control_delivery_register import register,ROOT
from azure_at_rest.controls import CHECKS


class DeliveryRegisterTests(unittest.TestCase):
    def test_every_predicate_has_exact_objective_and_real_implementation_test_report_links(self):
        data=register();rows={r['id']:r for r in data['checks']};caps=data['capabilities']
        self.assertEqual(215,len(rows))
        self.assertEqual(set(CHECKS),{key.split(':',1)[1] for key in caps if key.startswith('configuration:')})
        for key,cap in caps.items():
            for objective in cap['catalog_objectives']:
                self.assertIn(key,rows[objective]['implementation_refs'])
            for path in cap['implementation_files']+cap['test_files']+cap.get('report_files',[])+[cap['permissions_guide']]:
                self.assertTrue((ROOT/path).is_file(),path)
            self.assertEqual('NOT_VERIFIED',cap['live_validation'])
            self.assertTrue(cap['criteria']);self.assertTrue(cap['reporting']);self.assertTrue(cap['remaining_dependencies'])
        for row in rows.values():
            for key in row['implementation_refs']:self.assertIn(row['id'],caps[key]['catalog_objectives'])
            self.assertTrue(row['required_evidence']);self.assertTrue(row['criteria_requirements'])
            self.assertTrue(row['remaining_acceptance_boundary'])
            self.assertTrue(set(row['proposed_permission_profiles'])<=set(data['proposed_permission_profiles']))

    def test_metadata_never_marks_whole_objective_or_manual_assertion_accepted(self):
        data=register();self.assertEqual(0,data['complete_objectives'])
        for row in data['checks']:
            self.assertFalse(row['whole_objective_complete'])
            self.assertIsNone(row['disposition']['exclusion'])
            self.assertEqual('NOT_ASSESSED',row['disposition']['manual_or_inherited_acceptance'])
            support=bool(row['implementation_refs'] or row['existing_encryption_rules'])
            self.assertEqual('PARTIAL_EXECUTABLE_SUPPORT' if support else 'NOT_IMPLEMENTED',row['state'])

    def test_planes_and_specialized_adapters_are_not_inferred_from_parent_arm_type(self):
        caps=register()['capabilities']
        self.assertEqual('MICROSOFT_GRAPH',caps['configuration:APPREG-delegated-grants']['collection_plane'])
        self.assertEqual('KEY_VAULT_DATA_METADATA',caps['configuration:KV-secrets-lifecycle']['collection_plane'])
        self.assertIn('azure_at_rest/automation_assets.py',caps['configuration:AUTO-runtime-packages']['implementation_files'])
        self.assertEqual('NORMALIZED_GUEST_EXPORT',caps['guest:missing_critical_patches']['collection_plane'])
        self.assertEqual('KUBERNETES_METADATA',caps['workload:privileged']['collection_plane'])
