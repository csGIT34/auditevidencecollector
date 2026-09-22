from cloud_governance import report_model
import json
import unittest
from cloud_governance.catalog import MANAGED_REDIS_FAMILIES, RULES
from cloud_governance.collector import endpoint
from cloud_governance.workflow import assess_snapshot
from cloud_governance.archive import save_run, load_run, publish_pdf
from tests.helpers import Scenario, resource
from tests.test_archive import MemoryStore

CLUSTER = 'Microsoft.Cache/redisEnterprise'
DATABASE = 'Microsoft.Cache/redisEnterprise/databases'
CACHE = 'Microsoft.Cache/Redis'
CANARY = 'DO-NOT-ARCHIVE-SECRET'
REVIEWED = ('Enterprise_E10', 'EnterpriseFlash_F300', 'Balanced_B10', 'MemoryOptimized_M20',
            'ComputeOptimized_X5', 'FlashOptimized_A250')


def cluster(sku='Balanced_B10', name='cache'):
    return resource(CLUSTER, name, {'provisioningState': 'Succeeded'}, sku=sku)


def database(parent='cache', name='default', rdb=True, aof=False):
    return resource(DATABASE, parent + '/' + name, {'provisioningState': 'Succeeded',
                                                    'persistence': {'rdbEnabled': rdb, 'aofEnabled': aof}})


def cache(name='legacy', sku='Premium', family='P', capacity=1, persistence=None):
    properties = {'provisioningState': 'Succeeded', 'sku': {'name': sku, 'family': family, 'capacity': capacity}}
    if persistence is not None:
        properties['redisConfiguration'] = persistence
    return resource(CACHE, name, properties)


