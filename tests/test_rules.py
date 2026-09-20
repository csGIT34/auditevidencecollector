import copy
import unittest

from azure_at_rest.catalog import RULES
from azure_at_rest.collector import endpoint
from tests.helpers import Scenario, resource


class RuleTests(unittest.TestCase):
    def result(self, kind, props=None, sku=None):
        row = resource(kind, properties=props, sku=sku)
        scenario = Scenario([row])
        scenario.run()
        return scenario.result(row)

    def test_service_guarantees_accept_missing_optional_cmk(self):
        for kind in ("Microsoft.Storage/storageAccounts", "Microsoft.Compute/disks", "Microsoft.Compute/snapshots", "Microsoft.Compute/images",
                     "Microsoft.DBforPostgreSQL/flexibleServers", "Microsoft.DBforMySQL/flexibleServers",
                     "Microsoft.DocumentDB/databaseAccounts", "Microsoft.DocumentDB/mongoClusters", "Microsoft.ContainerRegistry/registries",
                     "Microsoft.RecoveryServices/vaults", "Microsoft.DataProtection/backupVaults", "Microsoft.OperationalInsights/workspaces",
                     "Microsoft.AppConfiguration/configurationStores", "Microsoft.KeyVault/vaults", "Microsoft.Search/searchServices"):
            with self.subTest(kind=kind):
                result = self.result(kind)
                self.assertEqual("PASS", result["result"])
                self.assertEqual("documented_service_guarantee", result["basis"])
                self.assertTrue(result["sources"])

    def test_storage_contradiction_is_unknown(self):
        result = self.result("Microsoft.Storage/storageAccounts", {"encryption": {"services": {"blob": {"enabled": False}}}})
        self.assertEqual("UNKNOWN", result["result"])

    def test_unrecognized_encryption_value_is_unknown(self):
        result = self.result("Microsoft.Compute/disks", {"encryption": {"type": "FutureEncryption"}})
        self.assertEqual("UNKNOWN", result["result"])

    def test_ade_disabled_does_not_disable_sse(self):
        result = self.result("Microsoft.Compute/disks", {"encryptionSettingsCollection": {"enabled": False}})
        self.assertEqual("PASS", result["result"])

    def test_acr_cmk_disabled_does_not_disable_default_encryption(self):
        self.assertEqual("PASS", self.result("Microsoft.ContainerRegistry/registries", {"encryption": {"status": "disabled"}})["result"])

    def test_failed_or_transitional_provisioning_not_pass(self):
        for state in ("Creating", "Failed", "Deleting", "Canceled", "Unknown"):
            self.assertEqual("UNKNOWN", self.result("Microsoft.Storage/storageAccounts", {"provisioningState": state})["result"])

    def test_tde_must_be_explicit(self):
        for state, expected in (("Enabled", "PASS"), ("Disabled", "FAIL"), (None, "UNKNOWN"), ("Enabling", "UNKNOWN"), (True, "UNKNOWN"), ([], "UNKNOWN")):
            with self.subTest(state=state):
                db = resource("Microsoft.Sql/servers/databases", "server/db")
                s = Scenario([db]).tde(db, state)
                s.run()
                self.assertEqual(expected, s.result(db)["result"])

    def test_missing_tde_endpoint_is_error(self):
        db = resource("Microsoft.Sql/servers/databases", "server/db")
        s = Scenario([db]); s.run()
        self.assertEqual("ERROR", s.result(db)["result"])

    def test_sql_mi_tde_disabled_fails(self):
        db = resource("Microsoft.Sql/managedInstances/databases", "server/db")
        s = Scenario([db]).tde(db, "Disabled"); s.run()
        self.assertEqual("FAIL", s.result(db)["result"])

    def test_synapse_status_field(self):
        db = resource("Microsoft.Synapse/workspaces/sqlPools", "ws/pool")
        s = Scenario([db]).tde(db)
        tde = s.responses[endpoint(db["id"] + "/transparentDataEncryption/current", RULES[db["type"].lower()].api)]
        tde["properties"] = {"status": "Enabled"}
        s.run()
        self.assertEqual("PASS", s.result(db)["result"])

    def test_master_is_narrow_na_and_no_tde_get(self):
        db = resource("Microsoft.Sql/servers/databases", "server/master")
        s = Scenario([db]); s.run()
        self.assertEqual("NOT_APPLICABLE", s.result(db)["result"])
        self.assertFalse(any("transparentDataEncryption" in u for u in s.transport.calls))

    def test_sql_parent_aggregates_child_failure(self):
        server = resource("Microsoft.Sql/servers", "server")
        db = resource("Microsoft.Sql/servers/databases", "server/db")
        s = Scenario([server]).children(server, "databases", [db]).tde(db, "Disabled"); s.run()
        self.assertEqual(2, s.report["summary"]["resource_count"])
        self.assertEqual("FAIL", s.result(server)["result"])

    def test_sql_parent_complete_empty_is_na(self):
        self.assertEqual("NOT_APPLICABLE", self.result("Microsoft.Sql/servers")["result"])

    def test_kusto_cache_independent_from_storage(self):
        for props, expected in (({}, "UNKNOWN"), ({"enableDiskEncryption": False}, "FAIL"), ({"enableDiskEncryption": True}, "PASS")):
            self.assertEqual(expected, self.result("Microsoft.Kusto/clusters", props)["result"])

    def test_service_bus_tier_is_required(self):
        for sku, expected in ((None, "UNKNOWN"), ("Basic", "UNKNOWN"), ("Standard", "UNKNOWN"), ("Premium", "PASS")):
            self.assertEqual(expected, self.result("Microsoft.ServiceBus/namespaces", sku=sku)["result"])

    def test_compute_and_apps_do_not_pass_on_one_property(self):
        for kind in ("Microsoft.Compute/virtualMachines", "Microsoft.Compute/virtualMachineScaleSets", "Microsoft.ContainerService/managedClusters",
                     "Microsoft.App/containerApps", "Microsoft.App/jobs", "Microsoft.App/managedEnvironments", "Microsoft.Web/sites"):
            with self.subTest(kind=kind):
                self.assertEqual("UNKNOWN", self.result(kind, {"securityProfile": {"encryptionAtHost": True}})["result"])

    def test_vm_resolves_disk_and_keeps_workload_gap(self):
        disk = resource("Microsoft.Compute/disks", "disk")
        vm = resource("Microsoft.Compute/virtualMachines", "vm", {"storageProfile": {"osDisk": {"managedDisk": {"id": disk["id"]}}}})
        s = Scenario([disk, vm]); s.run()
        result = s.result(vm)
        self.assertEqual("UNKNOWN", result["result"])
        self.assertEqual("PASS", result["dependencies"][0]["result"])
        self.assertTrue(result["gaps"])

    def test_unresolved_dependency_not_pass(self):
        workspace = resource("Microsoft.OperationalInsights/workspaces", "missing")
        app = resource("Microsoft.Insights/components", "app", {"WorkspaceResourceId": workspace["id"]})
        s = Scenario([app]); s.run()
        self.assertEqual("UNKNOWN", s.result(app)["result"])
        self.assertFalse(s.result(app)["dependencies"][0]["resolved"])

    def test_workspace_backed_app_insights(self):
        workspace = resource("Microsoft.OperationalInsights/workspaces", "logs")
        app = resource("Microsoft.Insights/components", "app", {"WorkspaceResourceId": workspace["id"]})
        s = Scenario([app, workspace]); s.run()
        self.assertEqual("PASS", s.result(app)["result"])

    def test_capture_missing_fields_prevent_namespace_pass(self):
        ns = resource("Microsoft.EventHub/namespaces", "events")
        hub = resource("Microsoft.EventHub/namespaces/eventhubs", "events/hub")
        s = Scenario([ns]).children(ns, "eventhubs", [hub]); s.run()
        self.assertEqual("UNKNOWN", s.result(hub)["result"])
        self.assertEqual("UNKNOWN", s.result(ns)["result"])

    def test_capture_backing_storage_resolved(self):
        storage = resource("Microsoft.Storage/storageAccounts", "capturestore")
        ns = resource("Microsoft.EventHub/namespaces", "events")
        hub = resource("Microsoft.EventHub/namespaces/eventhubs", "events/hub", {
            "captureDescription": {"enabled": True, "destination": {"name": "EventHubArchive.AzureBlockBlob", "properties": {"storageAccountResourceId": storage["id"]}}}})
        s = Scenario([ns, storage]).children(ns, "eventhubs", [hub]); s.run()
        self.assertEqual("PASS", s.result(ns)["result"])

    def test_redis_persistence_is_not_assumed(self):
        disabled = {"sku": {"name": "Premium", "family": "P", "capacity": 1},
                    "redisConfiguration": {"rdb-backup-enabled": "false", "aof-backup-enabled": "false"}}
        self.assertEqual("PASS", self.result("Microsoft.Cache/Redis", disabled)["result"])
        self.assertEqual("UNKNOWN", self.result("Microsoft.Cache/Redis", {**disabled, "redisConfiguration": {"rdb-backup-enabled": "true"}})["result"])
        self.assertEqual("UNKNOWN", self.result("Microsoft.Cache/Redis", {"redisConfiguration": {"rdb-backup-enabled": "false", "aof-backup-enabled": "false"}})["result"])
        self.assertEqual("PASS", self.result("Microsoft.Cache/redisEnterprise", sku="Enterprise_E10")["result"])
        self.assertEqual("PASS", self.result("Microsoft.Cache/redisEnterprise", sku="Balanced_B10")["result"])
        self.assertEqual("UNKNOWN", self.result("Microsoft.Cache/redisEnterprise", sku="Unlisted_Z1")["result"])

    def test_network_is_justified_na_but_unknown_services_are_not(self):
        self.assertEqual("NOT_APPLICABLE", self.result("Microsoft.Network/virtualNetworks")["result"])
        result = self.result("MongoDB.Atlas/organizations")
        self.assertEqual("UNSUPPORTED", result["result"])
        self.assertEqual([], result["sources"])
