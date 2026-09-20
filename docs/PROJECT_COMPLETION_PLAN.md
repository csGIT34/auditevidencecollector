# Project completion plan

Created 2026-09-19. Project status: **INCOMPLETE**. This is the delivery checklist for the full audit evidence system, not just its encryption collector or hosting pipeline.

## Objective and current baseline

Deliver an Azure-hosted, deterministic evidence collection and assessment system covering applicable controls for all [23 services](PROGRAM_SCOPE.md). Develop and test on macOS/Linux; run unattended in Azure Functions with managed identity and retained evidence in Azure Storage. Reuse workplace infrastructure patterns. Terraform is for the temporary personal lab only.

Existing: scoped encryption-at-rest assessments, Functions/UAMI hosting, local/Blob archives, historical PDF reports, normalized offline Wiz reconciliation, CI and documentation. These are reusable components, not completion of the audit program. Source 0.11.0 has local validation; the last recorded personal deployment is stopped on 0.3.2. See [status](STATUS.md).

## Required deliverables, in execution order

Work in progress: 0.11.0 supplies 169 scoped configuration/identity predicates across the 23 services, including tenant-verified Graph metadata. Separate Kubernetes supplements assess eight per-container predicates through operator imports or an opt-in authenticated Functions collector. The [delivery register](audit/delivery-register.json) records partial support and remaining objective boundaries. Unchecked deliverables remain incomplete; predicate count is not completion.

### 1. Account for every proposed check

- [x] Turn the [215-check research catalog](audit/catalog.json) into a check-level delivery register, preserving its IDs and service/domain/control relationships.
- [ ] For every check, record collection plane, implementation files, criteria, permissions, test evidence, reporting support, live validation state and outstanding dependencies.
- [ ] Distinguish proposed, implemented/offline-tested, live-verified, manual/inherited and explicitly excluded checks. Link exclusion decisions and rationale; do not silently drop difficult checks.
- [ ] Separate engineering coverage from tenant findings. One working property never marks a service or NIST control complete.

Acceptance: every catalog check has a traceable disposition; completion counts derive from evidence, not prose. Manual evidence support does not mean the underlying organizational control is satisfied.

### 2. Extend the shared evidence and criteria model

- [ ] Support multiple checks per resource and ARM, Graph, Kubernetes, guest and imported evidence identities.
- [ ] Version observations, assessment rules, approved criteria, source references, timestamps, scope and evidence completeness independently.
- [ ] Support configurable baselines, freshness windows, approved exceptions and ownership. Missing required criteria produces an explicit unassessed result.
- [ ] Preserve denied, missing, stale, contradictory and unsupported states without implicit PASS or N/A.
- [ ] Keep existing saved runs readable and original archived facts/results unchanged.

Acceptance: synthetic criteria exercise the full local pipeline; absent workplace parameters do not prevent collection or local development and are never invented as approved policy.

### 3. Deliver the first non-encryption slice end to end

- [ ] Storage Accounts: safe account/service/container metadata for public exposure, transport protection, authentication configuration, diagnostics and supported recovery configuration.
- [ ] Function Apps: safe site/slot metadata for exposure, TLS, authentication, publishing authentication, identity and diagnostics, with hosting-specific applicability.
- [ ] Wire every new check through collection, criteria evaluation, archives, JSON/Markdown and self-contained PDFs.
- [ ] Test positive, negative, absent, denied and unsupported variants; document exact boundaries and minimum reads.

Acceptance: an offline run visibly reports multiple non-encryption results for both services; it is not merely an expanded inventory or research table. No app settings, credentials or key values are collected.

### 4. Expand collection across all 23 services

- [ ] Implement shared paginated ARM inventory, children/dependencies, role and diagnostic metadata, with per-service safe projections and exact API versions.
- [ ] Implement Microsoft Graph application/service-principal, owner, consent, federation and credential-metadata collection, keeping distinct object/principal/client identities.
- [ ] Implement the remaining service-specific adapters in the rollout below, including the currently missing encryption variants.
- [ ] Implement restricted Kubernetes metadata and guest/agent evidence ingestion for facts ARM cannot establish.
- [ ] Reconcile populations and dependencies; report unavailable evidence explicitly rather than treating undiscovered objects as absent.

