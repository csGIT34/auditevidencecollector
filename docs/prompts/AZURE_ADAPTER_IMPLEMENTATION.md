# Copyable workplace startup prompt

Copy the text below into the workplace LLM session with the transferred repository open. No home conversation is needed. Supply real inputs through approved mechanisms; do not paste credentials.

---

Work in this repository and implement the workplace integration, preserving unrelated changes. Inspect the actual revision/working tree. The home checkpoint is unreleased source built from c316078 / package 0.27.0. Use the revision containing this checkpoint; a clone of the earlier baseline alone lacks the report/Policy/Wiz changes.

The product is **audit evidence collection** across all 20 NIST SP 800-53 Rev. 5 families and 23 service entries. Retain positive and negative observations, unknown/missing evidence, exceptions, criteria, coverage, time/period and provenance. Support full reports and standalone topics such as encryption at rest, plus family/control/resource selections. Finding-free output is not complete evidence; no result means a NIST control is satisfied. No runtime LLM is needed.

Read docs/HOME_LAB_BUILD_STATUS.md and docs/WORKPLACE_AZURE_HANDOFF.md first, then only the contracts/modules needed for the immediate task. Do not re-research every service, reread the historical release log or rebuild working infrastructure. Existing seams:

- policy_query.py / policy_compliance.py: bounded Policy queries, full assignment-ID filtering, continuation, scope validation, conservative timestamp/Manual handling. Current limit: one assignment/subscription and 5,000 retained rows; overflow is incomplete.
- archive.py / storage.py / azure_adapters.py: hash-verified exact-run archives, create-only publication, local/Blob ObjectStore. Never rewrite or reassess originals.
- evidence_report.py: saved-fact full/selected JSON/Markdown/PDF, explicit topic maps, exact Wiz/operating attachments, verified replay. CLI evidence-report/evidence-report-show and FUNCTION-key POST /api/evidence/reports use the existing host; CG_REPORT_ENABLED controls reporting. Old /api/reports remains compatible.
- wiz.py / wiz_observations.py: strict PROJECT-DEFINED v1/v2 normalized contracts and importer. V2 has safe observations, positive/negative rule evaluations and scan targets/coverage. See examples/wiz/observations-export.json. Native Wiz API/GraphQL/auth and field mapping are unimplemented/unverified.
- operational.py: attributed records with periods, saved freshness/requirements and immutable linkage. Guest/Kubernetes have existing separate supplement reports.

In constrained Python 3.12, run python scripts/validate.py and python scripts/demo_audit_evidence.py --output ../audit-rehearsal-work using a new private directory. Report actual results; required skips fail acceptance. Synthetic success proves preservation/mixed outcomes, not live access or all-control effectiveness.

The immediate task is connecting available Wiz evidence to the tested normalized boundary. Inspect real authenticated documentation/schema, approved samples, enabled products/read scopes and installed CLI version. Never invent endpoints, GraphQL types, pagination fields, permissions or native status semantics. Obtain complete inventory and available positive/negative evaluations; Issues alone are insufficient. Preserve source timestamps, scan digests/commits, rule identity and coverage. Resolved/rejected/suppressed issues are not automatic passes. Verify Audit History API/export availability and retention before implementing history. Exclude discovered secrets/snippets.

Implement the native mapper using sanitized real fixtures, with pagination, partial GraphQL error, denial/throttling, unknown-field, identity/scope and chronology tests. Then make an authorized narrowly scoped live read and reconcile source counts/coverage. Reuse importer, reporting and ObjectStore. Preserve v1 imports and old archive bytes.

Policy should ultimately be the primary evaluator; current collection still runs direct reads first. Open engineering: Policy-led collection; evaluated definition/version/parameters/overrides/exemptions/attestations; multiple subscriptions/assignments and partitioning beyond bounds; partial-run preservation after Policy denial; combined guest/Kubernetes rows; broader organizational evidence. Do not describe these as done or merely credential-blocked. Choose a concrete slice with observable acceptance and schema compatibility.

Use existing work infrastructure patterns and docs/WORKPLACE_RUNTIME_CONTRACT.md. Home Terraform is not the work template. Bind actual tenant/scope/UAMI, separate runtime/evidence storage, network/DNS, caller authentication, schedule/budgets, criteria and retention. Build Linux x86_64 Python 3.12 dependencies, exclude the lab probe, run the packaged Functions smoke test and validate actual work RBAC/API/custody/latency before enablement. Honor authorization already supplied by the user; finish local preparation before requesting a genuinely missing approval. Keep secrets out of source/prompts/URLs/logs.

Finish with changed files, exact validation, preservation evidence, what is live versus fixture-tested and remaining blockers. Update checkpoint/handover so the next session does not rediscover the project. Do not claim full NIST completion, WORM retention or native Wiz readiness without corresponding evidence.
