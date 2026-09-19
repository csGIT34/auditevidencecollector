"""Conservative, scoped technical assessments; not a compliance certification."""
from collections import Counter, defaultdict

from . import __version__
from .catalog import RULES, RULE_VERSION, SOURCE_REVIEWED
from .safety import INVALID, identity, now
from .verification import GUIDANCE, add_verification

STATUSES = ("PASS", "FAIL", "UNKNOWN", "ERROR", "UNSUPPORTED", "NOT_APPLICABLE")
LIMITATIONS = [
    "Inventory covers only the subscription or resource-group scopes recorded in this report, as visible to the collection identity in its authenticated tenant in Azure public cloud. Whole-tenant coverage is not established.",
    "The scoped ARM resource list is not a universal child-resource or data-plane inventory. Only catalogued child collections are enumerated. Deleted, inaccessible, external and unlisted child resources may be absent.",
    "A PASS applies only to the stated resource scope and basis. Documented service enforcement is an inference from verified resource identity and a Microsoft guarantee, not a cryptographic measurement.",
    "Application data flows, Kubernetes runtime volumes, external SaaS, local copies, exports, diagnostics destinations and key lifecycle/availability are not comprehensively discovered.",
    "This is point-in-time technical evidence provisionally mapped to NIST SP 800-53 SC-28 and SC-28(1). Organizational scope, information types, integrity protection, procedures and operating effectiveness require separate RCSA/800-53A assessment.",
]

