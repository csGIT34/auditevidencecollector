# Home-lab build checkpoint

Date: 2026-09-21. Baseline: `c316078`, package version 0.27.0. This is an **unreleased source checkpoint**, not an Azure deployment. The completed feature checkpoint is `519f8cadd666cc3ed4a0f09155bc7e222208e3b3` (2026-09-21). The following commit, `d855930`, only adds Kubernetes interview questions. Transfer a revision containing `519f8ca` and the subsequent handover cleanup; `c316078` alone does not include these changes.

## Requirement and approach

Audit evidence across all 20 NIST SP 800-53 Rev. 5 families and the 23-service program: positive/negative observations, missing coverage and operating periods. Full-program, family, control and topic reports use the same preserved source evidence. Encryption at rest is one topic. Azure Policy supplies provider evaluations; direct collectors, Wiz and attributed records supplement them. Normal operation requires no LLM.

## Implemented here

| Area | Concrete behavior |
| --- | --- |
| Policy correctness | Failures/incompleteness reach aggregate status. Server-side full assignment-ID filtering precedes retention limits. Continuation is followed without an initial total `$top` cap; changed-origin/scope/filter links are rejected. RG boundaries are enforced. Management-group/subscription/RG assignment IDs are accepted. |
| Policy interpretation | Manual states remain UNKNOWN attestation states. Invalid/future/stale timestamps cannot become PASS. Approved criteria supply optional freshness; draft thresholds are ignored. Original provider states remain preserved. |
| Historical compatibility | New summaries carry a version marker; old archives retain saved summaries/bytes. Reports and historical reads do not reassess them with current rules. |
| Selected reports | JSON/Markdown/PDF for full scope, topic, family/control and resources. Positive, negative and unresolved records remain visible. Explicit topic maps are frozen; related unmapped assertions appear as context with a gap. Supporting dependency evidence remains attached. |
| All-family index | Full view: 189 candidate controls across all 20 families plus referenced controls. Missing evidence is NOT_ASSESSED; applicability UNDECLARED. This is not complete assessment of all 1,196 catalog entries. |
| Wiz v2 contract | Safe observations, PASS/FAIL/UNKNOWN/NOT_APPLICABLE/EXEMPT evaluations and scan identity/completion/coverage. Issue lifecycle remains distinct. V1/v2 imports are supported. No native schema/authentication is fabricated. |
| Operating records | Exact supplements retain periods, owners/reviewers, adverse statements, freshness and missing/conflicting requirements. Exceptions do not suppress technical findings. |
| Hosted use | FUNCTION-key POST `/api/evidence/reports`, existing report enablement/budget and Blob adapter. Old endpoint remains compatible. New modules enter source packaging. |
| Rehearsal | `scripts/demo_audit_evidence.py`: ARM/Graph + synthetic Policy/Wiz + operating supplement -> four views -> verified replay; no network. |

The rehearsal uses the existing committed ARM/Graph example, whose configuration rows cover **22 service entries**; the declared program remains 23. Full view: 219 records, comprising 204 PASS, 2 FAIL, 8 UNKNOWN, 2 NOT_APPLICABLE, 1 UNSUPPORTED, 1 OBSERVED and 1 attributed adverse statement. These count records, not satisfied controls.

## Reproduce without cloud access

```sh
python -m pip install -r requirements-dev.txt
python scripts/validate.py
python scripts/demo_audit_evidence.py --output ../audit-rehearsal
```

Use Python 3.12 for deployment builds. The gate requires every test/dependency and rejects skips. Rehearsal output must be a new directory outside the checkout. `result.json` lists exact run/import/report IDs; `encryption.pdf` is synthetic topic evidence. Source hashes are checked after all views are generated/read.

Validation: **427 tests, zero skips on Linux Python 3.12; 47 packaged Functions runtime checks; four-page PDF visually verified; 13 original source objects unchanged; exact Markdown replay matched.** See [current status](STATUS.md) for package digest and boundaries. These checks are local only; no Azure/Wiz calls or cloud changes occurred. Earlier live records apply to earlier releases.

## Open work

**Workplace-dependent:** real Wiz schema/auth/read scopes, native API/export/CLI examples, history availability, source mapping tests and live checks; tenant/UAMI/network/storage/caller binding; organizational criteria, tailoring, periods, retention and operational acceptance.

**Engineering still open:** Policy-led execution (direct reads currently run first); evaluated Policy definition/version/parameter/override/exemption/attestation snapshots; multi-subscription/assignment orchestration and >5,000-row partitioning; partial-run retention after Policy denial; combined guest/Kubernetes rows; broader organizational evidence and objective completion. These are not claimed blocked solely by work credentials. Missing coverage remains explicit.

All 215 objectives remain open/partial. A passing suite does not prove complete NIST coverage; normalized-contract tests do not prove a native Wiz connector.

## Small reading set for the next LLM

1. This checkpoint and [workplace handover](WORKPLACE_AZURE_HANDOFF.md).
2. [Report contract](EVIDENCE_REPORTS.md) and [Wiz contract](WIZ_INTEGRATION.md), only for the immediate task.
3. [Runtime contract](WORKPLACE_RUNTIME_CONTRACT.md), when binding/deploying the host.

Use the [startup prompt](prompts/AZURE_ADAPTER_IMPLEMENTATION.md). Do not reread the historical changelog, all service research files or every old prompt to connect one source. The [baseline Policy review](AZURE_POLICY_REVIEW.md) records why the fixes were needed.
