from cloud_governance import report_model
import json
import unittest
from cloud_governance.catalog import RULES
from cloud_governance.collector import endpoint
from cloud_governance.workflow import assess_snapshot
from cloud_governance.archive import save_run,load_run,publish_pdf
from tests.helpers import Scenario,resource
from tests.test_archive import MemoryStore


TYPES=('Microsoft.Dashboard/grafana','Microsoft.Monitor/accounts','Microsoft.Automation/automationAccounts')


class AdditionalEncryptionTests(unittest.TestCase):
    def test_scoped_provider_guarantees_keep_boundaries_and_exclude_payloads(self):
        for kind in TYPES:
            row=resource(kind,properties={'provisioningState':'Succeeded','credentials':{'password':'SECRET-CANARY'},'jobOutput':'SECRET-CANARY'})
            s=Scenario([row]);s.run();result=s.result(row)
            self.assertEqual('PASS',result['result']);self.assertEqual('documented_service_guarantee',result['basis'])
            self.assertIn('only;',result['scope']);self.assertNotIn('SECRET-CANARY',json.dumps(s.snapshot))
            self.assertNotIn('SECRET-CANARY',json.dumps(s.report))
            command=result['verification_commands'][0]
            self.assertEqual(RULES[kind.lower()].api,command['api_version'])

    def test_denied_mismatched_identity_and_unstable_provisioning_never_pass(self):
        for kind in TYPES:
            for response in ({'fixture_error':403},resource(kind,'different'),resource(kind,properties={'provisioningState':'Updating'})):
                row=resource(kind);s=Scenario([row]);s.responses[endpoint(row['id'],RULES[kind.lower()].api)]=response;s.run()
                self.assertIn(s.result(row)['result'],('ERROR','UNKNOWN'))

    def test_unreviewed_child_types_do_not_inherit_parent_guarantees(self):
        for kind in TYPES:
            row=resource(kind+'/unknownAssets','parent/child');s=Scenario([row]);s.run()
            self.assertEqual('UNSUPPORTED',s.result(row)['result'])

    def test_sources_and_scopes_are_frozen_in_archives_and_reports(self):
        s=Scenario([resource(kind) for kind in TYPES]);s.run();report=assess_snapshot(s.snapshot)
        store=MemoryStore();run=save_run(store,s.snapshot,report)['run_id'];before=dict(store.objects);publish_pdf(store,run)
        saved=load_run(store,run)['assessment'];self.assertEqual(report,saved)
        for row in report_model.resource_results(saved):
            self.assertEqual('PASS',row['result']);self.assertTrue(row['sources']);self.assertTrue(row['scope'])
        self.assertTrue(all(store.objects[k]==v for k,v in before.items()))
