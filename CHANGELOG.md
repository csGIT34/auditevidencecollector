# Release notes

## 0.21.0

- Assessment reports move to schema 1.2, where evidence kinds are peers under `evidence` instead of one kind holding the top-level `results` slot while the rest nest beneath it.
- `control_mapping.controls` is derived from the controls the collected evidence actually references, replacing the fixed `SC-28` / `SC-28(1)` pair. A synthetic all-service run now reports 38 referenced controls.
- The top-level `summary` is the cross-kind conclusion; each kind keeps its own summary beside its results.
- Archive format 1.2 pins the assessment schema written into it. Archives written as 1.0 and 1.1 keep loading under their own shape, verified against retained runs from tool versions 0.2.0 and 0.3.0.

## 0.20.0

- Rename the package and distribution from `azure_at_rest` / `azure-at-rest` to `cloud_governance` / `cloud-governance`. Encryption at rest is one rule family, not the identity of the program; the CLI is now `python -m cloud_governance`.
- Rename the `encryption_rule` evidence kind to `resource_rule`: it is a reviewed rule for an exact ARM type, not a topic.
- Rename the control scope declaration from "purview" to "tailoring", NIST's own term, so it no longer collides with the Microsoft Purview product. The CLI flag is `--tailoring`.
- Package `control_index.json` with the distribution; the control register would have failed on an installed wheel without it.

## 0.19.0

- Separate the controls the deployed Azure resource types implicate (48) from organization-wide candidates (189); the tailoring template defaults to the former and every control row records which it is.
- Record NIST SP 800-53 Rev. 5 and NIST SP 800-144 as governing references. SP 800-144 publishes recommendations rather than assessable control identifiers, so it produces no control status.
- Add a control-indexed evidence register: `control-register` inverts saved runs so each NIST SP 800-53 control lists its observations, findings and gaps without re-evaluating anything.
- Add an approved control tailoring with IN_SCOPE, INHERITED and EXCLUDED dispositions, required rationale and approver, and a `--template` starter covering every candidate control. A draft tailoring never excludes or inherits.
- Package control labels, titles and families from the reviewed NIST index, gated like the other packaged research exports.
- No status asserts that a control is satisfied; assessor determination, organization-defined parameters and operating effectiveness stay outside this evidence.

## 0.18.0

- Replace the Enterprise-only cache rule with exact Azure Managed Redis / Redis Enterprise cluster and database rules on API 2025-04-01, covering every reviewed SKU family and the Flash families' transient NVMe disk.
- Assess Azure Cache for Redis from its returned tier, family and size: Basic and Standard C0/C1 fail on Microsoft's documented absence of disk encryption, an enabled rdb/aof flag or missing Premium persistence settings stays incomplete, and no connection string is ever read.
- Enumerate cluster databases as children and add eleven database and cluster predicates for access-key authentication, client protocol, clustering, eviction, deferred upgrade, persistence, replication, diagnostics and declared ARM grants.
- Keep in-memory data, exported copies and geo-replication targets outside every new guarantee. Reject a shared predicate ID collision instead of silently rebinding a check to another resource type.

## 0.17.0

- Add scoped, source-backed encryption rules for Grafana-owned storage, Azure Monitor/Prometheus workspace data and Automation secure assets/runbooks.
- Require successful matching resource reads and stable provisioning; retain explicit external-store, plaintext-variable, job-output and worker exclusions. Unknown child types do not inherit a parent guarantee.
- Freeze rule sources and scope in the existing archive/verification/PDF path; no secret asset reads are added.


## 0.16.1

- Bound live ARM/Graph responses to 8 MiB; retain the 4 MiB vault limit and surface over-limit reads as incomplete/error evidence.
- Reject duplicate JSON members, nonfinite numbers, invalid UTF-8 and excessive nesting before evidence projection. Close failed responses without storing their bodies.


## 0.16.0

- Collect safe Log Analytics table plan/retention metadata and assess required table populations, allowed plans and minimum retention against approved criteria.
- Retain denied/truncated lists, missing/inherited sentinel values, unstable provisioning and inconsistent retention as incomplete. Exclude schemas and search query payloads.
- Regenerate the check-level delivery register with the new adapter/test/criteria links.


## 0.15.1

