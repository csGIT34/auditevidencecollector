from azure_at_rest.catalog import RULES
from azure_at_rest.collector import Collector, FixtureTransport, INVENTORY_API, SUBSCRIPTIONS_API, endpoint
from azure_at_rest.assessment import assess

SUB = "11111111-1111-1111-1111-111111111111"
SUB2 = "22222222-2222-2222-2222-222222222222"


def resource(kind, name="example", properties=None, sku=None, group="audit-demo"):
    namespace, *parts = kind.split("/")
    names = name.split("/")
    assert len(parts) == len(names)
    path = "/".join(p for pair in zip(parts, names) for p in pair)
    value = {"id": f"/subscriptions/{SUB}/resourceGroups/{group}/providers/{namespace}/{path}",
             "type": kind, "name": names[-1], "location": "eastus", "properties": properties or {}}
    if sku:
        value["sku"] = {"name": sku}
    return value


class Scenario:
    def __init__(self, resources=()):
        self.inventory_url = endpoint(f"/subscriptions/{SUB}/resources", INVENTORY_API)
        self.responses = {endpoint("/subscriptions", SUBSCRIPTIONS_API): {"value": [{"subscriptionId": SUB}]},
                          self.inventory_url: {"value": list(resources)}}
        for row in resources:
            self.detail(row)

    def detail(self, row):
        rule = RULES.get(row["type"].lower())
        if rule and rule.mode != "na":
            self.responses[endpoint(row["id"], rule.api)] = row
            for suffix, _ in rule.children:
                self.responses[endpoint(row["id"] + "/" + suffix, rule.api)] = {"value": []}
        return self

    def tde(self, row, state="Enabled", **kwargs):
        api = RULES[row["type"].lower()].api
        rid = row["id"] + "/transparentDataEncryption/current"
        self.responses[endpoint(rid, api)] = {"id": rid, "properties": {"state": state, **kwargs}}
        return self

    def children(self, parent, suffix, children):
        api = RULES[parent["type"].lower()].api
        self.responses[endpoint(parent["id"] + "/" + suffix, api)] = {"value": children}
        for child in children:
            self.detail(child)
        return self

    def run(self, max_pages=1000):
        self.transport = FixtureTransport(self.responses)
        self.snapshot = Collector(self.transport, max_pages, "offline_fixture").collect()
        self.report = assess(self.snapshot)
        return self.report

    def result(self, row):
        return next(r for r in self.report["results"] if r["id"].lower() == row["id"].lower())