class Assessor:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.records = {r["id"].lower(): r for r in snapshot["resources"]}
        self.results, self.visiting = {}, set()

    def evaluate(self, record):
        rid = record["id"]
        key = rid.lower()
        if key in self.results:
            return self.results[key]
        if key in self.visiting:
            return {"result": "UNKNOWN", "reason": "Dependency cycle."}
        self.visiting.add(key)
        rule = RULES.get(record["type"].lower())
        result = {k: record[k] for k in ("id", "type", "name", "subscription_id", "resource_group", "location", "kind", "sku", "collected_at")}
        result.update({"assessed_at": now(), "rule_id": rule.key if rule else "unsupported",
                       "rule_version": RULE_VERSION, "controls": ["SC-28", "SC-28(1)"],
                       "scope": rule.scope if rule else "No reviewed rule for this exact ARM resource type.",
                       "basis": "none", "evidence": record.get("evidence", {}),
                       "api_version": record.get("api_version"), "collection_status": record["collection_status"],
                       "sources": [{"url": rule.source, "reviewed_on": SOURCE_REVIEWED}] if rule else [],
                       "dependencies": [], "gaps": [], "errors": record.get("errors", [])})
        evidence = result["evidence"]

        def finish(status, reason, basis="none"):
            result.update(result=status, reason=reason, basis=basis)
            self.results[key] = result
            self.visiting.discard(key)
            return result

        def dep(dep_id, relation):
            target = self.records.get(str(dep_id).lower())
            if target:
                assessment = self.evaluate(target)
                status = assessment["result"]
            else:
                status = "UNKNOWN"
            result["dependencies"].append({"id": dep_id, "relation": relation, "result": status,
                                            "resolved": bool(target)})
            if status not in ("PASS", "NOT_APPLICABLE"):
                result["gaps"].append(f"Dependency {relation} is {status}: {dep_id}")
            return status

        def child_results():
            states = []
            for suffix, _ in rule.children:
                listing = record.get("children", {}).get(suffix)
                if not listing or listing.get("complete") is not True:
                    result["gaps"].append(f"Child collection {suffix} was not completely enumerated.")
                if listing:
                    for child_id in listing["ids"]:
                        states.append(dep(child_id, suffix))
            return states

        if not rule:
            return finish("UNSUPPORTED", "Inventory retained; no service or applicability assumptions made for this type.")
        if record["collection_status"] == "error" or record.get("errors"):
            return finish("ERROR", "A required resource or encryption read failed. No positive conclusion is available.")
        if rule.mode == "na":
            return finish("NOT_APPLICABLE", rule.scope, "justified_applicability")
        if record["collection_status"] != "ok":
            return finish("UNKNOWN", "Verified service-specific resource details are missing.")
        state = evidence.get("provisioningState")
        if state is not None and state.lower() not in ("succeeded", "running"):
            return finish("UNKNOWN", "Resource provisioning is incomplete, unsuccessful or unrecognized.")
        if any(value == INVALID for value in evidence.values()):
            return finish("UNKNOWN", "A relevant returned field has an unexpected value or shape.")

        if rule.mode == "tde":
            if record["name"].lower() == "master" and rule.key == "sql-tde":
                return finish("NOT_APPLICABLE", "SQL master cannot use TDE. User data must not be stored there; that condition is not verified by this tool.", "justified_applicability")
            state = evidence.get("tde.state")
            if state == "Enabled":
                return finish("PASS", "The database TDE endpoint explicitly reports Enabled; provider-managed keys are acceptable.", "api_configuration")
            if state == "Disabled":
                return finish("FAIL", "The database TDE endpoint explicitly reports Disabled.", "api_configuration")
            return finish("UNKNOWN", "TDE state is missing, transitional or unrecognized; database defaults do not establish encryption.", "api_configuration")

        if rule.mode == "database_parent":
            states = child_results()
            if "FAIL" in states:
                return finish("FAIL", "At least one enumerated user database has disabled TDE.", "dependency_assessment")
            if result["gaps"]:
                return finish("UNKNOWN", "User database enumeration or TDE evidence is incomplete.", "dependency_assessment")
            if not states or all(s == "NOT_APPLICABLE" for s in states):
                return finish("NOT_APPLICABLE", "The complete child listing contains no assessable user databases at this observation time.", "justified_applicability")
            return finish("PASS", "All enumerated user databases report TDE Enabled within this parent scope.", "dependency_assessment")

        if rule.mode == "kusto":
            flag = evidence.get("enableDiskEncryption")
            if flag is True:
                return finish("PASS", "VM disk encryption is explicitly enabled; backing-storage encryption is service enforced.", "api_configuration_and_service_guarantee")
            if flag is False:
                return finish("FAIL", "VM cache disk encryption is explicitly disabled; backing-storage encryption alone does not cover it.", "api_configuration")
            return finish("UNKNOWN", "VM cache disk encryption was not returned; backing-storage encryption alone is insufficient.")

        if rule.mode == "servicebus":
            if record["sku"].lower() != "premium":
                return finish("UNKNOWN", "This rule's documented service guarantee is scoped to Premium; no claim is made for a missing or different tier.")
            return finish("PASS", "Verified Premium resource identity is covered by the service-enforced encryption guarantee.", "documented_service_guarantee")

        if rule.mode == "redis_enterprise":
            if not record["sku"].lower().startswith(("enterprise_", "enterpriseflash_")):
                return finish("UNKNOWN", "SKU is missing or outside the reviewed Enterprise / Enterprise Flash guarantee.")
            return finish("PASS", "The documented guarantee covers service disks and persistence with Microsoft-managed keys.", "documented_service_guarantee")

        if rule.mode == "redis":
            result["gaps"].append("Persistence account identifiers are not available safely from this read without inspecting connection strings. Supply separate destination evidence; no secret/listKeys calls are made.")
            return finish("UNKNOWN", "Redis persistence flags do not establish the identity and encryption of every backing destination.", "backing_storage_required")

        if rule.mode == "linked":
            workspace = evidence.get("WorkspaceResourceId")
            if workspace and dep(workspace, "log_analytics_workspace") == "PASS":
                if self.records[workspace.lower()]["type"].lower() == "microsoft.operationalinsights/workspaces":
                    return finish("PASS", "The referenced Log Analytics workspace has positive encryption evidence for telemetry storage.", "dependency_assessment")
            return finish("UNKNOWN", "Workspace-backed telemetry storage could not be verified; classic and external stores require additional evidence.", "backing_storage_required")

        if rule.mode == "eventhub":
            parent_id = rid.rsplit("/", 2)[0]
            parent = self.records.get(parent_id.lower())
            # Avoid a namespace -> hub -> namespace recursion; examine verified parent identity directly.
            if not parent or parent["collection_status"] != "ok" or parent.get("errors"):
                result["gaps"].append("The owning Event Hubs namespace could not be verified.")
            else:
                result["sources"].append({"url": RULES[parent["type"].lower()].source, "reviewed_on": SOURCE_REVIEWED})
            capture = evidence.get("captureDescription.enabled")
            if capture is True:
                target = evidence.get("captureDescription.destination.properties.storageAccountResourceId")
                if not target:
                    result["gaps"].append("Capture is enabled but the destination storage account is unresolved.")
                else:
                    dep(target, "capture_storage")
                    if self.records.get(target.lower(), {}).get("type", "").lower() != "microsoft.storage/storageaccounts":
                        result["gaps"].append("Capture destination is not a verified storage account.")
            elif capture is not False:
                result["gaps"].append("Capture enablement is missing; an external capture destination cannot be ruled out.")
            if result["gaps"]:
                return finish("UNKNOWN", "Retained-message guarantee or Capture destination evidence is incomplete.", "backing_storage_required")
            return finish("PASS", "Namespace retained-message encryption and declared Capture configuration are substantiated.", "dependency_assessment_and_service_guarantee")

        if rule.mode == "workload":
            child_results()
            for ref in evidence.get("references", []):
                dep(ref["id"], ref["relation"])
            for field in ("managedEnvironmentId", "environmentId"):
                if field in evidence:
                    dep(evidence[field], "container_environment")
            if "nodeResourceGroup" in evidence:
                node_group = evidence["nodeResourceGroup"].lower()
                for other in self.records.values():
                    if (other["subscription_id"] == record["subscription_id"] and other["resource_group"].lower() == node_group
                            and other["type"].lower() in {"microsoft.compute/disks", "microsoft.storage/storageaccounts", "microsoft.compute/virtualmachinescalesets"}):
                        dep(other["id"], "node_resource_group_storage")
            if "defaultDataLakeStorage.accountUrl" in evidence:
                account = evidence["defaultDataLakeStorage.accountUrl"]
                matches = [r for r in self.records.values() if r["type"].lower() == "microsoft.storage/storageaccounts" and r["name"] == account]
                if len(matches) == 1:
                    dep(matches[0]["id"], "default_data_lake")
                else:
                    result["gaps"].append("Default data lake account could not be uniquely resolved in inventory.")
            result["gaps"].append(rule.scope)
            if any(d["result"] == "FAIL" for d in result["dependencies"]):
                return finish("FAIL", "A resolved storage dependency failed; remaining workload storage coverage is still incomplete.", "dependency_assessment")
            return finish("UNKNOWN", "ARM metadata does not establish encryption for all workload storage. Review the explicit dependencies and gaps.", "backing_storage_required")

        if rule.mode == "guarantee":
            if rule.key == "storage-sse" and any(v is False for k, v in evidence.items() if k.endswith(".enabled")):
                return finish("UNKNOWN", "A returned encryption flag contradicts the service guarantee; reconcile the evidence before accepting it.")
            if rule.children:
                child_results()
                if result["gaps"]:
                    return finish("UNKNOWN", "Service data encryption is documented, but a required child or destination assessment is incomplete.", "documented_service_guarantee_with_gaps")
            return finish("PASS", "Verified resource identity is covered by Microsoft's service-enforced encryption guarantee. Optional CMK fields are not required evidence of base encryption.", "documented_service_guarantee")
        return finish("UNSUPPORTED", "Rule evaluation mode is not implemented.")


