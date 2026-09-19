# Prioritized implementation backlog

This is the control-collector backlog, separate from the authorized local evidence archive/PDF pipeline. No broad new collector suite is added by the research. Priorities reflect dependencies and likely risk; owners must align them to the actual RCSA and resource population. Each slice stops when its defined evidence contract, safe collection and offline acceptance tests are complete.

| Priority / slice | Concrete deliverable | Exit evidence |
| --- | --- | --- |
| P0 — Select scope and criteria | Approve service variants, selected baseline/enhancements, owners/common controls, organization parameters, populations, evidence age, assurance period and exceptions. | Signed tailoring/criteria register; no unapproved thresholds used for PASS/FAIL. |
| P0 — Common record contract | Versioned cross-plane identities, safe observed facts separate from conclusions, check/criterion/control/source refs, dates, scope/pagination, evidence state and operating evidence. Preserve current reports/snapshot replay compatibility. | Fixtures prove explicit missing/denied/stale/unsupported and source identity mismatches; consumers use common records. |
| P1 — Inventory and shared ARM | Complete child/dependency discovery, effective role evidence, diagnostics categories/settings, public/TLS/auth configuration and baseline comparison using per-service adapters. | All authorized pages/scopes reconciled; safe projections and exact API version per type; no secret endpoint reads or automatic grants. |
| P1 — Identity plane | Graph application/service-principal/consent/owner/federation population and safe credential metadata; tenant shared policies/audit evidence separately authorized. | Distinct object/app/principal IDs; endpoint-specific consent; requested vs granted rights; Graph absence never inferred from ARM. |
| P1 — Encryption gaps | Add exact modern Redis/database, Event Grid family, Grafana, Prometheus and Automation guarantees/configuration; expand workload dependency closure. | Type/tier/API-specific source verification; unsupported variants remain unknown; no blanket Azure or CMK rule. |
| P2 — Workload and software | Restricted Kubernetes metadata, guest/agent reports, actual VMSS instances/revisions/image digests and scanned software identity. | Fixtures for model/instance drift, stale scan, missing agent, changed digest and unsupported runtime; no secret/env/log payload leakage. |
| P2 — Operational evidence | Aggregate ingestion/retention/health, backup protected-item completeness, recovery records, access-review outcomes, incident/change/remediation samples. | Compare to approved windows and expected populations; configuration alone cannot close operating objectives. |
| P3 — Common/provider/process assessments | Controlled evidence import with document date/period/owner, scope, attestations, assurance exceptions and assessment decision. | Manual/inherited evidence remains traceable and explicitly distinct from automatic configuration results. |
| Local Wiz evidence / native integration pending | Normalized import, inventory/finding comparison and historical replay are implemented; see [Wiz integration](../WIZ_INTEGRATION.md). Native API/export mapping requires the real workplace contract. | Preserve source meaning/time/completeness, exact ARM identity and historical hashes; no automatic control equivalence. |
| Deferred — MCP/query/dashboard | Optional readers can consume saved common records. | Separate scoped implementation; no runtime AI/model dependency in collection, evaluation, storage or reporting. |

## Service-specific next slices

