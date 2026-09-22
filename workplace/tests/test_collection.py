from cloud_governance import report_model
import copy
import io
import json
import unittest
from urllib.error import HTTPError

from cloud_governance.assessment import assess
from cloud_governance.catalog import RULES
from cloud_governance.collector import ArmTransport, CollectionError, Collector, FixtureTransport, SUBSCRIPTIONS_API, endpoint
from cloud_governance.safety import identity
from tests.helpers import SUB, SUB2, Scenario, resource


class CollectionTests(unittest.TestCase):
    def test_inventory_pagination_and_deduplication(self):
        a = resource("Microsoft.Storage/storageAccounts", "a")
        b = resource("Microsoft.Storage/storageAccounts", "b")
        s = Scenario([a]); s.detail(b)
        next_url = s.inventory_url + "&$skiptoken=second"
        s.responses[s.inventory_url]["nextLink"] = next_url
        s.responses[next_url] = {"value": [a, b]}
        s.run()
        self.assertEqual(2, report_model.resource_summary(s.report)["resource_count"])
        self.assertTrue(report_model.resource_summary(s.report)["inventory_complete"])
        self.assertEqual(2, s.snapshot["inventory"]["subscriptions"][0]["pages"])

    def test_partial_inventory_retains_resources_and_never_aggregate_pass(self):
        a = resource("Microsoft.Storage/storageAccounts", "a")
        s = Scenario([a])
        link = s.inventory_url + "&$skiptoken=secret-cursor"
        s.responses[s.inventory_url]["nextLink"] = link
        s.responses[link] = {"fixture_error": 403}
        s.run()
        self.assertEqual(1, report_model.resource_summary(s.report)["resource_count"])
        self.assertEqual("PASS", s.result(a)["result"])
        self.assertEqual("INCOMPLETE", report_model.resource_summary(s.report)["conclusion"])
        self.assertNotIn("secret-cursor", json.dumps(s.snapshot))

    def test_unsafe_pagination_does_not_send_token_to_other_host(self):
        for link in ("https://evil.example/subscriptions", "http://management.azure.com/subscriptions", "https://management.azure.com@evil.example/subscriptions"):
            s = Scenario([]); s.responses[s.inventory_url]["nextLink"] = link; s.run()
            self.assertNotIn(link, s.transport.calls)
            self.assertFalse(report_model.resource_summary(s.report)["inventory_complete"])

    def test_pagination_cannot_change_subscription_scope(self):
        s = Scenario([])
        link = s.inventory_url.replace(SUB, SUB2)
        s.responses[s.inventory_url]["nextLink"] = link; s.run()
        self.assertNotIn(link, s.transport.calls)
        self.assertEqual("pagination_scope_changed", s.snapshot["errors"][0]["code"])

    def test_pagination_cycle_limit_and_bad_link(self):
        for link, limit, expected in (("cycle", 10, "pagination_cycle"), ("next", 1, "pagination_limit"), (123, 10, "invalid_next_link"), ("", 10, "invalid_next_link")):
            s = Scenario([])
            value = s.inventory_url if link == "cycle" else s.inventory_url + "&p=2" if link == "next" else link
            s.responses[s.inventory_url]["nextLink"] = value
            s.run(max_pages=limit)
            self.assertEqual(expected, s.snapshot["errors"][0]["code"])
            self.assertEqual("INCOMPLETE", report_model.resource_summary(s.report)["conclusion"])

    def test_list_failure_and_empty_scope_do_not_green(self):
        s = Scenario([])
        s.responses[endpoint("/subscriptions", SUBSCRIPTIONS_API)] = {"fixture_error": 403}
        s.run()
        self.assertEqual("INCOMPLETE", report_model.resource_summary(s.report)["conclusion"])
        s = Scenario([]); s.run()
        self.assertEqual("INCOMPLETE", report_model.resource_summary(s.report)["conclusion"])

    def test_denied_detail_is_error_even_for_enforced_service(self):
        row = resource("Microsoft.Storage/storageAccounts")
        s = Scenario([row]); s.responses[endpoint(row["id"], RULES[row["type"].lower()].api)] = {"fixture_error": 403}; s.run()
        self.assertEqual("ERROR", s.result(row)["result"])

    def test_missing_properties_or_mismatched_identity_is_not_pass(self):
        row = resource("Microsoft.Storage/storageAccounts")
        for malformed in ({"id": row["id"], "type": row["type"]}, {**row, "id": row["id"] + "wrong"}, {**row, "properties": []}):
            s = Scenario([row]); s.responses[endpoint(row["id"], RULES[row["type"].lower()].api)] = malformed; s.run()
            self.assertEqual("ERROR", s.result(row)["result"])

    def test_invalid_inventory_not_silently_omitted(self):
        s = Scenario([])
        s.responses[s.inventory_url]["value"] = [None, {"id": "unsafe", "type": "Microsoft.Storage/storageAccounts"}]
        s.run()
        self.assertFalse(report_model.resource_summary(s.report)["inventory_complete"])
        self.assertEqual(2, len(s.snapshot["errors"]))

    def test_unknown_type_retained_without_detail_get(self):
        row = resource("Microsoft.NewService/dataStores")
        s = Scenario([row]); s.run()
        self.assertEqual("UNSUPPORTED", s.result(row)["result"])
        self.assertEqual(2, len(s.transport.calls))

    def test_sql_child_listing_denied_or_partial_cannot_pass_parent(self):
        server = resource("Microsoft.Sql/servers", "server")
        db = resource("Microsoft.Sql/servers/databases", "server/db")
        s = Scenario([server]).children(server, "databases", [db]).tde(db)
        url = endpoint(server["id"] + "/databases", RULES[server["type"].lower()].api)
        s.responses[url]["nextLink"] = url + "&p=2"
        s.responses[url + "&p=2"] = {"fixture_error": 403}
        s.run()
        self.assertEqual("PASS", s.result(db)["result"])
        self.assertEqual("UNKNOWN", s.result(server)["result"])
        self.assertFalse(report_model.resource_summary(s.report)["child_collections_complete"])

    def test_child_list_wrong_parent_is_rejected(self):
        server = resource("Microsoft.Sql/servers", "server")
        db = resource("Microsoft.Sql/servers/databases", "wrong/db")
        s = Scenario([server]).children(server, "databases", [db]).tde(db); s.run()
        self.assertEqual(1, report_model.resource_summary(s.report)["resource_count"])
        self.assertEqual("UNKNOWN", s.result(server)["result"])

    def test_duplicate_child_inventory_is_assessed_once(self):
        server = resource("Microsoft.Sql/servers", "server")
        db = resource("Microsoft.Sql/servers/databases", "server/db")
        s = Scenario([server, db]).children(server, "databases", [db]).tde(db); s.run()
        self.assertEqual(2, report_model.resource_summary(s.report)["resource_count"])
        self.assertEqual("PASS", s.result(server)["result"])

    def test_secret_fields_are_excluded_everywhere(self):
        row = resource("Microsoft.Web/sites", properties={
            "siteConfig": {"appSettings": [{"name": "PASSWORD", "value": "DO-NOT-RETAIN"}]},
            "configuration": {"secrets": [{"name": "key", "value": "DO-NOT-RETAIN"}]},
            "connectionString": "DO-NOT-RETAIN", "administratorLoginPassword": "DO-NOT-RETAIN"})
        row["tags"] = {"secret": "DO-NOT-RETAIN"}
        redis = resource("Microsoft.Cache/Redis", properties={"redisConfiguration": {
            "rdb-backup-enabled": "true", "rdb-storage-connection-string": "AccountKey=DO-NOT-RETAIN"}})
        s = Scenario([row, redis]); s.run()
        self.assertNotIn("DO-NOT-RETAIN", json.dumps(s.snapshot))
        self.assertNotIn("DO-NOT-RETAIN", json.dumps(s.report))
        self.assertFalse(any(word.lower() in url.lower() for word in ("listKeys", "listSecrets", "appsettings") for url in s.transport.calls))

    def test_arm_identity_cannot_lie_about_service_type(self):
        row = resource("Microsoft.NewService/dataStores")
        row["type"] = "Microsoft.Storage/storageAccounts"
        self.assertIsNone(identity(row))

    def test_retries_and_get_only(self):
        class Credential:
            def get_token(self): return "fixture-token"
        class Opener:
            calls = []
            def open(self, request, timeout):
                self.calls.append(request)
                if len(self.calls) == 1:
                    raise HTTPError(request.full_url, 429, "secret-message", {"Retry-After": "0"}, io.BytesIO(b"secret-body"))
                return io.BytesIO(b'{"value": []}')
        opener = Opener(); delays = []
        transport = ArmTransport(Credential(), opener=opener, sleep=delays.append)
        self.assertEqual({"value": []}, transport.get(endpoint("/subscriptions", SUBSCRIPTIONS_API)))
        self.assertEqual([0.0], delays)
        self.assertTrue(all(r.get_method() == "GET" for r in opener.calls))
        with self.assertRaises(CollectionError): transport.get("https://evil.example/")
        self.assertEqual(2, len(opener.calls))

    def test_http_errors_do_not_expose_provider_body(self):
        class Credential:
            def get_token(self): return "fixture-token"
        class Opener:
            def open(self, request, timeout):
                raise HTTPError(request.full_url, 403, "SECRET", {}, io.BytesIO(b"SECRET"))
        with self.assertRaises(CollectionError) as caught:
            ArmTransport(Credential(), opener=Opener()).get(endpoint("/subscriptions", SUBSCRIPTIONS_API))
        self.assertEqual("http_error", str(caught.exception))
        self.assertEqual(403, caught.exception.status)