def assess(snapshot):
    assessor = Assessor(snapshot)
    results = [assessor.evaluate(r) for r in snapshot["resources"]]
    resource_groups = {s["id"].lower(): s["resource_group"] for s in snapshot["inventory"]["subscriptions"] if s.get("resource_group")}
    add_verification(results, assessor.records, snapshot["mode"], resource_groups=resource_groups)
    counts = {s: 0 for s in STATUSES}
    counts.update(Counter(r["result"] for r in results))
    types = defaultdict(Counter)
    for result in results:
        types[result["type"]][result["result"]] += 1
    child_complete = all(c.get("complete") is True for r in snapshot["resources"] for c in r.get("children", {}).values())
    incomplete = (not snapshot["inventory"].get("complete") or not child_complete or not results or bool(snapshot["errors"])
                  or any(counts[s] for s in ("UNKNOWN", "ERROR", "UNSUPPORTED")) or any(r["gaps"] for r in results))
    conclusion = "FAILURES_FOUND" if counts["FAIL"] else "INCOMPLETE" if incomplete else "SUPPORTED_SCOPE_SATISFIED"
    return {"schema_version": "1.0", "tool_version": __version__, "rule_version": RULE_VERSION,
            "generated_at": now(), "mode": snapshot["mode"], "collection_started_at": snapshot["started_at"],
            "collection_completed_at": snapshot["completed_at"], "control_mapping": {
                "framework": "NIST SP 800-53 Rev. 5 / SP 800-53A Rev. 5", "controls": ["SC-28", "SC-28(1)"],
                "assessment": "Provisional technical configuration examination and documented service guarantees; not certification or full control effectiveness.",
                "sources": ["https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final", "https://csrc.nist.gov/pubs/sp/800/53/a/r5/final"]},
            "summary": {"conclusion": conclusion, "coverage_incomplete": incomplete, "inventory_complete": snapshot["inventory"].get("complete", False),
                        "child_collections_complete": child_complete, "resource_count": len(results), "counts": counts,
                        "collection_error_count": len(snapshot["errors"]), "types": {t: dict(v) for t, v in sorted(types.items())},
                        "unsupported_types": sorted({r["type"] for r in results if r["result"] == "UNSUPPORTED"})},
            "verification_guidance": GUIDANCE, "inventory": snapshot["inventory"], "limitations": LIMITATIONS, "errors": snapshot["errors"], "results": results}