| Service | First concrete collection gap | Required acceptance cases |
| --- | --- | --- |
| Event Hubs | Authorization/network/diagnostic metadata and complete hubs/Capture topology | Denied child page; nondefault SAS rights; external/missing Capture store; tier-dependent audit; replay evidence absent |
| AKS | Restricted Kubernetes adapter plus all pools/nodes/volumes and image identity | Forbidden namespace/PV; secret-bearing pod env projected out; RBAC wildcard; stale node; unencrypted external volume |
| App registrations | Tenant Graph adapter, applications/servicePrincipals and effective consent | Pagination; object/app ID confusion; requested but ungranted permission; stale federation/credential; denied grant read |
| Event Grid | Discriminated family/child discovery before any generic rule | Namespace vs custom/system/partner/MQTT; secret URL; missing destination; unsupported auth feature; no replay evidence |
| Storage Accounts | Each data service, container access metadata and backup/audit boundaries | Blob flag vs container state; Files protocol difference; SAS not enumerable; table/queue recovery gap |
| Cosmos DB | API-family authentication/roles/network and backup policies | NoSQL vs other API capability; Mongo cluster separation; denied native grants; unresolved export |
| Managed Redis | Current root/database/access-policy API and modern SKU rules | Balanced/other modern SKU; child unavailable; non-TLS; persistence vs backup; conflicting unsupported modes |
| Function Apps | Safe site/slot auth/network/TLS and owner dependency manifest | Hosting variation; slot drift; basic publishing; app settings never fetched; missing host store |
| Key Vaults | Safe object lifecycle metadata and control/data privilege model | Secret value endpoint forbidden; expired version; rotation consumer stale; RBAC vs access-policy; purge rights |
| PostgreSQL Flexible Servers | Server parameters plus restricted owner database-role/audit export | Entra enabled with password fallback; TLS client mismatch; pgaudit not producing events; restore absent |
| Azure Container Apps | Environment/revision/job permissions, ingress and deployed digests | Job start authority; literal env secret excluded; old runnable revision; missing mount; no fresh image scan |
| user-assigned managed identities | Attachment/federation and effective permission graph | Shared identity across owners; stale grant; orphan; principal changed on recreation; Graph permission denied |
| private endpoints | Target/groupIds/state and target restriction/DNS references | Approved wrong subresource; public target still open; pending connection; missing network-team test |
| Azure Container Registries | Repo authorization mode, digest inventory and scan/provenance import | Mutable tag; ABAC role mode mismatch; stale scan; admin credentials excluded; missing deleted artifact |
| backup vaults | Both families protected items/instances, policies/jobs/recovery points | Unprotected source; stale failed job; soft delete vs locked immutability; operational snapshot outside vault; restore absent |
| App Configuration | Store auth/network, snapshots and safe reference metadata | Literal secret value excluded; stale client secret reload; replica exposure; deletion/restore dependency |
| Application Insights | Ingestion auth/private paths and workspace/instrumentation linkage | Disabled local auth with unsupported SDK; sampling loss; classic/no workspace; daily cap; sensitive URL removed |
| Managed Grafana | Workspace/config/data-source metadata and safe credential-free exports | Shared identity disclosure; public snapshots; token lifecycle; version-specific feature; secureJsonData absent |
| Managed Prometheus | Microsoft.Monitor/accounts, DCR/DCE/collector and query access graph | Log Analytics confusion; private query/public ingestion; incomplete targets; stale samples; sensitive labels excluded |
| Log Analytics Workspaces | Table plan/retention, query/purge rights, DCR and export completeness | Retention override; unsupported export table; old data not exported; cap/transform loss; query-mode difference |
| Virtual Machines | Guest evidence import, full mounts and patch/EDR health | Managed disk pass with temp gap; stale agent; unpatched package; local admin unknown; backup without app consistency |
| Virtual Machine Scale Sets | Orchestration-aware instance enumeration and model drift | Mixed latestModelApplied; new unmonitored instance; Uniform/Flexible backup difference; rolled-back vulnerable image |
| Automation accounts | Safe account/asset/runbook version/worker metadata | Secret variable/job stream excluded; job-start privilege; old worker/module; no backup plan; webhook URL redacted |

## Common acceptance gates for every adapter/check

Pin exact provider/data-plane API and cloud support; verify minimum permissions and safe returned fields before calling; paginate every selected collection and reconcile expected scope; record missing/deleted/denied/unsupported/version errors; use stable dependency identities; version rules and parameter sets; retain evidence and results separately; add auditor-readable observations/criteria and honest limitations through the generic report path.

Offline tests must cover supported positive/negative predicates, absent/contradictory values, denial, truncation, unsupported variants, stale evidence, dependency mismatch and secret-bearing payload rejection/projection. Operating checks also require dated owner/test evidence with scope and provenance. No live action, credential retrieval, fault injection, restore, scan purchase or enforcement change follows merely from a candidate check.

A future authorized integration test runs against existing work resources with approved identities and a stated cost/permission boundary. Only after scoped verification may a check move from DISCOVERY_ONLY to IMPLEMENTED_UNVERIFIED_LIVE and then an accurately described verified state. Never mark an entire service/control implemented because one property is collected.