- Resolve declared VM/VMSS managed disks through verified direct reads inside the selected subscription/resource-group scope, including disks absent from inventory.
- Preserve denied/missing disk reads, inventory completeness and unresolved external references. Deduplicate reads; continue to report broader workload storage as incomplete.


## 0.15.0

- Collect safe Automation runbook publication/type/runtime/logging metadata, classic module versions, and runtime environment/default/imported package versions.
- Add exact population/version baseline assessment and preserve denied, missing-version, duplicate, future-dated and malformed evidence as incomplete.
- Exclude scripts, content links, parameters, asset values, webhook URLs and job streams. No runtime or package support/vulnerability guarantee is inferred from a returned version.


## 0.14.0

- Add an actual-membership predicate for Uniform and Flexible scale sets. Uniform membership reuses the existing instance read; Flexible membership filters VM declarations within the selected subscription/resource-group scope.
- Bring newly discovered Flexible member VMs into normal hydration and assessment, without storing raw guest properties.
- Expand guest evidence populations from saved Flexible membership, preserving missing/partial coverage and stable deduplication of overlapping selections. Live Flexible acceptance remains pending.


## 0.13.0

- Add three opt-in Key Vault data-plane LIST predicates for base key, secret and certificate expiration metadata, using the existing Functions identity and archive pipeline.
- Restrict requests to the ARM-verified vault origin and list paths; discard object contents, tags, key/certificate material and opaque page tokens.
- Add explicit lifecycle criteria, per-object frozen decisions, failure-plus-incomplete coverage, bounded lists, local fixtures and permission documentation. No live vault API validation is implied.


## 0.12.0

- Add typed guest/agent evidence for VM and saved Uniform VMSS instance populations: patch counts/recency, pending reboot, endpoint protection health/recency, vulnerability counts/recency.
- Preserve missing guests, incomplete instance populations, stale/failed source assessments and conflicting sources without implicit PASS.
- Add opt-in Functions import/report endpoints, local CLI, frozen archive replay, sample exports and normalized integration documentation. Vendor-native authentication and mappings remain unverified.


## 0.11.0

- Add opt-in Functions collection of AKS pods/nodes using the configured host identity, a fixed AKS audience, an ARM-verified endpoint and an explicit public CA.
- Restrict collection to configured source-run membership, subscription/resource-group scope and namespace; reject caller-supplied endpoints and admin credential retrieval.
- Preserve partial/denied paging states, enforce list versions and bounded populations, and prevent operator imports from claiming authenticated collection.
- Local validation only; workplace AKS permissions, TLS, network and live response acceptance remain outstanding.


## 0.10.0 — restricted Kubernetes workload evidence

- Project PodList/NodeList exports into exact saved AKS run supplements, excluding raw environment variables, commands, annotations, addresses and secrets.
- Assess eight explicit pod/container security and image-identity predicates with inherited settings, freshness and population completeness. Unknown/Windows OS leaves Linux predicates unassessed.
- Add immutable JSON/Markdown/PDF archives, CLI commands and opt-in key-protected Functions endpoints. Export origin remains operator-supplied; no Kubernetes credentials or live API access are fetched.

## 0.9.1 — container access and operating-evidence coverage

- Assess actual container anonymous-access declarations, including special containers, with explicit approved levels or exact populations. Exclude user metadata and legal-hold identities.
- Keep missing/unfinished job coverage visible alongside known failures; freeze per-source/operation job decisions in JSON, Markdown and PDFs.

## 0.9.0 — backup and restore job evidence

- Read both vault families’ safe job statuses and times. Add explicit source/vault-scoped latest-job recency criteria, including requiring both backup and restore success.
- Preserve failed, missing, unfinished, stale and future evidence; never equate successful job status with restored-data integrity. Historical assessment time and results remain frozen.

## 0.8.2 — Container Apps revision image evidence

- Compare actual revision populations, active flags and declared application/init-container images with approved criteria.
- Reject incomplete/malformed listings and exclude environment variables, commands and secret payloads. Digest resolution, running-container attestation and vulnerability scans remain separate.

## 0.8.1 — scale-set instance drift

- Read and compare actual Uniform VMSS instance identities and latest-model flags with supplied criteria. Preserve denied, malformed and incomplete listings.
- Detect missing expected instances and model drift; explicitly leave Flexible orchestration and guest state unassessed.

## 0.8.0 — operational evidence supplements

