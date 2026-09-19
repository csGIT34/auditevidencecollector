"""Auditor commands are generated as data, never executed by the reporting path."""
import json
import shlex

from .catalog import RULES
from .collector import INVENTORY_API, endpoint
from .safety import identity, resource_id, valid_api_version

GUIDANCE = {
    "prerequisites": "Azure CLI installed; an authorized existing sign-in in the correct tenant and Azure public cloud; metadata read rights on each resource/subscription. Commands use POSIX shell quoting (sh/bash/zsh); JSON argv is available for other launchers.",
    "current_state": "Rerunning retrieves CURRENT state, not historical proof of the saved observation. Compare returned fields with the timestamped evidence; retain the original report separately.",
    "service_guarantees": "Resource identity alone is not cryptographic proof. For mandatory encryption, combine a successful matching identity read with the linked Microsoft guarantee for the exact service, tier and stated scope. Missing optional CMK fields do not establish encryption.",
    "safety": "Commands use management-plane GETs and selected metadata only. They do not provision resources, read application data, fetch secrets/keys, enable diagnostics or activate paid services. No command is executed while generating a report. Do not add --debug or remove the projection; normal ARM responses may contain incidental sensitive fields before CLI projection.",
    "pagination": "List commands display one page and a more_pages indicator. A missing match or empty first page is not proof of absence. If more_pages is true, independently traverse all pages using the current nextLink and verify its ARM origin and unchanged collection path. Saved continuation tokens are not emitted.",
    "synthetic": "offline_fixture commands are SYNTHETIC EXAMPLES — DO NOT RUN. Demo IDs do not identify deployed resources. Only commands in an authorized live report target observed resources, and those may since have changed or been deleted.",
    "sources": ["https://learn.microsoft.com/en-us/cli/azure/reference-index?view=azure-cli-latest#az-rest",
                "https://learn.microsoft.com/en-us/cli/azure/use-azure-cli-successfully-query?view=azure-cli-latest"],
}

MORE_PAGES = "nextLink != `null` && nextLink != ''"


def projection(fields):
    return "{" + ", ".join(json.dumps(key) + ": " + value for key, value in fields.items()) + "}"


def property_expression(path):
    # Paths originate in the reviewed catalog, never in user/ARM-provided values.
    return "properties." + ".".join(json.dumps(part) for part in path.split("."))


def make_command(record, mode, kind, path, api, query, verifies, expected, interpretation, sources=(), paginated=False):
    if not identity(record) or not valid_api_version(api):
        raise ValueError("Invalid verification metadata")
    ident = identity(record)
    allowed_paths = {record["id"], f"/subscriptions/{ident['subscription_id']}/resources"}
    rule = RULES.get(record["type"].lower())
    if rule:
        allowed_paths.update(record["id"] + "/" + suffix for suffix, _ in rule.children)
        if rule.mode == "tde":
            allowed_paths.add(record["id"] + "/transparentDataEncryption/current")
    if path not in allowed_paths:
        raise ValueError("Unexpected verification endpoint")
    url = endpoint(path, api)
    argv = ["az", "rest", "--method", "get", "--url", url, "--query", query,
            "--output", "json", "--only-show-errors"]
    return {"kind": kind, "resource_id": record["id"], "method": "GET", "url": url, "api_version": api,
            "query": query, "argv": argv, "command": shlex.join(argv), "shell": "POSIX",
            "synthetic": mode == "offline_fixture", "verifies": verifies, "expected_fields": expected,
            "interpretation": interpretation, "sources": list(sources), "paginated": paginated,
            "relation": "self"}


def inventory_command(record, mode):
    ident = identity(record)
    if not ident:
        raise ValueError("Invalid verification identity")
    # The identity validator excludes apostrophes, backslashes, backticks and shell expansions.
    query = projection({"matches": "value[?id == '" + record["id"] + "'].{id: id, type: type, location: location}",
                        "more_pages": MORE_PAGES})
    return make_command(record, mode, "inventory_lookup", f"/subscriptions/{ident['subscription_id']}/resources",
                        INVENTORY_API, query, "Locate this resource's identity in subscription inventory.",
                        {"id": record["id"], "type": record["type"]},
                        "Identity only; no service-specific encryption verification is available from this command. "
                        "Follow all pages; an absent match is inconclusive. Unsupported or not-applicable status is not a PASS.",
                        paginated=True)


