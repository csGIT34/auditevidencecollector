# Full and selected audit evidence reports

The report is a view of an exact archived run. It includes positive observations, failed criteria, unknowns and missing coverage. It can attach exact normalized Wiz imports and saved operating-evidence reviews. Report generation never recollects Azure, reassesses the saved run or replaces its objects.

The full view indexes the 189 candidate controls across all 20 NIST SP 800-53 Rev. 5 families, plus controls referenced by selected evidence. This is an evidence index, not an applicability decision or proof that all controls were assessed. The pinned catalog contains 1,196 controls and enhancements; a family selector can expose its unassessed catalog entries. Approved control tailoring remains in the separate [control register](CONTROL_REGISTER.md); this new view reports applicability as `UNDECLARED`.

## Rehearse at home

```sh
python scripts/demo_audit_evidence.py --output ../audit-rehearsal
```

Use a new directory outside the checkout. No network, authentication or cloud calls occur. The script collects the existing ARM/Graph fixtures, adds synthetic positive/negative/Manual Policy states, imports positive/negative Wiz evaluations and a scan record, imports an adverse operating statement, and publishes four views. It verifies every original source object's hash afterward.

Outputs: `full.json`, `full.md`, `encryption.pdf`, `encryption.json`, `encryption.md`, family/control views, `topic-profile.json`, `result.json` and the reusable private `archive/`. The selected PDF deliberately retains a positive Wiz evaluation alongside a Policy failure. They have independent criteria; the application neither assumes equivalence nor chooses a winner.

## Local commands

Replace identifiers with the exact values returned by collection/import. `--store` is a local archive root.

```sh
python -m cloud_governance evidence-report --store /private/archive --run-id r-EXACT --pdf
python -m cloud_governance evidence-report --store /private/archive --run-id r-EXACT --topic encryption-at-rest --pdf
python -m cloud_governance evidence-report --store /private/archive --run-id r-EXACT --family AC --family IA --pdf
python -m cloud_governance evidence-report --store /private/archive --run-id r-EXACT --control SC-28 --pdf
python -m cloud_governance evidence-report --store /private/archive --run-id r-EXACT \
  --topic-profile /private/encryption-topic.json --wiz-import-id w-EXACT --operational-id o-EXACT --pdf
python -m cloud_governance evidence-report-show --store /private/archive --report-id e-EXACT
```

`--resource-id` can be repeated and must name resources in the saved ARM/identity inventory. Required saved resource-rule dependencies remain supporting evidence. A run-scoped operating statement is labelled as such; it does not become a resource-level attestation. Control/family choices form a union, then intersect with topic and resource selections. An empty selection is reported as missing evidence, never a pass. `--operational-id` may repeat for distinct reviews or periods.

Successful publication returns exit **0**, including reports containing failures. Invalid inputs and corrupt/unreadable sources return **3**. The older `collect` command retains its documented finding-based exit codes for compatibility; new aggregate summaries now include Policy evidence. Hosted collection already separates archive completion from findings.

## Explicit topic mapping

The built-in encryption topic selects the existing at-rest resource rules and CMK reference checks. It does not guess which tenant-specific Policy or Wiz rule IDs prove encryption at rest. NIST SC-28 alone does not establish that a rule measures that topic or the organization's required key model.

Start from the demo's profile or construct:

```json
{
  "schema_version": "1.0",
  "id": "encryption-at-rest",
  "version": "work-reviewed-1",
  "title": "Encryption at rest",
  "resource_rules": true,
  "checks": ["ST-cmk-key", "ACR-cmk-key", "APPC-cmk-key", "REDIS-cmk-key"],
  "policy_references": [],
  "controls": ["SC-28", "SC-28(1)"],
  "wiz_rules": [],
  "wiz_observations": false,
  "objective_ids": ["ST-R"]
}
```

Populate `policy_references` with reviewed `{"assignment": "FULL_ASSIGNMENT_ID", "reference": "EXACT_REFERENCE_ID"}` entries and `wiz_rules` with verified source rule IDs. `objective_ids` selects attributed operating records using their frozen objective mappings. `wiz_observations: true` explicitly includes all allowed observed facts in the selected population; use it only when that broader fact set is intended. The profile selects evidence; it does not create assessment criteria or approve a mapping.

Unmapped Policy/Wiz evaluations referencing a topic's controls are retained as unclassified context with a gap. An unclassified negative assertion remains visible but is not counted as a mapped topic evaluation. Review that context before using the report.

## Azure Functions

`GenerateEvidenceReport` is a FUNCTION-key-protected POST at `/api/evidence/reports`, using the existing `CG_REPORT_ENABLED` switch, Blob adapter and report budget. It defaults disabled. Existing `/api/reports` keeps its exact-run PDF contract. No new infrastructure or setting is required.

Example request bodies:

```json
{"run_id":"r-EXACT","topic":"encryption-at-rest"}
```

```json
{"run_id":"r-EXACT","families":["AC","IA"],"wiz_import_id":"w-EXACT","operational_ids":["o-EXACT"]}
```

Supported fields are `run_id`, either `topic` or `topic_profile`, `controls`, `families`, `resource_ids`, `wiz_import_id` and `operational_ids`. The request limit is 64 KiB; arrays are bounded. Successful responses return 201 and archive identifiers/PDF key; disabled operation returns 503. Deployment must still supply approved caller authentication and network restrictions. The new endpoint is locally tested, not deployed by this change.

## Evidence custody and limits

Each `evidence-reports/e-.../` publication contains JSON, Markdown, optionally PDF, an intent and a final hash manifest. A failed publication retains a failure marker where storage allows. Reads verify the report and referenced source archives. Existing historical report bytes are never regenerated on read. Hashes and create-only writes do not themselves establish signatures, trusted timestamping or WORM retention.

Wiz scope and synthetic/live mode must match Azure. Recorded tenant mismatches are rejected. Native Wiz authentication is not established by an operator import. Observation timestamps remain source timestamps; the report does not invent an approved cross-source freshness window. Use the existing reconciler with explicitly approved age/skew limits where needed.

Operating statements retain assertion, period, owner/reviewer, reference digest and the original review's freshness/requirement outcomes. They remain attributed evidence and do not suppress findings. Guest and Kubernetes supplements retain their existing dedicated reports; merging those supplement rows into this selectable view is not implemented. Azure Policy currently omits evaluated definition/version snapshots, effective parameters and exemption/attestation documents; reports state that limitation.