Acceptance: all 23 services have check-level coverage and explicit variant boundaries, backed by local fixtures. Every applicable automatable check has an implemented collection/evaluation path or a visible unresolved delivery item.

### 5. Implement assessment coverage across all 12 domains

- [ ] Identity, authentication, authorization and privileged access.
- [ ] Public exposure, resource restrictions and private connectivity.
- [ ] Encryption and protection at rest, including remaining dependency gaps.
- [ ] Transmission protection.
- [ ] Secrets, certificates and key lifecycle, using safe metadata.
- [ ] Audit generation, retention, protection and collection health.
- [ ] Secure configuration, change approval and drift.
- [ ] Vulnerabilities, patching, versions and software supply chain.
- [ ] Backup, recovery, restore evidence and availability.
- [ ] Inventory, ownership and lifecycle.
- [ ] Detection, incident monitoring and response.
- [ ] Governance, access review, exceptions, privacy and shared controls.

Acceptance: implement the applicable check predicates and evidence paths from the catalog. Configuration findings remain distinct from operating effectiveness; NIST mappings do not imply certification. Domain breadth must be demonstrated per check, not by assigning twelve labels to existing encryption results.

### 6. Complete Wiz integration

- [ ] Add native export mapping and authenticated read-only API transport against a verified Wiz contract, reusing the normalized archive/reconciliation layer.
- [ ] Handle pagination, retries, denied/partial results, observation age, inventory identity and finding lifecycle without losing source meaning.
- [ ] Feed relevant findings into vulnerability/coverage evidence with explicit rule mappings and criteria; do not equate Wiz severity with a NIST conclusion.
- [ ] Test transport and mappings locally with verified sanitized contracts; verify real access at work.

Acceptance: a real Wiz collection or native export maps reproducibly into archived evidence and the report. The current normalized synthetic importer alone does not complete this item. Native schema/access is an external dependency; unrelated local development continues.

### 7. Support operational, manual and inherited evidence

- [x] Import dated backup/restore, access-review, incident, change, remediation and provider/process evidence with owner, scope, period and provenance.
- [ ] Assess required populations, freshness and approved thresholds where evidence supports deterministic evaluation.
- [x] Provide explicit human assessment/attestation records for judgments automation cannot establish.

Acceptance: the report distinguishes observed configuration, operating records and human/provider assertions. Missing restore or review evidence remains a gap even when configuration looks correct.

Implementation: [operational supplements](OPERATIONAL_EVIDENCE.md) archive attributed records, required populations/periods and freshness. Authenticated provider provenance and automatic operating-effectiveness observations remain open.

### 8. Finish audit reporting and historical comparison

- [ ] Produce a generic multi-control report showing selected scope, criteria, observations, conclusions, source provenance and unresolved gaps.
- [ ] Show coverage by service/domain/check and separate automated, manual, inherited and unassessed evidence.
- [x] Compare exact saved runs for newly/no-longer observed resources, changed facts/results and lost evidence; distinguish rule/criteria changes from resource drift. See [saved-run comparison](SAVED_RUN_COMPARISON.md); absence is not proof of deletion.
- [ ] Preserve exact-run replay and tamper detection; visually verify representative large multi-control PDFs and historical compatibility.

Acceptance: an auditor can trace each result to saved facts and criteria without recollecting Azure or relying on chat history.

### 9. Make the expanded system run unattended in Azure

- [ ] Extend host configuration and orchestration for enabled collectors, scope, criteria and schedules.
- [ ] Handle partial failures, throttling, execution limits, overlapping runs and resumable/bounded work where required by measured workloads.
- [ ] Add collection health/freshness visibility and actionable failure reporting; document retention and recovery.
- [ ] Keep runtime independent of a developer machine and runtime AI/model calls.

Acceptance: the packaged expanded application completes scheduled collection/archive/report workflows under Azure limits; failures remain visible and evidence is not silently lost.