def direct_commands(record, mode, include_children=True):
    """Use the API version actually recorded, including when replay uses newer rules."""
    if not identity(record):
        raise ValueError("Invalid verification identity")
    rule = RULES.get(record["type"].lower())
    api = record.get("api_version")
    if api is not None and not valid_api_version(api):
        raise ValueError("Invalid verification API version")
    if record.get("request_path", record["id"]) != record["id"]:
        raise ValueError("Unexpected verification request path")
    if not rule or rule.mode == "na" or not api:
        return [inventory_command(record, mode)]
    fields = {"id": "id", "type": "type", "location": "location", "kind": "kind", "sku": "sku.name",
              "provisioningState": "properties.provisioningState"}
    expected = {"id": record["id"], "type": record["type"]}
    for path in rule.paths:
        # The collector derives only an account name from this URL; printing the raw URL could expose SAS data.
        if path == "defaultDataLakeStorage.accountUrl":
            continue
        fields[path] = property_expression(path)
        if path in record["evidence"]:
            expected["properties." + path] = record["evidence"][path]
    if rule.key in {"compute", "disk-sse"}:
        for prefix in ("storageProfile", "virtualMachineProfile.storageProfile"):
            fields[prefix + ".osDiskId"] = "properties." + prefix + ".osDisk.managedDisk.id"
            fields[prefix + ".dataDiskIds"] = "properties." + prefix + ".dataDisks[].managedDisk.id"
    if rule.key == "aks":
        fields["agent_pools"] = "properties.agentPoolProfiles[].{name: name, osDiskType: osDiskType, enableEncryptionAtHost: enableEncryptionAtHost}"
    if rule.key == "container-app":
        fields["volumes"] = "properties.template.volumes[].{name: name, storageName: storageName, storageType: storageType}"
    explanation = "Compare selected fields with the saved observation; missing/contradictory fields or denied reads do not establish a PASS. "
    if rule.mode in {"guarantee", "servicebus", "redis_enterprise"}:
        explanation += "Identity alone is not cryptographic proof; apply the linked mandatory-encryption guarantee only to its exact service/tier/scope. Optional CMK settings are not the base-encryption switch."
        if rule.mode == "servicebus":
            expected["sku.name"] = "Premium (required for this rule's guarantee)"
        elif rule.mode == "redis_enterprise":
            expected["sku.name"] = "Enterprise_* or EnterpriseFlash_* (reviewed SKUs only)"
    elif rule.mode == "kusto":
        explanation += "properties.enableDiskEncryption must be true for the VM cache check; false is a failure, missing is unknown. The linked guarantee covers backing storage separately."
    elif rule.mode in {"tde", "database_parent"}:
        explanation += "Database or server identity does not prove TDE. Use the separate per-database TDE reads; SQL master cannot use this mechanism."
    else:
        explanation += "These are partial component observations. Verify referenced storage separately; workload, runtime and external-storage gaps remain. URL-derived data-lake references are omitted to avoid exposing SAS values."
    commands = [make_command(record, mode, "resource_get", record["id"], api, projection(fields),
                             "Read resource identity and selected encryption/dependency metadata using the collector's recorded API version.",
                             expected, explanation, (rule.source,))]
    if rule.mode == "tde" and not (rule.key == "sql-tde" and record["name"].lower() == "master"):
        state_field = "status" if rule.key == "synapse-tde" else "state"
        path = record["id"] + "/transparentDataEncryption/current"
        commands.append(make_command(record, mode, "tde_get", path, api,
                                     projection({"id": "id", state_field: "properties." + state_field}),
                                     "Read the database's TDE configuration, not the server's key/protector setting.",
                                     {"id": path, "properties." + state_field: record["evidence"].get("tde.state", "not observed")},
                                     "Enabled supports the scoped configuration check; Disabled fails it. Missing, transitional or denied results remain unverified. This is current configuration, not a cryptographic test.",
                                     (rule.source,)))
    if include_children:
        for suffix, _ in rule.children:
            commands.append(make_command(record, mode, "list_" + suffix, record["id"] + "/" + suffix, api,
                                         projection({"resources": "value[].{id: id, type: type}", "more_pages": MORE_PAGES}),
                                         "Enumerate " + suffix + " identities; separate child reads establish configuration.",
                                         {"previously_observed_ids": record.get("children", {}).get(suffix, {}).get("ids", [])},
                                         "Traverse every page. A first page, resource count or identity list cannot prove encryption; run each child's configuration commands. Missing children/read errors keep coverage incomplete.",
                                         (rule.source,), paginated=True))
    return commands


def add_verification(results, records, mode):
    for row in results:
        record = records[row["id"].lower()]
        commands = direct_commands(record, mode)
        notes = ["Saved result: " + row["result"] + ". Commands are independent read suggestions; they do not change the assessment or guarantee a PASS."]
        if mode == "offline_fixture":
            notes.append("SYNTHETIC EXAMPLES — DO NOT RUN. These IDs do not identify deployed resources.")
        dependencies = list(row["dependencies"])
        if row["rule_id"] == "eventhub-capture":
            dependencies.append({"id": row["id"].rsplit("/", 2)[0], "relation": "owning_namespace"})
        for dependency in dependencies:
            target = records.get(str(dependency["id"]).lower())
            if target is None:
                notes.append("No collected service endpoint/API is available for dependency " + str(dependency["id"]) + "; no configuration command is fabricated.")
                continue
            for command in direct_commands(target, mode, include_children=False):
                command["relation"] = dependency["relation"]
                commands.append(command)
        seen = set()
        row["verification_commands"] = []
        for command in commands:
            key = (command["url"], command["query"])
            if key not in seen:
                row["verification_commands"].append(command)
                seen.add(key)
        row["verification_notes"] = notes
