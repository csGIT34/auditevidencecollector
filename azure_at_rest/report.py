"""Readable evidence report with explicit scope, gaps, timestamps and sources."""
import html
import json


def text(value):
    return html.escape(str(value)).replace("|", "&#124;").replace("\n", " ").replace("`", "&#96;")


def markdown(report):
    summary = report["summary"]
    lines = ["# Azure technical evidence assessment", "",
             f"**Encryption conclusion: {summary['conclusion']}**", "",
             f"Evidence mode: **{text(report['mode'])}**. Generated: {text(report['generated_at'])}.",
             f"Collection: {text(report['collection_started_at'])} to {text(report['collection_completed_at'])}.",
             f"Rule version: {report['rule_version']}; tool version: {report['tool_version']}.", "",
             "Provider-managed keys are acceptable. PASS is limited to each resource's stated scope and evidence basis.",
             "This is technical evidence, not RCSA certification or an assertion that every workload is encrypted.", "",
             "## Inventory and coverage", "",
             f"Resources: {summary['resource_count']}. Inventory page traversal complete: {summary['inventory_complete']}. "
             f"Known child traversal complete: {summary['child_collections_complete']}. "
             f"Coverage incomplete: {summary['coverage_incomplete']}. Collection errors: {summary['collection_error_count']}.", "",
             "| Result | Count |", "| --- | ---: |"]
    if "configuration_assessment" in report:
        lines[2:2] = ["**Configuration conclusion: " + report["configuration_assessment"]["summary"]["conclusion"] + "**", ""]
    lines.extend(f"| {status} | {count} |" for status, count in summary["counts"].items())
    lines.extend(["", "| Subscription | Listing complete | Pages | Items received |", "| --- | --- | ---: | ---: |"])
    for sub in report["inventory"]["subscriptions"]:
        lines.append(f"| {text(sub['id'])} | {sub['complete']} | {sub['pages']} | {sub['items_received']} |")
    lines.extend(["", "Subscription discovery: " + text(json.dumps(report["inventory"]["subscription_discovery"], sort_keys=True)), "",
                  "| ARM type | Results |", "| --- | --- |"])
    for resource_type, counts in summary["types"].items():
        lines.append(f"| {text(resource_type)} | {text(', '.join(f'{s}: {n}' for s, n in sorted(counts.items())))} |")
    if summary["unsupported_types"]:
        lines.extend(["", "Unsupported types: " + ", ".join(text(t) for t in summary["unsupported_types"]) + "."])
    lines.extend(["", "## Independent verification", ""])
    for key, value in report["verification_guidance"].items():
        if key != "sources":
            lines.extend([text(value), ""])
    lines.append("[Azure CLI REST and query documentation](" + report["verification_guidance"]["sources"][0] + ").")
    lines.extend(["", "## Resource evidence", ""])
    for row in report["results"]:
        lines.extend([f"### {text(row['result'])} — {text(row['name'])}", "",
                      f"Resource: {text(row['id'])}", "",
                      f"Type: {text(row['type'])}; location: {text(row['location'])}; SKU: {text(row['sku'])}.",
                      f"Observed: {text(row['collected_at'])}; assessed: {text(row['assessed_at'])}.",
                      f"Rule: {row['rule_id']} / {row['rule_version']}; basis: {row['basis']}; API: {text(row['api_version'])}.", "",
                      f"**Reason:** {text(row['reason'])}", "", f"**Scope:** {text(row['scope'])}", "",
                      "Safe configuration evidence:", "", "```json", json.dumps(row["evidence"], indent=2, sort_keys=True), "```", ""])
        for dependency in row["dependencies"]:
            lines.append(f"- Dependency ({text(dependency['relation'])}): {text(dependency['id'])} — {dependency['result']}; resolved: {dependency['resolved']}.")
        for gap in row["gaps"]:
            lines.append(f"- Gap: {text(gap)}")
        for source in row["sources"]:
            lines.append(f"- [Microsoft service documentation]({source['url']}) (reviewed {source['reviewed_on']}).")
        for error in row["errors"]:
            lines.append(f"- Read error: {text(error['operation'])} / {text(error['code'])} / HTTP {text(error['http_status'])}.")
        lines.extend(["", "Read-only verification commands:", ""])
        for note in row["verification_notes"]:
            lines.extend([text(note), ""])
        for command in row["verification_commands"]:
            label = "SYNTHETIC EXAMPLE — DO NOT RUN" if command["synthetic"] else "CURRENT-STATE READ — requires authorized sign-in"
            lines.extend(["**" + label + " / " + text(command["kind"]) + " (" + text(command["relation"]) + ")**", "",
                          text(command["verifies"]), "", "```sh", command["command"], "```", "",
                          "Expected / saved fields: " + text(json.dumps(command["expected_fields"], sort_keys=True)), "",
                          text(command["interpretation"]), ""])
            for source in command["sources"]:
                lines.append("[Supporting service documentation](" + source + ").")
            lines.append("")
    if "configuration_assessment" in report:
        cfg = report["configuration_assessment"]
        lines.extend(["## Configuration control assessments", "", text(cfg["limits"]), "",
                      "Criteria: " + text(json.dumps(cfg["policy"], sort_keys=True)), "",
                      "| Resource | Check / objective | Result | Observation | Criterion | Reason |",
                      "| --- | --- | --- | --- | --- | --- |"] )
        for row in cfg["results"]:
            lines.append("| " + " | ".join(text(v) for v in (row["resource_id"],row["check_id"] + " / " + row["catalog_ref"],row["result"],json.dumps(row["observation"]),json.dumps(row["criterion"]),row["reason"])) + " |")
            if "job_evaluation" in row:lines.append("| " + text(row["resource_id"]) + " | Saved job evaluation | | " + text(json.dumps(row["job_evaluation"])) + " | | |")
        lines.extend(["", "Sources: " + ", ".join("[Microsoft API schema](" + url + ")" for url in sorted({r["source"] for r in cfg["results"]})), ""])
    lines.extend(["## Collection errors", ""])
    if not report["errors"]:
        lines.append("No collection errors recorded. This does not establish exhaustive coverage.")
    for error in report["errors"]:
        lines.append(f"- {text(error['scope'])}: {text(error['operation'])}, {text(error['code'])}, "
                     f"HTTP {text(error['http_status'])}, {text(error['observed_at'])}.")
    lines.extend(["", "## Control mapping and limits", "",
                  report["control_mapping"]["assessment"], "",
                  "[NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) / "
                  "[NIST SP 800-53A Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final). "
                  "Mappings: SC-28 and SC-28(1).", ""])
    lines.extend("- " + text(item) for item in report["limitations"])
    return "\n".join(lines) + "\n"


def exit_code(report):
    configuration = report.get("configuration_assessment", {}).get("summary", {})
    if report["summary"]["counts"]["FAIL"] or configuration.get("counts", {}).get("FAIL", 0):
        return 1
    return 2 if report["summary"]["coverage_incomplete"] or configuration.get("conclusion") == "INCOMPLETE" else 0
