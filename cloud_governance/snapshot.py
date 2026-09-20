"""Reject malformed replay snapshots. Snapshots are editable evidence, not attestations."""
from datetime import datetime
import re
from .catalog import RULES
from .safety import ENUMS, INVALID, identity, label, resource_id, subscription_id, valid_api_version, resource_group_name, resource_group_id


def require(condition):
    if not condition:
        raise ValueError("Invalid snapshot")


def timestamp(value):
    require(isinstance(value, str))
    require(datetime.fromisoformat(value).tzinfo is not None)


def listing(value):
    require(isinstance(value, dict) and type(value.get("complete")) is bool)
    require(type(value.get("pages")) is int and value["pages"] >= 0)
    require(type(value.get("items_received")) is int and value["items_received"] >= 0)
    require(not value["complete"] or value["pages"] > 0)


def validate_snapshot(snapshot):
    require(isinstance(snapshot, dict) and snapshot.get("schema_version") in {"1.0","1.1"})
    require(set(snapshot) - {"identity_evidence"} == {"schema_version", "mode", "started_at", "completed_at", "inventory", "resources", "errors"})
    require(snapshot.get("mode") in {"azure_live", "offline_fixture", "azure"})
    timestamp(snapshot.get("started_at"))
    timestamp(snapshot.get("completed_at"))
    require(isinstance(snapshot.get("resources"), list) and isinstance(snapshot.get("errors"), list))
    if snapshot["schema_version"] == "1.0":
        require("identity_evidence" not in snapshot and all("configuration" not in row for row in snapshot["resources"]))
    if "identity_evidence" in snapshot:
        from .graph import validate_identity_evidence
        validate_identity_evidence(snapshot["identity_evidence"])
    inventory = snapshot.get("inventory")
    require(isinstance(inventory, dict) and type(inventory.get("complete")) is bool)
    require(isinstance(inventory.get("subscriptions"), list) and isinstance(inventory.get("subscription_discovery"), dict))
    require(set(inventory) == {"complete", "subscriptions", "subscription_discovery"})
    discovery = inventory["subscription_discovery"]
    require(type(discovery.get("complete")) is bool)
    require(discovery.get("mode") in {"explicit", "accessible_in_current_tenant"})
    require(set(discovery) <= {"complete", "mode", "pages", "items_received"})
    if discovery["mode"] != "explicit":
        listing(discovery)
    seen = set()
    for sub in inventory["subscriptions"]:
        listing(sub)
        require(set(sub) - {"resource_group"} == {"id", "complete", "pages", "items_received"})
        if "resource_group" in sub:
            require(resource_group_name(sub["resource_group"]) is not None)
        require(subscription_id(sub.get("id")) is not None)
    require(len({s["id"].lower() for s in inventory["subscriptions"]}) == len(inventory["subscriptions"]))
    derived_complete = bool(inventory["subscriptions"]) and discovery["complete"] and all(s["complete"] for s in inventory["subscriptions"])
    require(inventory["complete"] == derived_complete)
    for row in snapshot["resources"]:
        ident = identity(row)
        require(ident is not None and row["id"].lower() not in seen)
        require(set(row) <= {"id", "type", "name", "subscription_id", "resource_group", "location", "kind", "sku", "collected_at", "collection_status", "evidence", "children", "errors", "api_version", "request_path", "configuration"})
        if "api_version" in row:
            require(valid_api_version(row["api_version"]))
        if "request_path" in row:
            require(row["request_path"] == row["id"])
        seen.add(row["id"].lower())
        require(all(row.get(k) == v for k, v in ident.items()))
        require(row["subscription_id"] in {s["id"].lower() for s in inventory["subscriptions"]})
        scope = next(s for s in inventory["subscriptions"] if s["id"].lower() == row["subscription_id"])
        require("resource_group" not in scope or row["resource_group"].lower() == scope["resource_group"].lower())
        timestamp(row.get("collected_at"))
        require(row.get("collection_status") in {"ok", "error", "inventory_only"})
        require(all(isinstance(row.get(k), str) and (label(row[k]) == row[k] or row[k] in {INVALID, "[invalid]"}) for k in ("location", "kind", "sku")))
        require(isinstance(row.get("errors"), list) and isinstance(row.get("evidence"), dict) and isinstance(row.get("children"), dict))
        if "configuration" in row:
            from .controls import validate_observations
            validate_observations(row["configuration"], row["type"])
        rule = RULES.get(row["type"].lower())
        paths = set(rule.paths) if rule else set()
        extra = {"provisioningState", "references", "unmanaged_disk_present", "volumes", "agent_pools", "tde.state", "tde.observed_at"}
        require(set(row["evidence"]) <= paths | extra)
        for key, value in row["evidence"].items():
            if key in {"references", "volumes", "agent_pools"}:
                require(isinstance(value, list) and all(isinstance(v, dict) for v in value))
                allowed = {"references": {"relation", "id"}, "volumes": {"name", "storageName", "storageType"},
                           "agent_pools": {"name", "osDiskType", "enableEncryptionAtHost"}}[key]
                require(all(set(v) <= allowed and all(type(x) in (str, bool) for x in v.values()) for v in value))
                if key == "references":
                    require(all(set(v) == allowed and v["relation"] == "managed_disk" and (resource_id(v["id"]) or v["id"] == INVALID) for v in value))
            else:
                if value == INVALID:
                    continue
                if key in ENUMS:
                    require(isinstance(value, str) and value in ENUMS[key])
                elif key.lower().endswith("id"):
                    require(resource_id(value) is not None)
                elif key == "tde.state":
                    require(value in ("Enabled", "Disabled", "[missing-or-unrecognized]"))
                elif key == "tde.observed_at":
                    timestamp(value)
                elif key == "provisioningState":
                    require(isinstance(value, str) and value.lower() in {"succeeded", "failed", "canceled", "cancelled", "creating", "updating", "deleting", "accepted", "running"})
                elif key == "nodeResourceGroup":
                    require(label(value) == value)
                elif key == "defaultDataLakeStorage.accountUrl":
                    require(isinstance(value, str) and re.fullmatch(r"[a-z0-9]{3,24}", value) is not None)
                elif key.startswith("redisConfiguration."):
                    require(value in ("true", "false"))
                elif key == "osDiskSizeGB":
                    require(type(value) is int and 0 <= value <= 65536)
                elif key == "sku.capacity":
                    require(type(value) is int and 0 <= value <= 64)
                else:
                    require(type(value) is bool)
        if rule:
            require(set(row["children"]) <= {c[0] for c in rule.children})
            # Missing mandatory child listings remain UNKNOWN during evaluation.
        for child in row["children"].values():
            listing(child)
            require(set(child) == {"complete", "pages", "items_received", "ids"})
            require(isinstance(child.get("ids"), list) and all(resource_id(i) for i in child["ids"]))
    for error in snapshot["errors"] + [e for r in snapshot["resources"] for e in r["errors"]]:
        require(isinstance(error, dict))
        require(set(error) == {"scope", "operation", "code", "http_status", "observed_at"})
        require(all(isinstance(error[k], str) for k in ("scope", "operation", "code")))
        require(error["code"] in {"invalid_url", "unsafe_url", "redirect_rejected", "authentication_failed", "malformed_response", "response_size_limit", "http_error", "network_error", "retry_exhausted", "fixture_response_missing", "pagination_scope_changed", "pagination_cycle", "pagination_limit", "malformed_page", "invalid_next_link", "invalid_resource_identity", "invalid_detail_identity_or_properties", "invalid_tde_response", "invalid_subscription_identity"})
        operations = {"inventory_identity", "resource_get", "tde_get", "list_resources", "list_subscriptions"} | {"list_" + suffix for rule in RULES.values() for suffix, _ in rule.children}
        require(error["operation"] in operations)
        scope = error["scope"]
        require(scope == "/subscriptions" or resource_group_id(scope) is not None or resource_id(scope) is not None or (scope.startswith("/subscriptions/") and subscription_id(scope[len("/subscriptions/"):]) is not None))
        require(error["http_status"] is None or (type(error["http_status"]) is int and 100 <= error["http_status"] <= 599))
        timestamp(error["observed_at"])