### 10. Validate locally and in the bounded personal lab

- [ ] Keep macOS/Linux CI covering all new adapters, predicates, migrations and packaged Functions behavior.
- [ ] Test pagination, denials, stale/conflicting evidence, throttling, secret projection, scale and archive preservation.
- [ ] Use inexpensive representative live resources to verify supported APIs, UAMI permissions and complete reports; use fixtures for expensive/unavailable service variants.
- [ ] Check expected cost before adding resources, remain within the entire personal subscription's under-$25 monthly budget, and stop idle runtime.

Acceptance: publish exact-version validation evidence and list which checks remain offline-only. Do not provision all 23 services merely to claim lab coverage. A budget alert is not a hard spending cap.

### 11. Complete workplace handoff and acceptance

- [ ] Provide a deployment configuration contract, minimum-permission matrix, setup/preflight and acceptance commands, sample configuration and troubleshooting/rollback instructions.
- [ ] Document adapter/check extension, evidence schemas, baseline configuration, Wiz integration and known limitations.
- [ ] Connect workplace tenant, UAMI, storage, networks and approved criteria using existing workplace infrastructure patterns.
- [ ] Verify the real resource population, deployed variants, authorized read access, Wiz mapping, scheduled operation and audit outputs at work.

Acceptance: a fresh clone can be configured without reconstructing this conversation; workplace acceptance records identify the exact build, scope and remaining exceptions.

### 12. Close the temporary lab and project

- [ ] After successful workplace handoff, preserve required evidence and destroy project-owned personal lab resources.
- [ ] Verify deletion and delayed charges; preserve unrelated resources.
- [ ] Reconcile the delivery register against implementation, tests, reports and workplace acceptance. Publish remaining explicit exclusions and their approval.

Acceptance: no required implementation item is silently deferred, the workplace system is operational, and temporary lab cleanup is verified. Organizational judgments/approvals remain with their owners.

## Service rollout

These batches sequence work; none removes a service or applicable domain from scope. Deliver collection, evaluation, archive/report support and tests together in each batch.

| Order | Services | Principal additions |
| --- | --- | --- |
| A | Storage Accounts; Function Apps | First full non-encryption vertical slice, safe exposure/TLS/auth/diagnostic and recovery metadata |
| B | App registrations; user-assigned managed identities; Key Vaults; private endpoints | Graph and ARM identity/privilege, credential lifecycle, target/approval/private-connectivity evidence |
| C | Event Hubs; Event Grid; Cosmos DB; Managed Redis; PostgreSQL Flexible Servers; App Configuration | Family-specific auth/network/protocol/audit/recovery configuration and dependencies |
| D | Application Insights; Managed Grafana; Managed Prometheus; Log Analytics Workspaces | Telemetry identity, ingestion/query configuration, retention and health evidence |
| E | AKS; Azure Container Apps; Azure Container Registries; Virtual Machines; Virtual Machine Scale Sets | Workload identities, deployed images/instances, drift, scan/patch/agent and storage evidence |
| F | backup vaults; Automation accounts | Both vault families, protected populations/jobs/recovery evidence; safe automation identity/runtime/runbook metadata |

Detailed variant and negative-test requirements remain in the [implementation backlog](audit/IMPLEMENTATION_BACKLOG.md) and [service matrix](audit/SERVICE_MATRIX.md).

## Delivery rules

- Implement and prove substantive control coverage before optional infrastructure polish, dashboards or AI/MCP consumers.
- Finish everything possible locally. Keep a short external-dependency list for approved workplace criteria, real variants/access and the Wiz contract; continue independent implementation while those are unavailable.
- Report progress as check IDs implemented/tested/live-verified, with evidence and remaining work. Test counts or hosting success alone are not project completion.
- Do not mark this plan complete because a release is published. Separate local engineering completion, workplace acceptance and lab cleanup.
- Optional dashboards, query databases and AI/MCP readers are outside this completion plan unless separately requested. Existing required evidence, comparison and reporting features are not deferred to them.