- Import attributed, dated restore/access/change/incident/exception records against an exact saved run; preserve automated findings and freeze objective references.
- Publish hash-verified JSON/Markdown archives and standalone PDFs through the CLI and opt-in, key-protected Azure Functions endpoints.
- Reject invalid scope, duplicate fields and incomplete archives; distinguish stale, future and expired evidence. Operator statements and referenced hashes remain unverified assertions.

## 0.7.0 — diagnostic destinations and protected backups

- Compare protected sources, policies and reported states for Data Protection and Recovery Services vaults. Missing expected items and unhealthy states cannot hide behind vault-level configuration.
- Compare each setting’s enabled audit categories together with its actual destination IDs and workspace table mode, reusing the existing API read.
- Malformed destinations, wrong identities, incomplete pages and denied reads cannot pass. Delivery health and retention remain separate.

## 0.6.0 — ARM authorization and delegated consent

- Compare declared resource/inherited ARM assignments and resolved built-in/custom role permissions with supplied approved grant sets.
- Collect and compare Graph delegated consent, including per-user and tenant-wide grants and scope claims.
- Retain explicit partial/denied evidence; preserve historical runs. No identity grants or live resources are created.

## 0.5.1 — saved-run comparison and freshness

- Preserve incomplete coverage when failures also exist; reject missing or falsely complete Graph replay populations.
- Validation: 188 local tests and 22 packaged Functions runtime checks; retained 0.3.1/0.5.0 archive hashes unchanged.
- Optional configured freshness windows prevent stale/future configuration observations from passing; exact historical results remain unchanged.
- Compare exact saved ARM/Graph runs with immutable JSON/Markdown publications, separate criteria/rule changes, lost evidence and explicit population/scope differences.

## 0.5.0 — expanded configuration assessments

- Add 115 scoped predicates spanning all 23 service entries, configurable typed criteria and exact-resource overrides. Wider audit objectives remain incomplete.
- Add opt-in tenant-verified Graph metadata, diagnostic category pagination, UAMI federation and private endpoint target/approval evidence.
- Persist independent configuration results and overall outcomes; include them and frozen NIST objective references in historical PDFs.
- Write schema 1.1 archives/snapshots/assessments, preserve schema 1.0 reads, and require the new reader for new runs. No in-place archive migration.
- Add an all-service synthetic demonstration and a 215-objective delivery register. Native Wiz, deep workload/operating evidence and workplace validation remain open.

## 0.4.0 — 2026-09-19

- Fix credential cleanup being skipped when Blob client cleanup raises. HTTP error handling now uses `ExecutionError.outcome`; status codes and safe JSON response envelopes are unchanged. Python callers must stop parsing exception text as JSON.
- Add normalized Wiz evidence import, exact Azure/Wiz inventory and finding comparison, and hash-verified historical comparison reads. Provide strict v1 contract/reference schema, synthetic fixtures/demo and negative/preservation tests. Native Wiz API/authentication/export mapping remains workplace-specific work; this release does not claim a live Wiz connector.
- Add subprocess-isolated synthetic scale measurements and a CI scale regression. Local 2,000-resource PDF publication: 14.505 seconds, 389.77 MiB peak RSS; real Azure latency/CPU and work data remain unmeasured.
- Add documentation relative-link checks and isolated Terraform mock CI. Consolidate current status, architecture, local workflows and handoff, and correct stale pre-deployment statements.

Snapshot/assessment/archive v1, rule version 2026.09.19.1 and PDF renderer 1.2 remain unchanged. New imports/comparisons use separate create-only namespaces. Historical Azure runs/PDFs are preserved; the original retained 0.3.1 live archive was verified readable without changing any bytes. Local checks: 143 Python tests, four Terraform mocked plans and 22 packaged-runtime checks. Check the exact commit's CI before transfer.

The personal Azure app remains stopped on 0.3.2. This source release was not redeployed to the cloud. Rollback restores the earlier package or disables operations; it must not delete retained archives. An older release does not expose the new Wiz commands, but its Azure run/PDF namespaces are unchanged.

## Earlier validated baseline

The personal v0.3.2 pipeline completed repeated requests, a second collection, and current/historical PDFs after the Flex concurrency mitigation. See [that live validation record](infra/personal-lab/REPEAT_VALIDATION.md). Earlier dated documents preserve their historical observations. [Current status](docs/STATUS.md) identifies the remaining workplace validation boundaries.
