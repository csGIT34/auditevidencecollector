# Evidence method, candidate criteria and permissions

Every check resolves to its service-specific evidence and candidate acceptance condition **plus** the organization parameters and permission profiles below. Shared references extend service rows; they are not implicit control passes. Routes/property names are collection design inputs, not claims that the current CLI reads them. Data-plane/Graph/Kubernetes APIs and permissions require separate review before use.

## Assessment method

For each check, EXAMINE approved settings, records and scoped provider evidence; INTERVIEW the accountable control/service owner to establish context and exceptions; TEST the selected mechanism and operating process using authorized evidence or a separately approved test plan. The pinned NIST index includes the official objective IDs, method IDs and assessment objects. Check mappings reference the root objective because they support only the stated part of its scope. Assessors must select sub-objectives, depth and coverage, populations/sampling and evidence age before concluding effectiveness. No root-objective reference means every sub-objective was tested.

Static configuration can support design/implementation. Dated samples, event receipt, review outcomes, remediation tickets and test results support operation. A point-in-time observation does not establish an entire audit period. An interview/attestation alone is not independent proof. Avoid universal check rollups or majority-vote control ratings.

Proposed result dimensions: applicability decision; evidence state (available/missing/denied/stale/unsupported/not-collected); configuration result; operating-evidence result; assessment limitations. Preserve the existing CLI status semantics until a versioned extension is designed. A service-level encryption N/A is not audit-wide N/A.

## Organization-defined candidate criteria

These parameters are deliberately unresolved. Proposed predicates in the matrices become executable only after values, approver, effective period, version and exceptions are recorded. SC-28(1) permits provider-managed encryption under the user requirement.

| Domain | Parameters to approve |
| --- | --- |
| I: Identity, authentication, authorization and privileged access | Approved human/workload principals, role scopes, separation of duties, privileged elevation duration, access review frequency, emergency accounts and permitted authentication methods. |
| N: Public exposure, resource restrictions and private connectivity | Approved ingress/egress and service destinations, public exposure exceptions, allowed client networks, private subresources and network-team evidence owner. |
| R: Encryption and protection at rest | Classified information/storage boundaries, required confidentiality/integrity mechanisms and approved cryptography. Provider-managed keys are accepted; CMK is conditional on an explicit separate requirement. |
| T: Transmission protection | Approved protocols and minimum versions, certificate validation/trust and any protocol-specific exceptions; propose TLS 1.2 or stronger where supported, subject to approved architecture. |
| K: Secrets, certificates and key lifecycle | Credential/certificate/key lifetime, rotation and revocation periods, approved issuers/algorithms, expiry warning threshold, custody and recovery requirements. |
| L: Audit generation, retention, protection and collection health | Required event categories/content, retention by dataset, clock accuracy, maximum ingestion lag/missing-event window, capacity threshold, destination protection and review frequency. |
| C: Secure configuration, change approval and drift | Approved baseline/version, change approval and emergency change process, drift interval/tolerance, permitted features, exception approver and expiry. |
| V: Vulnerabilities, patching, versions and software supply chain | Supported version policy, scan scope/frequency/freshness, severity-based remediation deadlines, trusted publishers/digests and compensating-control approval. |
| B: Backup, recovery, restore tests and availability | BIA-derived RPO/RTO, backup frequency/retention/isolation, integrity checks, restore-test interval and success measures, availability/capacity requirements. |
| O: Inventory, ownership and lifecycle | Authoritative tenant/subscription/service inventory, named accountable owners, classification, region/retention rules, lifecycle states and reconciliation frequency. |
| D: Detection, incident monitoring and response | Threat scenarios, detection coverage and test frequency, triage/notification/containment deadlines, responders, evidence preservation and exercise cadence. |
| G: Governance, access review, exceptions, privacy and shared controls | Selected NIST baseline/tailoring and assessment depth/coverage, control owners, evidence age/sampling, legal/privacy basis, supplier assurance, exception and risk acceptance periods. |

## Permission profiles and safe boundaries

Permission profiles are planning constraints, not requests to grant access. Start with separately scoped read roles and endpoint-specific minimum actions; do not grant Contributor/Owner or credential-list actions merely to collect evidence. Cross-subscription/tenant, group expansion, PIM and data-plane access are separately authorized. No cloud or data-plane operations were run.

### ARM: ARM control plane

Read-only provider GET/list actions at approved resource/child scopes; Reader is a starting profile, not a guarantee of every required read. Microsoft.Insights/diagnosticSettings/read and diagnosticSettingsCategories/read for diagnostics. Pin provider/cloud/API versions during adapter design.

Exclude listKeys, listSecrets, publishing profiles, credentials, run commands, deployment outputs and unprojected payloads. GET can still contain sensitive metadata. No network writes.

### AUTH: ARM authorization

