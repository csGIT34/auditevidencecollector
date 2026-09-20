# Program-wide NIST applicability and evidence catalog

**All 23 services are in scope across applicable audit controls.** Version 0.5.0 adds scoped non-encryption predicates; see [configuration assessments](../CONFIGURATION_ASSESSMENTS.md) and the [delivery register](delivery-register.json). This catalog is provisional research for RCSA/control-owner/auditor tailoring, not a compliance certification, approved baseline or tenant finding. No tenant was accessed. The catalog itself is research; executable support is tracked separately in the delivery register.

The matrix separates four questions: **does the control apply; what evidence could support it; can we collect/evaluate it; what did we actually observe?** A proposed check has no finding until approved criteria and sufficient scoped evidence exist. A technical PASS on one signal never establishes the whole NIST control or operating effectiveness over an audit period.

## Start here

- [Service evidence matrix](SERVICE_MATRIX.md): service-specific checks, evidence, candidate criteria, permissions, sources and known gaps.
- [Shared control evidence](SHARED_CHECKS.md): identity/access reviews, logging health, change, vulnerability, recovery, incident response, governance, privacy, people and provider duties.
- [All 20 NIST families](NIST_FAMILY_REVIEW.md): candidate controls, responsibilities and conditional exclusions.
- [Coverage audit](COVERAGE_AUDIT.md): every one of the 23 services × 12 domains, with a check or explicit boundary rationale.
- [Prioritized implementation backlog](IMPLEMENTATION_BACKLOG.md): collection phases, service-specific work and acceptance gates.
- [Evidence method and permission boundary](METHOD.md), [source register](SOURCES.md), [machine-readable catalog](catalog.json), [NIST control/objective index](nist-control-index.json).

Current executable encryption rules and their limits remain in [implementation coverage](../COVERAGE.md) and [authoritative service identity scope](../PROGRAM_SCOPE.md). The tool is still version 0.1.1 at this research snapshot. The [local archive/PDF pipeline](../LOCAL_ARCHIVE_PDF.md) now exists in tool 0.3.0; it does not implement these proposed control checks.

## Research basis and limits

Reviewed on 2026-09-19 against the official NIST OSCAL catalog containing SP 800-53 Rev. 5.2.0 and SP 800-53A Rev. 5.2.0 assessment procedures. The source SHA-256, upstream commit and published metadata are recorded. NIST 800-53 is a control catalog; it is not itself this organization's selected baseline. Baseline, overlays, enhancements, assessment depth/coverage and organization-defined parameters require approval. Each family's policy/procedure control is a shared governance responsibility, not 23 separate Azure configuration tests.

Microsoft service baselines (MCSB v1) are feature/responsibility references; several warn that guidance is outdated. Current service documentation governs feature interpretation. MCSB v2 is preview in the reviewed index. Microsoft/NIST mappings are not one-to-one equivalences and are not imported as proof of NIST satisfaction. NIST mappings here are reasoned candidate mappings, tied to the stated check boundary. Exact provider API versions and safe projections for unimplemented checks remain adapter acceptance work.

Scope is intentionally broader than ARM: Entra applications/service principals, Kubernetes, guest/agent reports, service metadata, provider assurance, process evidence and authorized test records. The [local Wiz evidence adapter](../WIZ_INTEGRATION.md) imports and correlates normalized observations; no native Wiz API access or new control evaluator exists. App registrations are not ARM resources. Managed Redis uses the modern redisEnterprise SKU/database boundary. Managed Prometheus uses Microsoft.Monitor/accounts, not Log Analytics. Event Grid families and both backup vault families stay distinguishable.

## Decisions needed before findings

The RCSA must approve the system/tenant/resource population, classifications, business criticality and each selected control/enhancement; name service/common/provider control owners; resolve deployed Event Grid/Redis/backup/Functions variants; set each parameter in METHOD.md; agree safe evidence permissions and maximum evidence age; approve sampling/depth and inherited assurance; and define exceptions and reassessment. These are future assessment decisions, not blockers to this research catalog.

Provider-managed at-rest keys are accepted. No blanket CMK mandate, uniform retention period, restore frequency or vulnerability SLA is invented. Missing/denied/stale/unsupported/manual evidence is a gap, never an implicit PASS or N/A. Private endpoints remain in resource-local scope; the network team retains VNet/routing/firewall/DNS ownership.

Collection, evaluation, core persistence and reports remain deterministic without runtime AI/model calls. Optional MCP/AI readers, querying databases and dashboards are deferred. No-runtime-AI does not imply free hosting/storage. No resource provisioning, cloud upload, retention locking or live test occurs in this research.

## Maintenance and validation

`catalog.json` is the research source of truth; Markdown matrices are readable views. `nist-control-index.json` retains selected official control statements, assessment objectives/method objects and organization-defined parameter definitions to support reproducible review. It is not a runtime rule catalog. Do not merge it into executable RULES until a scoped adapter/evaluator has passed the backlog gates.

Run `python3 docs/audit/validate_catalog.py` from the repository to check all service/domain/family/control/source references and planned-check status. Change mappings and readable views together. Re-review service documentation/API capability before implementation and when provider features change.

The [predicate execution plan](PREDICATE_EXECUTION_PLAN.md) tracks the remaining service objectives section by section, with the measured position before and after each one.