class ManagedRedisTests(unittest.TestCase):
    def test_every_reviewed_sku_family_passes_on_its_documented_disk_boundary(self):
        for sku in REVIEWED:
            row = cluster(sku)
            scenario = Scenario([row]); scenario.run(); result = scenario.result(row)
            self.assertEqual('PASS', result['result'])
            self.assertEqual('documented_service_guarantee', result['basis'])
            self.assertIn('not encrypted', result['reason'])
            # Only the flash families store keys and values on the transient NVMe disk.
            self.assertEqual('Flash' in sku, 'NVMe' in result['reason'])
            command = result['verification_commands'][0]
            self.assertEqual(RULES[CLUSTER.lower()].api, command['api_version'])
            self.assertIn('reviewed families only', json.dumps(command['expected_fields']))

    def test_unlisted_or_missing_sku_never_inherits_a_family_guarantee(self):
        for row in (cluster('Unlisted_Z1'), resource(CLUSTER, 'nosku', {'provisioningState': 'Succeeded'})):
            scenario = Scenario([row]); scenario.run(); result = scenario.result(row)
            self.assertEqual('UNKNOWN', result['result'])
            self.assertEqual('none', result['basis'])

    def test_database_persistence_is_covered_by_its_verified_cluster(self):
        parent, child = cluster(), database()
        scenario = Scenario([parent]).children(parent, 'databases', [child]); scenario.run()
        self.assertEqual('PASS', scenario.result(parent)['result'])
        result = scenario.result(child)
        self.assertEqual('PASS', result['result'])
        self.assertIn('rdbEnabled', result['reason'])
        self.assertEqual([RULES[DATABASE.lower()].source, RULES[CLUSTER.lower()].source],
                         [source['url'] for source in result['sources']])

    def test_database_without_persistence_states_only_cluster_managed_files(self):
        parent, child = cluster(), database(rdb=False, aof=False)
        scenario = Scenario([parent]).children(parent, 'databases', [child]); scenario.run()
        self.assertIn('No persistence is declared', scenario.result(child)['reason'])

    def test_denied_or_incomplete_database_evidence_blocks_the_cluster(self):
        parent, child = cluster(), database()
        listing = endpoint(parent['id'] + '/databases', RULES[CLUSTER.lower()].api)
        for broken in ({listing: {'fixture_error': 403}},
                       {endpoint(child['id'], RULES[DATABASE.lower()].api): {'fixture_error': 403}},
                       {endpoint(child['id'], RULES[DATABASE.lower()].api): resource(DATABASE, 'cache/other')}):
            scenario = Scenario([parent]).children(parent, 'databases', [child])
            scenario.responses.update(broken); scenario.run()
            result = scenario.result(parent)
            self.assertEqual('UNKNOWN', result['result'])
            self.assertTrue(result['gaps'])

    def test_database_without_a_verified_reviewed_cluster_stays_unknown(self):
        parent, child = cluster('Unlisted_Z1'), database()
        scenario = Scenario([parent]).children(parent, 'databases', [child]); scenario.run()
        result = scenario.result(child)
        self.assertEqual('UNKNOWN', result['result'])
        self.assertEqual('backing_storage_required', result['basis'])
        orphan = database('missing')
        scenario = Scenario([orphan]); scenario.run()
        self.assertEqual('UNKNOWN', scenario.result(orphan)['result'])

    def test_legacy_cache_tiers_select_their_documented_statement(self):
        off = {'rdb-backup-enabled': 'false', 'aof-backup-enabled': 'false'}
        cases = [(cache('basic', 'Basic', 'C', 0), 'FAIL'), (cache('standard1', 'Standard', 'C', 1), 'FAIL'),
                 (cache('standard2', 'Standard', 'C', 2), 'PASS'), (cache('premium', persistence=off), 'PASS'),
                 (cache('persisted', persistence={**off, 'rdb-backup-enabled': 'true'}), 'UNKNOWN'),
                 (cache('unreported'), 'UNKNOWN'),
                 (resource(CACHE, 'notier', {'provisioningState': 'Succeeded'}), 'UNKNOWN')]
        for row, expected in cases:
            scenario = Scenario([row]); scenario.run()
            self.assertEqual(expected, scenario.result(row)['result'], row['name'])

    def test_no_connection_string_key_or_link_payload_reaches_evidence(self):
        parent = cluster()
        parent['properties']['accessKeys'] = {'primaryKey': CANARY}
        child = database()
        child['properties'].update(geoReplication={'groupNickname': CANARY, 'linkedDatabases': [{'id': CANARY}]},
                                   secretCanary=CANARY)
        legacy = cache('legacy', persistence={'rdb-backup-enabled': 'false', 'aof-backup-enabled': 'false',
                                              'rdb-storage-connection-string': CANARY})
        scenario = Scenario([parent, legacy]).children(parent, 'databases', [child]); scenario.run()
        self.assertNotIn(CANARY, json.dumps(scenario.snapshot))
        self.assertNotIn(CANARY, json.dumps(scenario.report))

    def test_saved_run_preserves_decisions_sources_and_original_objects(self):
        parent, child = cluster(), database()
        legacy = cache('legacy', persistence={'rdb-backup-enabled': 'false', 'aof-backup-enabled': 'false'})
        scenario = Scenario([parent, legacy]).children(parent, 'databases', [child]); scenario.run()
        report = assess_snapshot(scenario.snapshot)
        store = MemoryStore(); run = save_run(store, scenario.snapshot, report)['run_id']
        before = dict(store.objects); publish_pdf(store, run)
        saved = load_run(store, run)['assessment']
        self.assertEqual(report, saved)
        self.assertEqual({'PASS'}, {row['result'] for row in report_model.resource_results(saved)})
        for row in report_model.resource_results(saved):
            self.assertTrue(row['sources'] and row['scope'])
        self.assertTrue(all(store.objects[key] == value for key, value in before.items()))

    def test_every_reviewed_family_prefix_is_exercised(self):
        self.assertEqual(set(MANAGED_REDIS_FAMILIES), {sku.split('_')[0].lower() + '_' for sku in REVIEWED})