Microsoft.Authorization/roleAssignments/read and roleDefinitions/read at resource and ancestor scopes; separately approved reads for deny assignments, eligible/active PIM schedules and group membership resolution.

An assignment list alone is not effective access: include inherited scopes, conditions, deny assignments, group expansion and application-specific data roles. Missing scope is incomplete evidence.

### GRAPH: Microsoft Graph tenant objects

Application.Read.All for /applications and /servicePrincipals and service principal /appRoleAssignments; Directory.Read.All separately for /oauth2PermissionGrants. Owners and federation metadata need endpoint-specific read permission verification.

Separate tenant consent; ARM Reader does not grant Graph. Use object id and appId distinctly. Project credential keyId/type/startDateTime/endDateTime only; never secretText, token or private key. Granting consent is outside this task.

### GAUDIT: Microsoft Graph audit reports

AuditLog.Read.All for approved auditLogs/signIns or directoryAudits evidence; verify delegated directory role, licensing, event-type/API support and retention.

Workload/managed-identity sign-in coverage must be demonstrated, not inferred from a default interactive-sign-in response. Export minimal actor/object/time/outcome metadata; identity logs can contain PII.

### K8S: Kubernetes API

Separately authorized RBAC get/list on named namespaces/resources: workloads, service accounts, roles/bindings, network policies, PVC/PV/StorageClass and node/version metadata as needed.

No cluster-admin or credential retrieval by this catalog. Exclude secrets, exec, attach, pod logs and ConfigMap values. Pods/env/annotations can contain secrets: server-side filtering alone is insufficient; reviewed projections required.

### DATA: Service data-plane metadata

A service-specific metadata-only role/custom action list must be validated per endpoint before implementation. ARM Reader does not imply database, Key Vault, Grafana or registry data access.

Owner-supplied redacted exports are an acceptable initial path. No secret/object/database values, metrics labels, dashboard query contents or credential-bearing URLs by default. Some read-only roles still expose content; do not grant broad roles just to gather metadata.

### LOG: Log/metric aggregate queries

Scoped Azure Monitor/Log Analytics table or resource query permission, or approved Grafana/PromQL query scope; verify relevant table/data actions and mode.

Use aggregate counts, last-observed time, lag and outcome statistics with an approved query. Querying can incur costs and expose data; no queries executed here. No raw event payload collection by default.

### GUEST: Guest/agent and software reports

Read previously produced patch, EDR, machine-configuration and vulnerability reports at approved scopes; guest-local metadata only via a separately approved owner process.

No remote commands, shell login, package changes or new agents. Installed extension existence does not prove healthy scanning or patch completion.

### PROCESS: Process evidence / interview / authorized test records

Control-owner access to approved documents, tickets, approvals, exercises and redacted sampled records.

Separate authorization needed for active restores, failovers, penetration tests and alert simulations. Catalog research performs none. Signed owner statements complement rather than replace independent operating evidence.

### PROVIDER: Provider assurance

Public service documentation plus authorized assurance reports, contractual responsibility matrix and support evidence where needed.

A feature/default statement establishes capability only. Inheritance needs exact service/tier/region, report period, scope, exceptions and customer responsibilities. Customer workload software is not inherited.

### WIZ: Optional Wiz export/API

Future read-only, organization-authorized export with documented inventory, finding and scan scopes; no Wiz connection or credential exists in this tool.

Corroborating evidence only until source timestamps, scan coverage, resource identity and rule meaning reconcile. Wiz finding IDs are not NIST assessment conclusions.

## Provenance and automation requirements

Every future observation needs collection run/time/period, source/plane, tenant and stable object/resource identity, exact route/API/schema/collector version, scope/pagination completeness, allowlisted facts, dependencies and explicit errors. Assessment records separately retain rule/control/criterion version, applied parameters, source evidence IDs, result/reason and gaps. Configuration comparisons, timestamp windows and inventory joins are deterministic; approval, legal basis and operating judgment remain identified human tasks.

Wiz/direct-source reconciliation must compare stable IDs, service variants, observation time, scan/evidence coverage and semantics. Do not substitute a Wiz recommendation, Azure Policy compliance label or provider certification for the underlying selected control evidence. No connection is implemented or authorized.

Sensitive data can exist in metadata: query strings, app settings, pod env/annotations, dashboard JSON, runbooks, log streams and credential-bearing references. Prefer owner-supplied redacted manifests/aggregate reports until safe APIs/projections exist. Never read secrets and redact them only afterwards as an assessment strategy.

Sources: [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final), [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [graph-app](https://learn.microsoft.com/en-us/graph/api/application-list?view=graph-rest-1.0), [graph-grants](https://learn.microsoft.com/en-us/graph/api/oauth2permissiongrant-list?view=graph-rest-1.0), [graph-roles](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-approleassignments?view=graph-rest-1.0), [graph-signins](https://learn.microsoft.com/en-us/graph/api/signin-list?view=graph-rest-1.0)
