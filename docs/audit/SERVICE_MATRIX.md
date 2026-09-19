# Per-service control and evidence matrix

All rows are **proposed checks**, not tenant findings. Applicability and implementation maturity are separate. Each row includes evidence, proposed acceptance, permissions and sources; full NIST rationale/objective mappings are in [catalog.json](catalog.json), with official statements/methods in [the control index](nist-control-index.json). [METHOD.md](METHOD.md) defines mandatory parameters and safety constraints. Shared references are expanded in [SHARED_CHECKS.md](SHARED_CHECKS.md).

## 01. Event Hubs (EH)

**Resource/evidence boundary:** Microsoft.EventHub/namespaces; eventhubs, authorizationRules, consumerGroups; Capture destinations

**Current executable encryption maturity only:** Supported for scoped namespace/hub storage and resolved Capture dependencies. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Publishers, consumers, retained events and Capture destinations each need owners; event replay is workload-specific.

**Service sources:** [event-hubs-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/event-hubs-security-baseline)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **EH-I** Publisher, receiver and namespace privileges (direct) | AC-3, AC-6, IA-9 | Namespace disableLocalAuth; namespace/hub authorizationRules rights; effective sender/receiver roles and client identity design. | Only approved send/receive/manage scopes; local SAS use requires an approved need; applications do not use namespace root-manage rights. Apply domain I parameters. | ARM, AUTH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EH-N** Namespace ingress and Capture egress boundary (direct) | SC-7, AC-4 | publicNetworkAccess, networkRuleSets defaultAction/IP/VNet rules and trusted-service bypass; private endpoint target/state; Capture target IDs. | Observed paths match the approved boundary and Capture destinations; network team supplies DNS/routing and connectivity validation. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EH-R** Retained events and Capture data (direct) | SC-28, SC-28(1) | Exact namespace/hub identity, SKU and service encryption guarantee; every hub Capture storage dependency and read completeness. | Provider encryption is acceptable within the documented retained-data boundary; all enabled Capture stores independently meet the storage requirement. Apply domain R parameters. | ARM, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EH-T** Publisher, consumer and delivery transport (direct) | SC-8, SC-8(1) | minimumTlsVersion where exposed; AMQP/Kafka/HTTPS client configuration and certificate-validation test records. | Approved encrypted protocols are used on all identified client/destination paths; a namespace TLS setting alone does not prove client validation. Apply domain T parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EH-K** SAS and optional CMK lifecycle (direct) | IA-5, SC-12 | Authorization rule metadata, key-rotation approvals and client rollover tests; optional encryption key IDs/identity and vault lifecycle metadata. | Permitted SAS credentials rotate/revoke per policy; optional CMK remains available and managed. Do not call listKeys to assess lifecycle. Apply domain K parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EH-L** Access, operational and Capture audit (direct) | AU-2, AU-12, AU-5 | Discover available diagnostic categories by tier; enabled categories/destinations; client audit requirements, Capture errors and recent aggregate receipt/lag. | Required security events are collected and collection/Capture failures acted upon; do not assume every tier logs each event payload or data action. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EH-C** Hub retention and consumer configuration drift (direct) | CM-2, CM-6, CM-3 | Namespace/hub/consumer-group settings, partition/retention/Capture changes and approved IaC/change history. | Topology and retention match approved baseline; significant changes have authorization and recovery analysis. Apply domain C parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EH-V** Managed broker versus customer clients (inherited) | SA-9, SI-2, SA-22 | Provider broker assurance and advisories; separate publisher/consumer SDK and connector version/SBOM reports. | Managed broker patching has scoped inheritance evidence; customer clients/connectors remain on supported, remediated versions. Apply domain V parameters. | PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EH-B** Replay, Capture recovery and regional resilience (direct) | CP-9, CP-10, CP-4 | Retention/Capture configuration, tier-specific data-versus-metadata replication design, checkpoint dependencies and replay/failover exercise records. | Workload can recover within RPO/RTO; retention or namespace metadata recovery alone is not an event backup or tested replay. Apply domain B parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: EH-I, ORG-I | Publisher, receiver and namespace privileges |
| N: Public exposure, resource restrictions and private connectivity | direct: EH-N | Namespace ingress and Capture egress boundary |
| R: Encryption and protection at rest | direct: EH-R | Retained events and Capture data |
| T: Transmission protection | direct: EH-T | Publisher, consumer and delivery transport |
| K: Secrets, certificates and key lifecycle | direct: EH-K | SAS and optional CMK lifecycle |
| L: Audit generation, retention, protection and collection health | direct: EH-L, ORG-L | Access, operational and Capture audit |
| C: Secure configuration, change approval and drift | direct: EH-C, ORG-C | Hub retention and consumer configuration drift |
| V: Vulnerabilities, patching, versions and software supply chain | inherited: EH-V, ORG-V | Managed broker versus customer clients |
| B: Backup, recovery, restore tests and availability | direct: EH-B, ORG-B | Replay, Capture recovery and regional resilience |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Publishers, consumers, retained events and Capture destinations each need owners; event replay is workload-specific. |
| D: Detection, incident monitoring and response | shared: ORG-D | Publishers, consumers, retained events and Capture destinations each need owners; event replay is workload-specific. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Publishers, consumers, retained events and Capture destinations each need owners; event replay is workload-specific. |

## 02. AKS (AKS)

**Resource/evidence boundary:** Microsoft.ContainerService/managedClusters and agentPools; Kubernetes workloads, RBAC and volumes; node resources

**Current executable encryption maturity only:** Partial; node/host/storage metadata only, workload storage incomplete. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Control plane, node pools, namespaces, workload identities, container provenance and persistent volumes require distinct owners and evidence.

**Service sources:** [azure-kubernetes-service-aks-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/azure-kubernetes-service-aks-security-baseline), [aks-security](https://learn.microsoft.com/en-us/azure/aks/concepts-security)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **AKS-I** Cluster access and workload identity (direct) | AC-3, AC-6, IA-9 | aadProfile, enableRBAC, disableLocalAccounts, OIDC/workload-identity settings; cluster/namespaced RBAC, service accounts and federation subjects. | Approved cluster and workload principals have minimal scopes; no unapproved admin/local-account paths or wildcard bindings; admission privileges reviewed. Apply domain I parameters. | ARM, AUTH, K8S, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AKS-N** API server and workload network isolation (direct) | SC-7, AC-4 | apiServerAccessProfile private/authorized-IP settings; networkProfile; ingress/services, NetworkPolicies and egress dependency inventory. | API and workload paths meet approved isolation; both policy selection and enforcement are demonstrated; network team supplies shared routing/firewall evidence. Apply domain N parameters. | ARM, K8S, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AKS-R** Secrets, nodes and workload storage (direct) | SC-28, SC-28(1) | Cluster service-encryption guarantee; pool host/OS/disk properties; PV/PVC/CSI storage IDs, ephemeral/hostPath/emptyDir classifications and backing-store results. | Every in-scope stored-data boundary is protected or explicitly excepted; managed disk encryption alone cannot establish all pod storage protection. Apply domain R parameters. | ARM, K8S, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AKS-T** API, ingress and service-to-service encryption (direct) | SC-8, SC-8(1), SC-17 | Ingress TLS references and certificate metadata, service mesh/mTLS policy where selected, control-plane guarantee and approved client/test evidence. | Required ingress and internal paths use approved encryption and certificate validation; ingress TLS does not imply east-west TLS. Apply domain T parameters. | K8S, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AKS-K** Workload secrets and federation lifecycle (direct) | IA-5, SC-12 | Key Vault CSI/reference metadata, identity grants/federated issuer-subject-audience, rotation configuration and application reload tests. | Secret use follows approved custody/rotation with tested renewal/revocation; do not read Kubernetes Secret values or unfiltered pod environment data. Apply domain K parameters. | ARM, K8S, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AKS-L** Control-plane audit and workload log health (direct) | AU-2, AU-12, AU-5 | Selected kube-audit/admin/control-plane categories; workload audit routes, AMA/DCR links, aggregate receipt/lag and audit destination retention. | Selected privileged and workload operations are auditable end to end; agent/diagnostic configuration is corroborated by recent receipt. Apply domain L parameters. | ARM, K8S, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AKS-C** Admission and workload hardening (direct) | CM-2, CM-6, CM-7 | Azure Policy/admission settings, Pod Security admission/enforcement, securityContext/privilege/capabilities, service account token use and namespace baseline exceptions. | Approved workload restrictions are enforced and drift reviewed; optional security features are selected by risk rather than assumed universally required. Apply domain C parameters. | ARM, K8S, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AKS-V** Cluster, node and image vulnerability lifecycle (direct) | RA-5, SI-2, SA-22, SI-7 | Control-plane/pool Kubernetes and OS versions, node image/update channels; image digests/SBOM/scans, node/runtime security health and upgrade records. | All pools and deployed digests have fresh coverage and timely remediation; configured automatic updates alone do not establish actual node/image patch state. Apply domain V parameters. | ARM, K8S, GUEST, PROCESS, WIZ. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AKS-B** Cluster rebuild and stateful recovery (direct) | CP-9, CP-10, CP-4 | Declarative cluster/workload backups, persistent-store recovery points, etcd/provider responsibility, availability zones/PDB/replica design and restore tests. | Recover workload configuration and state within approved limits; multi-zone nodes or pod replicas alone do not back up application data. Apply domain B parameters. | ARM, K8S, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: AKS-I, ORG-I | Cluster access and workload identity |
| N: Public exposure, resource restrictions and private connectivity | direct: AKS-N | API server and workload network isolation |
| R: Encryption and protection at rest | direct: AKS-R | Secrets, nodes and workload storage |
| T: Transmission protection | direct: AKS-T | API, ingress and service-to-service encryption |
| K: Secrets, certificates and key lifecycle | direct: AKS-K | Workload secrets and federation lifecycle |
| L: Audit generation, retention, protection and collection health | direct: AKS-L, ORG-L | Control-plane audit and workload log health |
| C: Secure configuration, change approval and drift | direct: AKS-C, ORG-C | Admission and workload hardening |
| V: Vulnerabilities, patching, versions and software supply chain | direct: AKS-V, ORG-V | Cluster, node and image vulnerability lifecycle |
| B: Backup, recovery, restore tests and availability | direct: AKS-B, ORG-B | Cluster rebuild and stateful recovery |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Control plane, node pools, namespaces, workload identities, container provenance and persistent volumes require distinct owners and evidence. |
| D: Detection, incident monitoring and response | shared: ORG-D | Control plane, node pools, namespaces, workload identities, container provenance and persistent volumes require distinct owners and evidence. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Control plane, node pools, namespaces, workload identities, container provenance and persistent volumes require distinct owners and evidence. |

## 03. App registrations (APPREG)

**Resource/evidence boundary:** Microsoft Graph applications; related servicePrincipals, owners, appRoleAssignments, oauth2PermissionGrants and federatedIdentityCredentials

**Current executable encryption maturity only:** No Graph collection; unassessed. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Application object, enterprise application/service principal and deployed workload are separate; tenant IAM owns consent and human authentication controls.

**Service sources:** [app-registration](https://learn.microsoft.com/en-us/entra/identity-platform/security-best-practices-for-app-registration), [app-operations](https://learn.microsoft.com/en-us/entra/architecture/security-operations-applications), [graph-app](https://learn.microsoft.com/en-us/graph/api/application-list?view=graph-rest-1.0), [graph-grants](https://learn.microsoft.com/en-us/graph/api/oauth2permissiongrant-list?view=graph-rest-1.0), [graph-roles](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-approleassignments?view=graph-rest-1.0), [graph-signins](https://learn.microsoft.com/en-us/graph/api/signin-list?view=graph-rest-1.0)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **APPREG-I** Requested permissions versus effective consent (direct) | AC-2, AC-3, AC-6, IA-9 | application requiredResourceAccess and appRoles; servicePrincipal appRoleAssignments, delegated consent scopes, assignment requirements and owners. | Approved least-privilege grants and tenant audience; requested permissions are not confused with granted consent or runtime authorization. Apply domain I parameters. | GRAPH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPREG-N** Application audience and redirect trust boundary (direct) | AC-4, IA-13 | signInAudience, verified publisher/domain, redirect URIs, identifierUris, logout URLs and app instance property locks where applicable. | URIs/audience are owned, intended and constrained; app registration has no VNet/publicNetworkAccess switch. Actual hosting exposure belongs to the workload. Apply domain N parameters. | GRAPH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPREG-R** Directory metadata and external credential custody (inherited) | SC-28, SA-9 | Entra service assurance for directory metadata; credential custody architecture and deployed workload data inventory. | Provider directory protection is justified within scope; application business data and private-key/secret copies are assessed at their actual stores. Apply domain R parameters. | PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPREG-T** OAuth redirect and token transport security (direct) | SC-8, SC-8(1), IA-13 | Redirect URI schemes, implicit/public-client flow flags and app type; owner evidence for TLS, PKCE and token issuer/audience/signature validation. | Approved protocol flows and exact redirects are enforced; native loopback exceptions are evaluated by client type. Registration metadata cannot prove runtime token validation. Apply domain T parameters. | GRAPH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPREG-K** Application credential and federation hygiene (direct) | IA-5, SC-12, SC-17 | Credential keyId/type/start/end metadata, federated issuer/subject/audiences, usage/expiry reports, approved rotation and revocation records. | No unnecessary public-client credentials or stale secrets; approved federation/certificate preference and lifecycle enforced without retrieving private material. Apply domain K parameters. | GRAPH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPREG-L** Application changes and sign-in monitoring (direct) | AU-2, AU-12, AU-5 | Directory application/owner/credential/consent change events and separately scoped service-principal sign-ins; export/retention and event-type completeness. | Required changes and workload authentication outcomes reach protected monitoring; licensed retention and unsupported event types remain explicit gaps. Apply domain L parameters. | GAUDIT, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPREG-C** Registration and consent change control (direct) | CM-2, CM-3, CM-6 | Approved application manifest projection, permission/audience/URI/owner diffs, change approval and tenant application-management policy evidence. | Sensitive manifest changes have impact review and authorization; configuration templates contain no secret values. Apply domain C parameters. | GRAPH, GAUDIT, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPREG-V** Identity integration and application code security (direct) | SA-11, SI-2, RA-5 | Token-validation and authorization tests, SDK dependency scans and security review of the relying application; provider Entra assurances separately. | Supported identity libraries and negative security tests meet approved criteria; there is no customer patchable OS on the application object. Apply domain V parameters. | PROCESS, GUEST. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPREG-B** Identity configuration recovery and credential replacement (direct) | CP-9, CP-10, CP-4 | Approved manifest/owner/grant configuration records, deletion/recreation/rebinding procedures, credential reissuance and dependency recovery exercise. | Recovery restores approved identity relationships within RTO; never assume object/app IDs or secrets survive deletion/recreation or that credential export is required. Apply domain B parameters. | GRAPH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: APPREG-I, ORG-I | Requested permissions versus effective consent |
| N: Public exposure, resource restrictions and private connectivity | direct: APPREG-N | Application audience and redirect trust boundary |
| R: Encryption and protection at rest | inherited: APPREG-R | Directory metadata and external credential custody |
| T: Transmission protection | direct: APPREG-T | OAuth redirect and token transport security |
| K: Secrets, certificates and key lifecycle | direct: APPREG-K | Application credential and federation hygiene |
| L: Audit generation, retention, protection and collection health | direct: APPREG-L, ORG-L | Application changes and sign-in monitoring |
| C: Secure configuration, change approval and drift | direct: APPREG-C, ORG-C | Registration and consent change control |
| V: Vulnerabilities, patching, versions and software supply chain | direct: APPREG-V, ORG-V | Identity integration and application code security |
| B: Backup, recovery, restore tests and availability | direct: APPREG-B, ORG-B | Identity configuration recovery and credential replacement |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Application object, enterprise application/service principal and deployed workload are separate; tenant IAM owns consent and human authentication controls. |
| D: Detection, incident monitoring and response | shared: ORG-D | Application object, enterprise application/service principal and deployed workload are separate; tenant IAM owns consent and human authentication controls. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Application object, enterprise application/service principal and deployed workload are separate; tenant IAM owns consent and human authentication controls. |

## 04. Event Grid (EG)

**Resource/evidence boundary:** Microsoft.EventGrid topic/domain/system/partner/namespace families; subscriptions, namespace topics and MQTT client/topic-space permissions

**Current executable encryption maturity only:** Unsupported; family and child discovery absent. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Publishing, delivery and MQTT broker permissions differ; retain subtype, dead-letter store and destination ownership instead of applying one generic namespace rule.

**Service sources:** [event-grid-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/event-grid-security-baseline), [eventgrid-security](https://learn.microsoft.com/en-us/azure/event-grid/security-authentication), [eventgrid-mqtt](https://learn.microsoft.com/en-us/azure/event-grid/mqtt-client-authentication), [eventgrid-overview](https://learn.microsoft.com/en-us/azure/event-grid/overview)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **EG-I** Publish, subscribe and delivery authorization (direct) | AC-3, AC-6, IA-9 | Subtype-specific local-auth controls/roles; event delivery identity, MQTT clients/topic-space permission bindings and Entra authentication configuration. | Only intended senders/receivers/topics/destinations are authorized; current namespace/MQTT capabilities override outdated baseline feature notes. Apply domain I parameters. | ARM, AUTH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EG-N** Ingress restrictions and delivery destination trust (direct) | SC-7, AC-4 | Subtype publicNetworkAccess/IP/private endpoint settings and topic/subscription destination resource identities; MQTT routing and approved outbound targets. | Supported exposure controls match approved paths; system/partner subscriptions and HTTP/MQTT families have separately evaluated boundaries. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EG-R** Retained events and dead-letter storage (direct) | SC-28, SC-28(1) | Exact event family/tier/retention boundary, applicable provider encryption statement and every dead-letter/delivery-store dependency. | No blanket at-rest pass from Event Hubs or generic Azure guidance; unresolved family-specific retained data or destination evidence remains unknown. Apply domain R parameters. | ARM, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EG-T** Event delivery and MQTT transport (direct) | SC-8, SC-8(1), SC-17 | HTTPS delivery endpoint scheme/identity with query credentials removed; TLS policies and MQTT certificate trust metadata; client validation tests. | Encrypted approved protocols and valid destination/client trust on each supported path; redact webhook URLs that contain secrets. Apply domain T parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EG-K** Publisher keys, webhook credentials and MQTT certificates (direct) | IA-5, SC-12, SC-17 | Key usage/rotation records, delivery identity, MQTT CA/thumbprint/expiry metadata and revocation/replacement procedures. | Static credentials are justified, scoped and rotated; certificate renewal/revocation tested; never request publisher keys or credential-bearing destination URLs. Apply domain K parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EG-L** Publish/delivery/MQTT failure observability (direct) | AU-2, AU-12, AU-5 | Available diagnostic categories per family, delivery failures/dead-lettering and authentication aggregates, route/destination and receipt health. | Required publishing, access and delivery events are observable for the deployed subtype; metrics are not automatically per-event audit. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EG-C** Subscription filters and MQTT routing baseline (direct) | CM-2, CM-3, CM-6, SI-10 | Event type/subject filters, retry/TTL/dead-letter settings, MQTT topic-space bindings and routing changes; consumer input-validation test records. | Approved routing/filter rules prevent unintended disclosure; consumers validate untrusted event content and changes are controlled. Apply domain C parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EG-V** Provider broker and customer event handlers (inherited) | SA-9, SI-2, SA-11 | Managed broker assurance; separate webhook/consumer runtime, dependencies, scanners and secure-development tests. | Provider patch scope is evidenced; customer handlers and MQTT clients remain subject to vulnerability and application-security evidence. Apply domain V parameters. | PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **EG-B** Delivery recovery and replay strategy (direct) | CP-9, CP-10, CP-4 | Subtype retry/retention/dead-letter settings; protected source replay store, consumer idempotency and outage/replay test results. | Documented loss/duplicate/replay behavior meets RPO/RTO; Event Grid retry retention is not a general-purpose backup. Apply domain B parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: EG-I, ORG-I | Publish, subscribe and delivery authorization |
| N: Public exposure, resource restrictions and private connectivity | direct: EG-N | Ingress restrictions and delivery destination trust |
| R: Encryption and protection at rest | direct: EG-R | Retained events and dead-letter storage |
| T: Transmission protection | direct: EG-T | Event delivery and MQTT transport |
| K: Secrets, certificates and key lifecycle | direct: EG-K | Publisher keys, webhook credentials and MQTT certificates |
| L: Audit generation, retention, protection and collection health | direct: EG-L, ORG-L | Publish/delivery/MQTT failure observability |
| C: Secure configuration, change approval and drift | direct: EG-C, ORG-C | Subscription filters and MQTT routing baseline |
| V: Vulnerabilities, patching, versions and software supply chain | inherited: EG-V, ORG-V | Provider broker and customer event handlers |
| B: Backup, recovery, restore tests and availability | direct: EG-B, ORG-B | Delivery recovery and replay strategy |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Publishing, delivery and MQTT broker permissions differ; retain subtype, dead-letter store and destination ownership instead of applying one generic namespace rule. |
| D: Detection, incident monitoring and response | shared: ORG-D | Publishing, delivery and MQTT broker permissions differ; retain subtype, dead-letter store and destination ownership instead of applying one generic namespace rule. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Publishing, delivery and MQTT broker permissions differ; retain subtype, dead-letter store and destination ownership instead of applying one generic namespace rule. |

## 05. Storage Accounts (ST)

**Resource/evidence boundary:** Microsoft.Storage/storageAccounts; blob/file/queue/table services, containers/shares and copies

**Current executable encryption maturity only:** Supported scoped service encryption; no object data collection. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Each storage service, anonymous-access path, SAS design, retention dataset and export/replica requires classification and ownership.

**Service sources:** [storage-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/storage-security-baseline), [storage-security](https://learn.microsoft.com/en-us/azure/storage/blobs/security-recommendations)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **ST-I** Data authorization, shared keys and anonymous access (direct) | AC-3, AC-6, IA-5 | allowSharedKeyAccess, allowBlobPublicAccess, defaultToOAuthAuthentication; container publicAccess, data role/ACL metadata and SAS governance. | Approved principals and service-specific authorization only; default OAuth preference is not enforcement. Account flags, container policy and issued SAS limitations are assessed separately. Apply domain I parameters. | ARM, AUTH, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ST-N** Firewall, bypass and private subresource coverage (direct) | SC-7, AC-4 | publicNetworkAccess, networkAcls defaultAction/bypass/IP/VNet rules and private endpoint groupIds for blob/file/queue/table/dfs as used. | All used data endpoints meet approved restrictions; a blob private endpoint alone does not isolate file/queue/table or disable public access. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ST-R** Storage service encryption and copies (direct) | SC-28, SC-28(1) | Service identity/kind, encryption configuration/scope and documented platform guarantee; external copies/exports classified separately. | Provider-managed encryption accepted across documented stored data; infrastructure encryption/CMK only required when separately selected. Apply domain R parameters. | ARM, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ST-T** Secure transfer and service-specific protocols (direct) | SC-8, SC-8(1) | supportsHttpsTrafficOnly, minimumTlsVersion; Azure Files SMB/NFS protocol/encryption settings and client mounts. | Each used HTTP/file protocol satisfies approved confidentiality/integrity; HTTPS-only does not establish every SMB/NFS client path. Apply domain T parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ST-K** Account/SAS and optional encryption-key lifecycle (direct) | IA-5, SC-12 | Key creation/rotation metadata if exposed; SAS policy, issuance/revocation records, user-delegation design and optional vault references. | Static keys and signed URLs are minimized, scoped and expired/revoked per policy; issued account-key SAS inventory is not fully observable from account GET. Apply domain K parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ST-L** Per-service read/write/delete audit and retention (direct) | AU-2, AU-12, AU-5, AU-9 | Diagnostic categories/settings on each used storage service; destination retention/immutability, event aggregates and denied-access alerts. | Required service data events are received and protected; account-level Activity Log alone does not audit object access. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ST-C** Service settings, immutability and deletion safeguards (direct) | CM-2, CM-3, CM-6 | Blob/file service settings, versioning, soft delete, lifecycle/immutability/legal holds and approved changes/locks. | Required safeguards match data classification and retention obligations; immutable retention is never invented or enabled by the collector. Apply domain C parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ST-V** Managed storage platform and customer transfer tools (inherited) | SA-9, SI-2, SA-22 | Storage assurance/advisories plus client SDK, AzCopy/agent and mounted host version/scan evidence. | Provider service patching is inherited within scope; customer tools and hosts have supported/remediated components. Apply domain V parameters. | PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ST-B** Dataset-specific protection and tested recovery (direct) | CP-9, CP-9(1), CP-10, CP-4 | Redundancy/replication, blob/file backup/version/deletion protection, queue/table recovery design, recovery points and sampled restore results. | Required datasets recover within RPO/RTO; replication and soft delete alone are not independent backup or proof that all storage services are recoverable. Apply domain B parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: ST-I, ORG-I | Data authorization, shared keys and anonymous access |
| N: Public exposure, resource restrictions and private connectivity | direct: ST-N | Firewall, bypass and private subresource coverage |
| R: Encryption and protection at rest | direct: ST-R | Storage service encryption and copies |
| T: Transmission protection | direct: ST-T | Secure transfer and service-specific protocols |
| K: Secrets, certificates and key lifecycle | direct: ST-K | Account/SAS and optional encryption-key lifecycle |
| L: Audit generation, retention, protection and collection health | direct: ST-L, ORG-L | Per-service read/write/delete audit and retention |
| C: Secure configuration, change approval and drift | direct: ST-C, ORG-C | Service settings, immutability and deletion safeguards |
| V: Vulnerabilities, patching, versions and software supply chain | inherited: ST-V, ORG-V | Managed storage platform and customer transfer tools |
| B: Backup, recovery, restore tests and availability | direct: ST-B, ORG-B | Dataset-specific protection and tested recovery |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Each storage service, anonymous-access path, SAS design, retention dataset and export/replica requires classification and ownership. |
| D: Detection, incident monitoring and response | shared: ORG-D | Each storage service, anonymous-access path, SAS design, retention dataset and export/replica requires classification and ownership. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Each storage service, anonymous-access path, SAS design, retention dataset and export/replica requires classification and ownership. |

## 06. Cosmos DB (COS)

**Resource/evidence boundary:** Microsoft.DocumentDB/databaseAccounts and API-specific children; mongoClusters separate variant

**Current executable encryption maturity only:** Supported account/cluster encryption as separate exact types. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** API family governs identity/audit/backup capabilities; account-based Cosmos and separately branded Mongo clusters need independent feature matrices.

**Service sources:** [azure-cosmos-db-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/azure-cosmos-db-security-baseline), [cosmos-security](https://learn.microsoft.com/en-us/azure/cosmos-db/security)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **COS-I** API-specific data roles and local authentication (direct) | AC-3, AC-6, IA-9 | API kind/capabilities, disableLocalAuth where supported, SQL role definitions/assignments or other API-native roles; client identities. | Approved least privilege enforced for actual API; a NoSQL Entra option is not presumed available on every Mongo/Cassandra/Table/Gremlin variant. Apply domain I parameters. | ARM, AUTH, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **COS-N** Public access, firewall and regional endpoints (direct) | SC-7, AC-4 | publicNetworkAccess, ipRules, virtualNetworkRules, private endpoint connections/group IDs and network ACL bypass/resource IDs. | All selected API and regional endpoints meet approved restrictions; trusted-service and broad Azure-address exceptions are justified. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **COS-R** Managed data and backup encryption (direct) | SC-28, SC-28(1) | Exact account/cluster identity and documented encryption scope; optional keyVaultKeyUri and backup/export dependencies. | Provider encryption accepted for the documented type; external exports and application caches require their own evidence. Apply domain R parameters. | ARM, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **COS-T** API transport and client trust (direct) | SC-8, SC-8(1) | Service TLS guarantee/settings by API; connection scheme, driver TLS/certificate validation and negative connection-test evidence. | Every selected client/API path enforces approved encrypted transport and certificate validation. Apply domain T parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **COS-K** Keys, resource tokens and optional CMK (direct) | IA-5, SC-12 | Credential mode, resource-token issuance/TTL policy, key rotation/revocation records and optional vault metadata. | Non-Entra credentials have justified scopes/lifetimes and rotation; no account keys or connection strings collected. Apply domain K parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **COS-L** API-specific request audit and ingestion health (direct) | AU-2, AU-12, AU-5 | Available request/control-plane diagnostic categories by API, destination settings, request outcome aggregates and retention. | Required accesses/changes are auditable without capturing document/query contents; category availability and sampling limitations recorded. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **COS-C** Consistency, regions and data-plane change controls (direct) | CM-2, CM-3, CM-6 | Consistency, regions/write settings, API capabilities, backup policy and schema/index/throughput change approvals. | Account and API configuration match approved application/data requirements with reviewed security/availability impact. Apply domain C parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **COS-V** Managed engines and application drivers (inherited) | SA-9, SI-2, SA-22 | Provider engine support/assurance; API version/driver inventories, dependency scans and unsupported-feature notices. | Managed engine responsibilities evidenced; customer drivers and queries/application code remain assessed. Apply domain V parameters. | PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **COS-B** Backup mode, retention and regional restore (direct) | CP-9, CP-10, CP-4 | Periodic/continuous backup policy, retention/locations, restore/recovery records, region failover design and application validation. | Selected API backup and restore capabilities meet RPO/RTO; multi-region writes or replication alone do not establish backup integrity/recovery. Apply domain B parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: COS-I, ORG-I | API-specific data roles and local authentication |
| N: Public exposure, resource restrictions and private connectivity | direct: COS-N | Public access, firewall and regional endpoints |
| R: Encryption and protection at rest | direct: COS-R | Managed data and backup encryption |
| T: Transmission protection | direct: COS-T | API transport and client trust |
| K: Secrets, certificates and key lifecycle | direct: COS-K | Keys, resource tokens and optional CMK |
| L: Audit generation, retention, protection and collection health | direct: COS-L, ORG-L | API-specific request audit and ingestion health |
| C: Secure configuration, change approval and drift | direct: COS-C, ORG-C | Consistency, regions and data-plane change controls |
| V: Vulnerabilities, patching, versions and software supply chain | inherited: COS-V, ORG-V | Managed engines and application drivers |
| B: Backup, recovery, restore tests and availability | direct: COS-B, ORG-B | Backup mode, retention and regional restore |
| O: Inventory, ownership and lifecycle | shared: ORG-O | API family governs identity/audit/backup capabilities; account-based Cosmos and separately branded Mongo clusters need independent feature matrices. |
| D: Detection, incident monitoring and response | shared: ORG-D | API family governs identity/audit/backup capabilities; account-based Cosmos and separately branded Mongo clusters need independent feature matrices. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | API family governs identity/audit/backup capabilities; account-based Cosmos and separately branded Mongo clusters need independent feature matrices. |

## 07. Managed Redis (REDIS)

**Resource/evidence boundary:** Microsoft.Cache/redisEnterprise plus databases and access-policy assignments; match modern SKU

**Current executable encryption maturity only:** Partial root read; modern SKU and database children unassessed. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Persistence, export backups, client authentication and cache rebuild from the authoritative store are separate evidence boundaries.

**Service sources:** [redis](https://learn.microsoft.com/en-us/azure/redis/secure-azure-managed-redis)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **REDIS-I** Redis users and access-key authentication (direct) | AC-3, AC-6, IA-9 | Modern cluster/database SKU, accessKeysAuthentication and accessPolicyAssignments/user principal permissions where API exposes them; owner export otherwise. | Only approved Entra principals/Redis command scopes; permitted access-key fallback is justified. Cluster managed identity is not proof of client authentication. Apply domain I parameters. | ARM, AUTH, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **REDIS-N** Modern Redis private and public access (direct) | SC-7 | Cluster publicNetworkAccess, private endpoint approval/target and client DNS/connectivity validation from network owner. | Approved private/public paths match deployed modern service; no legacy Cache for Redis firewall assumptions. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **REDIS-R** Persistence, OS and tier-specific disk encryption (direct) | SC-28, SC-28(1) | Modern SKU/database identity, persistence configuration and current service disk-encryption scope; flash-tier and exported-storage boundaries. | Documented provider encryption applies to actual disk/tier boundary; volatile memory is not misreported as disk encryption and exports are checked separately. Apply domain R parameters. | ARM, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **REDIS-T** Redis encrypted client protocol (direct) | SC-8, SC-8(1) | Database clientProtocol, supported TLS configuration and client trust/validation evidence. | Non-TLS access disabled unless approved; clients use approved TLS and validate the endpoint. Apply domain T parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **REDIS-K** Access-key and optional encryption key lifecycle (direct) | IA-5, SC-12 | Authentication mode, rotation/revocation records, optional CMK/identity reference and expiry/availability evidence. | Permitted credentials can be rotated without unplanned client failure; no keys collected; CMK is optional under this program. Apply domain K parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **REDIS-L** Client connections, authentication and cache health (direct) | AU-2, AU-12, AU-5 | Connection-log categories, management changes, aggregate client/authentication failures and destination/receipt health. | Required connection and administrative events arrive within criteria; connection logs are not assumed to audit each Redis command/value. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **REDIS-C** Database policy and module drift (direct) | CM-2, CM-3, CM-6 | Database clustering/eviction/persistence/module configuration, approved code/IaC and change records. | Chosen cache behavior and optional modules match approved security/data-loss design; changes are tested and reviewed. Apply domain C parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **REDIS-V** Managed server and Redis client components (inherited) | SA-9, SI-2, SA-22 | Managed Redis service support/advisories and exposed engine/module version; customer client/library scan/version reports. | Provider updates are evidenced; clients/modules are supported and remediated against approved deadlines. Apply domain V parameters. | PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **REDIS-B** Export backup versus persistence and replication (direct) | CP-9, CP-10, CP-4 | RDB/AOF persistence, supported geo-replication mode, export job/storage retention evidence and import/rebuild test from authoritative data. | Selected recovery design meets RPO/RTO; persistence can persist corruption and is not backup. Verify mode compatibility before proposing combined protections. Apply domain B parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: REDIS-I, ORG-I | Redis users and access-key authentication |
| N: Public exposure, resource restrictions and private connectivity | direct: REDIS-N | Modern Redis private and public access |
| R: Encryption and protection at rest | direct: REDIS-R | Persistence, OS and tier-specific disk encryption |
| T: Transmission protection | direct: REDIS-T | Redis encrypted client protocol |
| K: Secrets, certificates and key lifecycle | direct: REDIS-K | Access-key and optional encryption key lifecycle |
| L: Audit generation, retention, protection and collection health | direct: REDIS-L, ORG-L | Client connections, authentication and cache health |
| C: Secure configuration, change approval and drift | direct: REDIS-C, ORG-C | Database policy and module drift |
| V: Vulnerabilities, patching, versions and software supply chain | inherited: REDIS-V, ORG-V | Managed server and Redis client components |
| B: Backup, recovery, restore tests and availability | direct: REDIS-B, ORG-B | Export backup versus persistence and replication |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Persistence, export backups, client authentication and cache rebuild from the authoritative store are separate evidence boundaries. |
| D: Detection, incident monitoring and response | shared: ORG-D | Persistence, export backups, client authentication and cache rebuild from the authoritative store are separate evidence boundaries. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Persistence, export backups, client authentication and cache rebuild from the authoritative store are separate evidence boundaries. |

## 08. Function Apps (FUNC)

**Resource/evidence boundary:** Microsoft.Web/sites(kind=functionapp)/slots, hosting plan; Container Apps variant and host/content dependencies

**Current executable encryption maturity only:** Partial site/slot identity; host/content and runtime storage unverified. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Deployment/SCM access, HTTP function authorization, triggers and backing stores are distinct; hosting plan changes available controls.

**Service sources:** [functions-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/functions-security-baseline), [functions-security](https://learn.microsoft.com/en-us/azure/azure-functions/security-concepts)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **FUNC-I** HTTP, trigger, deployment and managed identities (direct) | AC-3, AC-6, IA-9 | authsettingsV2 safe projection, function authorization design, site/slot identity, trigger/client roles and basic publishing credential policy metadata. | Approved caller/trigger/deployment identities enforced; function keys alone are not user identity or least-privilege authorization. Apply domain I parameters. | ARM, AUTH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **FUNC-N** Site and SCM ingress plus dependency paths (direct) | SC-7, AC-4 | publicNetworkAccess and site/SCM access restrictions, private endpoints, hosting-plan network capabilities and trigger/storage links. | App and deployment endpoints match exposure policy; VNet integration for outbound traffic is not evidence of private inbound access. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **FUNC-R** Host, content, deployment and runtime storage (direct) | SC-28, SC-28(1) | Hosting mode and metadata-only dependency manifest for AzureWebJobsStorage/content shares/packages/mounts/temp stores; backing encryption evidence. | All declared stored-data locations meet protection requirement or remain explicit gaps; do not retrieve secret-bearing app settings to discover them. Apply domain R parameters. | ARM, PROCESS, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **FUNC-T** HTTPS, SCM and downstream transport (direct) | SC-8, SC-8(1), SC-17 | httpsOnly, minTlsVersion/scmMinTlsVersion where supported; certificate metadata and client transport tests. | Approved encrypted paths cover HTTP, SCM, triggers and outbound dependencies; app HTTPS redirect alone does not cover downstream calls. Apply domain T parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **FUNC-K** Function keys and Key Vault references (direct) | IA-5, SC-12, SC-17 | Owner-provided redacted Key Vault/reference map, certificate expiry and key rotation/revocation/dependency reload records. | Credentials stay in approved custody and rotate successfully; no host/function keys, publishing credentials or settings values collected. Apply domain K parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **FUNC-L** Execution, application audit and deployment logs (direct) | AU-2, AU-12, AU-5 | Diagnostics/Application Insights/DCR links, runtime audit requirements, sampling and aggregate receipt; deployment/authentication failures. | Security events are retained and not silently lost to sampling, quotas or broken instrumentation; function execution counts alone are insufficient audit. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **FUNC-C** Runtime hardening and deployment change (direct) | CM-2, CM-3, CM-6, CM-7 | Remote debugging/CORS/FTP/basic publishing policy, site/slot baseline, deployment provenance and change/rollback records. | Approved features only; slots/deployments have authorization and validated rollback without exposing application settings. Apply domain C parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **FUNC-V** Function runtime, language and dependency support (direct) | RA-5, SI-2, SA-22, SA-11 | Runtime/language stack from safe config or owner manifest; package/container digests, dependency scans and application input/error security tests. | Supported runtimes and freshly assessed dependencies with timely remediation; provider OS maintenance does not patch customer packages. Apply domain V parameters. | ARM, GUEST, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **FUNC-B** Code redeploy, host state and trigger recovery (direct) | CP-9, CP-10, CP-4 | Source/package/configuration backup, plan-specific backup capability, host/trigger/downstream state and replay/idempotency restore tests. | Whole function workload can recover within limits; site backup does not automatically include trigger sources and external stores. Apply domain B parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: FUNC-I, ORG-I | HTTP, trigger, deployment and managed identities |
| N: Public exposure, resource restrictions and private connectivity | direct: FUNC-N | Site and SCM ingress plus dependency paths |
| R: Encryption and protection at rest | direct: FUNC-R | Host, content, deployment and runtime storage |
| T: Transmission protection | direct: FUNC-T | HTTPS, SCM and downstream transport |
| K: Secrets, certificates and key lifecycle | direct: FUNC-K | Function keys and Key Vault references |
| L: Audit generation, retention, protection and collection health | direct: FUNC-L, ORG-L | Execution, application audit and deployment logs |
| C: Secure configuration, change approval and drift | direct: FUNC-C, ORG-C | Runtime hardening and deployment change |
| V: Vulnerabilities, patching, versions and software supply chain | direct: FUNC-V, ORG-V | Function runtime, language and dependency support |
| B: Backup, recovery, restore tests and availability | direct: FUNC-B, ORG-B | Code redeploy, host state and trigger recovery |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Deployment/SCM access, HTTP function authorization, triggers and backing stores are distinct; hosting plan changes available controls. |
| D: Detection, incident monitoring and response | shared: ORG-D | Deployment/SCM access, HTTP function authorization, triggers and backing stores are distinct; hosting plan changes available controls. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Deployment/SCM access, HTTP function authorization, triggers and backing stores are distinct; hosting plan changes available controls. |

## 09. Key Vaults (KV)

**Resource/evidence boundary:** Microsoft.KeyVault/vaults; key/secret/certificate metadata and versions; managedHSM separate

**Current executable encryption maturity only:** Partial: current guarantee covers secret values only. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Vault administration, object use, key custody, recovery and audit access require separate duties and metadata permissions.

**Service sources:** [key-vault-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/key-vault-security-baseline), [keyvault-security](https://learn.microsoft.com/en-us/azure/key-vault/general/secure-key-vault)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **KV-I** Vault administration versus object use (direct) | AC-3, AC-5, AC-6 | enableRbacAuthorization or accessPolicies, inherited assignments and object scopes; permissions to change access, purge, unwrap, sign or get secrets. | Approved control/data rights and separation of duties; control-plane Reader does not prove or provide secret access. Review legacy policy escalation paths. Apply domain I parameters. | ARM, AUTH, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **KV-N** Vault firewall and private connections (direct) | SC-7 | publicNetworkAccess, networkAcls defaultAction/bypass/IP/VNet rules, approved private endpoint state and target. | Vault access matches approved paths; trusted-service bypass and public exceptions documented with network owner evidence. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **KV-R** Secret, key and certificate protection boundary (direct) | SC-28, SC-28(1), SC-13 | Vault SKU and service guarantee; metadata-only key type/HSM protection requirements and backup/export dependency inventory. | Each selected object class meets approved protection; current secret-value guarantee does not establish key-object or exported-backup coverage. Apply domain R parameters. | ARM, DATA, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **KV-T** Vault API and consuming client transport (direct) | SC-8, SC-8(1) | Provider API TLS assurance and consumer HTTPS/certificate-validation configuration/test records. | Approved transport enforced for each consumer; no raw secret retrieval needed for transport verification. Apply domain T parameters. | PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **KV-K** Object lifecycle, expiry, rotation and revocation (direct) | IA-5, SC-12, SC-17 | Key/secret/certificate version attributes enabled/expiry/not-before, rotation policies, certificate issuer/lifetime and expiration/rollover/revocation records. | Required lifetimes/algorithms/rotation meet approved policy and consumers adopt new versions; metadata reads exclude secret values and private keys. Apply domain K parameters. | DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **KV-L** Vault data access and administrative audit (direct) | AU-2, AU-12, AU-5, AU-9 | AuditEvent or available equivalent categories, destinations/receipt, access-denied/expiry alerts and log reader/purge permissions. | Object-use and administrative events are received/protected and actionable without collecting request secrets. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **KV-C** Recovery safeguards and access-mode changes (direct) | CM-2, CM-3, CM-6 | enablePurgeProtection, softDeleteRetentionInDays, recovery level, deployment/disk/template access flags and access-model change approvals. | Approved deletion and access safeguards enforced; purge-protection/retention changes require authorized design decisions, not collector mutation. Apply domain C parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **KV-V** Managed cryptographic service and clients (inherited) | SA-9, SI-2, SC-13 | Exact service/SKU cryptographic assurance, provider advisories and client SDK/dependency remediation evidence. | Provider cryptographic guarantees match required algorithms/module assurance; no assumption that optional CMK or HSM is universally required. Apply domain V parameters. | PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **KV-B** Vault/object recovery and dependent service recovery (direct) | CP-9, CP-10, CP-4 | Soft-delete/purge protection, protected backup strategy, regional constraints and authorized object recovery/consumer rebind tests. | Keys/secrets/certificates and dependent workloads recover within requirements; soft delete alone is not a complete backup or restore test. Apply domain B parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: KV-I, ORG-I | Vault administration versus object use |
| N: Public exposure, resource restrictions and private connectivity | direct: KV-N | Vault firewall and private connections |
| R: Encryption and protection at rest | direct: KV-R | Secret, key and certificate protection boundary |
| T: Transmission protection | direct: KV-T | Vault API and consuming client transport |
| K: Secrets, certificates and key lifecycle | direct: KV-K | Object lifecycle, expiry, rotation and revocation |
| L: Audit generation, retention, protection and collection health | direct: KV-L, ORG-L | Vault data access and administrative audit |
| C: Secure configuration, change approval and drift | direct: KV-C, ORG-C | Recovery safeguards and access-mode changes |
| V: Vulnerabilities, patching, versions and software supply chain | inherited: KV-V, ORG-V | Managed cryptographic service and clients |
| B: Backup, recovery, restore tests and availability | direct: KV-B, ORG-B | Vault/object recovery and dependent service recovery |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Vault administration, object use, key custody, recovery and audit access require separate duties and metadata permissions. |
| D: Detection, incident monitoring and response | shared: ORG-D | Vault administration, object use, key custody, recovery and audit access require separate duties and metadata permissions. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Vault administration, object use, key custody, recovery and audit access require separate duties and metadata permissions. |

## 10. PostgreSQL Flexible Servers (PG)

**Resource/evidence boundary:** Microsoft.DBforPostgreSQL/flexibleServers; configurations, administrators, firewall/private links and databases

**Current executable encryption maturity only:** Supported scoped managed data/log/temp/backup encryption. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Server authentication flags, SQL role grants, audit extension configuration, replication and restore evidence have different collection permissions.

**Service sources:** [azure-database-for-postgresql-flexible-server-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/azure-database-for-postgresql-flexible-server-security-baseline), [postgres-security](https://learn.microsoft.com/en-us/azure/postgresql/security/security-overview)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **PG-I** Server authentication and database role grants (direct) | AC-3, AC-6, IA-9 | authConfig and administrator metadata; redacted pg_roles/grants/membership/security-definer reviews from a restricted catalog reader. | Only approved Entra/password methods and minimal SQL permissions; Entra enabled does not imply password disabled or least-privilege database grants. Apply domain I parameters. | ARM, AUTH, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PG-N** Server access mode and firewall (direct) | SC-7 | network publicNetworkAccess/delegatedSubnet/privateDnsZone IDs, firewallRules, private endpoint state and approved client path tests. | Deployed public/private mode and exceptions meet approved design; network team owns delegated subnet/DNS/routing administration. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PG-R** Database, logs, temporary data and backups (direct) | SC-28, SC-28(1) | Flexible-server identity and dataEncryption/provider guarantee; external dumps, replicas and exports mapped separately. | Documented service encryption accepted with provider keys; external copies have independent protection evidence. Apply domain R parameters. | ARM, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PG-T** Database TLS and client certificate validation (direct) | SC-8, SC-8(1) | Server parameter TLS/secure-transport settings and client sslmode/trust configuration; authorized negative/plaintext test records. | Required transport is enforced and clients validate server identity; server TLS support alone does not prove verify-full client behavior. Apply domain T parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PG-K** Database credentials and optional CMK (direct) | IA-5, SC-12 | Credential expiry/rotation policy and sampled revocation; optional encryption key/identity/vault metadata and consumer rollover tests. | Approved credential lifecycle operates; read role metadata without password hashes or connection strings. Apply domain K parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PG-L** Database audit, connection logs and destinations (direct) | AU-2, AU-12, AU-5 | pgaudit/logging parameter selections, diagnostic categories, sensitive-query redaction design and aggregate event receipt/lag. | Selected privileged/data operations are audited and retained; enabling log export without database event generation is incomplete. Apply domain L parameters. | ARM, DATA, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PG-C** Extensions, parameters and schema change (direct) | CM-2, CM-3, CM-6, CM-7 | Allowlisted extensions/server parameters, privileged SQL features, IaC/schema migrations and change/rollback records. | Approved baseline and migration privileges enforced; parameter/schema drift reviewed with security impact. Apply domain C parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PG-V** Major versions, extensions and provider maintenance (direct) | RA-5, SI-2, SA-22 | Server version/maintenanceWindow, upgrade/advisory records, extension/client versions and vulnerability reports. | Supported engine/extension/client lifecycle with tested timely upgrades; Microsoft maintenance responsibilities do not remove customer major-version planning. Apply domain V parameters. | ARM, DATA, PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PG-B** PITR, retention, HA and tested recovery (direct) | CP-9, CP-9(1), CP-10, CP-4 | backup retention/geo redundancy, highAvailability/replicas, recovery point metadata and authorized restore/failover application tests. | Actual backup and restore capability meets approved RPO/RTO; HA/replicas alone do not protect against logical corruption. Apply domain B parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: PG-I, ORG-I | Server authentication and database role grants |
| N: Public exposure, resource restrictions and private connectivity | direct: PG-N | Server access mode and firewall |
| R: Encryption and protection at rest | direct: PG-R | Database, logs, temporary data and backups |
| T: Transmission protection | direct: PG-T | Database TLS and client certificate validation |
| K: Secrets, certificates and key lifecycle | direct: PG-K | Database credentials and optional CMK |
| L: Audit generation, retention, protection and collection health | direct: PG-L, ORG-L | Database audit, connection logs and destinations |
| C: Secure configuration, change approval and drift | direct: PG-C, ORG-C | Extensions, parameters and schema change |
| V: Vulnerabilities, patching, versions and software supply chain | direct: PG-V, ORG-V | Major versions, extensions and provider maintenance |
| B: Backup, recovery, restore tests and availability | direct: PG-B, ORG-B | PITR, retention, HA and tested recovery |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Server authentication flags, SQL role grants, audit extension configuration, replication and restore evidence have different collection permissions. |
| D: Detection, incident monitoring and response | shared: ORG-D | Server authentication flags, SQL role grants, audit extension configuration, replication and restore evidence have different collection permissions. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Server authentication flags, SQL role grants, audit extension configuration, replication and restore evidence have different collection permissions. |

## 11. Azure Container Apps (ACA)

**Resource/evidence boundary:** Microsoft.App/containerApps, jobs, managedEnvironments; revisions, identities and storage dependencies

**Current executable encryption maturity only:** Partial metadata; revisions and storage dependencies incomplete. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** App/job runtime, environment, revision/image, secret references and backing data stores require independent evidence; job-start rights can expose identity/secret use.

**Service sources:** [azure-container-apps-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/azure-container-apps-security-baseline), [container-apps](https://learn.microsoft.com/en-us/azure/container-apps/security), [container-apps-architecture](https://learn.microsoft.com/en-us/azure/well-architected/service-guides/azure-container-apps)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **ACA-I** App callers, runtime identities and job execution (direct) | AC-3, AC-6, IA-9 | authConfigs safe metadata, managed identity lifecycle/roles, registry pull identity and job start/update permissions. | Approved callers and minimal identities; review job-start and role wildcard abilities as powerful access even without explicit listSecrets. Apply domain I parameters. | ARM, AUTH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACA-N** Environment and app ingress/egress boundaries (direct) | SC-7, AC-4 | Environment publicNetworkAccess/private endpoint/internal design; app ingress external/transport/IP restrictions and dependency endpoints. | App/environment restrictions meet approved paths; internal ingress and VNet routing are evaluated separately from private endpoints. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACA-R** Ephemeral and mounted application storage (direct) | SC-28, SC-28(1) | App/job revision volume types, environment storage references via safe owner manifest, platform encryption scope and backing-store results. | All selected ephemeral/persistent/external stores are accounted for; no secret-bearing environment storage payloads retrieved. Apply domain R parameters. | ARM, PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACA-T** Ingress, service traffic and certificates (direct) | SC-8, SC-8(1), SC-17 | ingress allowInsecure, transport/clientCertificateMode, custom-domain certificate metadata, selected peer mTLS and downstream client tests. | Required encrypted paths and certificate validation operate end to end; HTTP ingress TLS does not automatically cover TCP/Dapr/downstream traffic. Apply domain T parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACA-K** Secret references and consumer refresh (direct) | IA-5, SC-12, SC-17 | Secret names/references only, Key Vault identity grants, certificate lifecycle and revision/application refresh tests. | Secrets use approved custody and rotate/revoke successfully across revisions; no listSecrets, literal environment values or secret volumes read. Apply domain K parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACA-L** Application/system audit and collection health (direct) | AU-2, AU-12, AU-5 | Environment logsConfiguration/diagnostics, Dapr/app audit requirements, job/revision outcomes and aggregate receipt/lag. | Required application/security events reach protected destinations; console logs are not automatically adequate security audit. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACA-C** Revisions, scale rules and deployment configuration (direct) | CM-2, CM-3, CM-6, CM-7 | Revision/image digest and traffic split, ingress/Dapr/scale-rule configuration, job schedule and approved deployment/change history. | Approved runnable revisions and minimal features; deployment and traffic changes reviewed with rollback evidence. Apply domain C parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACA-V** Container images and managed platform (direct) | RA-5, SI-2, SI-7, SA-22 | Deployed image digests, SBOM/provenance, registry scan results, runtime support and provider host assurance. | Actual deployed images have fresh vulnerability coverage and timely remediation; managed hosts do not patch customer image packages. Apply domain V parameters. | ARM, GUEST, PROVIDER, PROCESS, WIZ. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACA-B** Declarative rebuild and application state recovery (direct) | CP-9, CP-10, CP-4 | Revision/IaC artifacts, protected backing stores, zone/min replica/scale design and redeploy/restore/failover exercise records. | Recover configuration and business state within RTO/RPO; replicas and retained revisions are not complete data backups. Apply domain B parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: ACA-I, ORG-I | App callers, runtime identities and job execution |
| N: Public exposure, resource restrictions and private connectivity | direct: ACA-N | Environment and app ingress/egress boundaries |
| R: Encryption and protection at rest | direct: ACA-R | Ephemeral and mounted application storage |
| T: Transmission protection | direct: ACA-T | Ingress, service traffic and certificates |
| K: Secrets, certificates and key lifecycle | direct: ACA-K | Secret references and consumer refresh |
| L: Audit generation, retention, protection and collection health | direct: ACA-L, ORG-L | Application/system audit and collection health |
| C: Secure configuration, change approval and drift | direct: ACA-C, ORG-C | Revisions, scale rules and deployment configuration |
| V: Vulnerabilities, patching, versions and software supply chain | direct: ACA-V, ORG-V | Container images and managed platform |
| B: Backup, recovery, restore tests and availability | direct: ACA-B, ORG-B | Declarative rebuild and application state recovery |
| O: Inventory, ownership and lifecycle | shared: ORG-O | App/job runtime, environment, revision/image, secret references and backing data stores require independent evidence; job-start rights can expose identity/secret use. |
| D: Detection, incident monitoring and response | shared: ORG-D | App/job runtime, environment, revision/image, secret references and backing data stores require independent evidence; job-start rights can expose identity/secret use. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | App/job runtime, environment, revision/image, secret references and backing data stores require independent evidence; job-start rights can expose identity/secret use. |

## 12. user-assigned managed identities (UAMI)

**Resource/evidence boundary:** Microsoft.ManagedIdentity/userAssignedIdentities; federatedIdentityCredentials; principal links and assignment relationships

**Current executable encryption maturity only:** Encryption-only inventory N/A; identity controls not implemented. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Identity owners must govern every attached resource, federated trust and effective grant; deletion and recreation can change principal identity.

**Service sources:** [uami](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/managed-identity-best-practice-recommendations), [graph-app](https://learn.microsoft.com/en-us/graph/api/application-list?view=graph-rest-1.0), [graph-roles](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-approleassignments?view=graph-rest-1.0)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **UAMI-I** Identity assignment and effective privileges (direct) | AC-3, AC-6, IA-9 | principalId/clientId/tenantId, resources using identity, identity assign/action permissions, ARM/data-plane grants and Graph app-role grants. | Only approved workloads may attach/use the identity; effective permissions are minimal. Anyone able to run code on an attached workload may exercise its permissions. Apply domain I parameters. | ARM, AUTH, GRAPH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **UAMI-N** Federated and attached-workload trust boundary (direct) | AC-4, IA-9 | Attachment inventory, federated issuer/subject/audiences and resource restriction/isolation settings where supported; consuming resource network boundaries. | Reuse/federation matches approved trust domains; identity has no service-local firewall, and preview assignment restrictions are not assumed mandatory. Apply domain N parameters. | ARM, AUTH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **UAMI-T** Identity token consumption paths (direct) | SC-8, IA-9 | Provider token issuance guarantee and host/application handling of identity endpoint/token exchange; consumer TLS validation evidence. | Bearer tokens remain within intended workload trust boundary and are sent only to validated encrypted resource endpoints; no token is collected. Apply domain T parameters. | PROCESS, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **UAMI-K** Provider credentials and customer federation lifecycle (direct) | IA-5, IA-9 | Provider credential lifecycle assurance, federated trust metadata and removal/compromise/revocation procedures. | No manual rotation requirement invented for platform-managed identity credentials; stale federated trust and workload assignment are removed on time. Apply domain K parameters. | ARM, PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **UAMI-L** Assignment, federation and workload sign-in monitoring (direct) | AU-2, AU-12, AU-5 | Activity Log changes, Graph managed-identity sign-in coverage where available and target service authorization logs; export/retention. | Assignment/permission/federation changes and required identity use are observable; sign-in/API availability gaps are recorded. Apply domain L parameters. | ARM, GAUDIT, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **UAMI-C** Identity trust and role drift (direct) | CM-2, CM-3, CM-6 | Approved assignment/federated/role manifest, change actor/time and drift history. | Identity reuse and role/federation changes have approval and impact analysis across all attached workloads. Apply domain C parameters. | ARM, AUTH, GRAPH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **UAMI-B** Identity dependency recovery and reauthorization (direct) | CP-2, CP-10, CP-4 | IaC and approved trust/grant manifest, identity recreation and role/client-reference rebind procedures; exercise evidence. | Workloads recover with intended principal/permissions; deletion/recreation is not assumed to preserve principalId/clientId or downstream grants. Apply domain B parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: UAMI-I, ORG-I | Identity assignment and effective privileges |
| N: Public exposure, resource restrictions and private connectivity | direct: UAMI-N | Federated and attached-workload trust boundary |
| T: Transmission protection | direct: UAMI-T | Identity token consumption paths |
| K: Secrets, certificates and key lifecycle | direct: UAMI-K | Provider credentials and customer federation lifecycle |
| L: Audit generation, retention, protection and collection health | direct: UAMI-L, ORG-L | Assignment, federation and workload sign-in monitoring |
| C: Secure configuration, change approval and drift | direct: UAMI-C, ORG-C | Identity trust and role drift |
| B: Backup, recovery, restore tests and availability | direct: UAMI-B, ORG-B | Identity dependency recovery and reauthorization |
| V: Vulnerabilities, patching, versions and software supply chain | not_resource_local: ORG-S | No customer OS/image on an identity. Provider service assurance and vulnerabilities in every attached workload are evaluated separately. |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Identity owners must govern every attached resource, federated trust and effective grant; deletion and recreation can change principal identity. |
| D: Detection, incident monitoring and response | shared: ORG-D | Identity owners must govern every attached resource, federated trust and effective grant; deletion and recreation can change principal identity. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Identity owners must govern every attached resource, federated trust and effective grant; deletion and recreation can change principal identity. |
| R: Encryption and protection at rest | not_resource_local: ORG-S | No customer data store or configurable at-rest mechanism on the identity resource. Provider directory assurance and every consuming workload/store remain applicable. |

## 13. private endpoints (PE)

**Resource/evidence boundary:** Microsoft.Network/privateEndpoints; privateLinkServiceConnections/manual connections, privateDnsZoneGroups and target resources

**Current executable encryption maturity only:** Encryption-only inventory N/A; connectivity controls unimplemented. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Platform owns endpoint target/approval evidence and target-service restriction; network team owns VNet, routing, firewall and DNS configuration/effective path validation.

**Service sources:** [azure-private-link-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/azure-private-link-security-baseline), [private-endpoint](https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-overview)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **PE-I** Endpoint creation, connection approval and target authorization (direct) | AC-3, AC-5, AC-6 | Endpoint/target RBAC, approval actor/state, cross-subscription/tenant approvals and service data-plane authorization. | Only authorized parties create/approve links; endpoint reachability does not replace target service authentication. Apply domain I parameters. | ARM, AUTH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PE-N** Exact private target and effective connectivity (direct) | SC-7, AC-4 | privateLinkServiceId/groupIds, connection status, subnet/NIC/DNS zone group references and target public-access settings; network owner path/DNS test. | Endpoint is approved for intended target/subresource, resolves/routes as designed and target exposure satisfies policy. Connection Approved alone does not prove public access disabled. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PE-T** Application encryption across private connectivity (direct) | SC-8, SC-8(1) | Target protocol/TLS configuration and client trust tests; private path ownership evidence. | Private routing is not treated as transport encryption; each application protocol meets the same approved encryption criteria. Apply domain T parameters. | PROCESS, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PE-L** Endpoint changes and target access observability (direct) | AU-2, AU-12, AU-5 | Activity Log create/delete/approval changes, target resource audit logs and approved network-team flow/connectivity evidence. | Changes and relevant access are observable; no unsupported assumption that the endpoint emits per-request service audit logs. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PE-C** Connection and DNS linkage drift (direct) | CM-2, CM-3, CM-6 | Approved target/groupIds/subnet/DNS reference manifest and change history; orphaned/rejected/pending connection reconciliation. | Linkage changes are reviewed, stale endpoints resolved and shared network configuration evidence remains with its owner. Apply domain C parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PE-B** Private connectivity recovery (direct) | CP-2, CP-10, CP-4 | Versioned endpoint/link declarations, dependency map and network-owner DNS/reconnection/failover exercise results. | Connectivity can be recreated and verified within recovery requirements; no customer data backup is claimed for an endpoint object. Apply domain B parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: PE-I, ORG-I | Endpoint creation, connection approval and target authorization |
| N: Public exposure, resource restrictions and private connectivity | direct: PE-N | Exact private target and effective connectivity |
| T: Transmission protection | direct: PE-T | Application encryption across private connectivity |
| L: Audit generation, retention, protection and collection health | direct: PE-L, ORG-L | Endpoint changes and target access observability |
| C: Secure configuration, change approval and drift | direct: PE-C, ORG-C | Connection and DNS linkage drift |
| B: Backup, recovery, restore tests and availability | direct: PE-B, ORG-B | Private connectivity recovery |
| V: Vulnerabilities, patching, versions and software supply chain | not_resource_local: ORG-S | Provider-managed connectivity has no customer patchable endpoint OS; network appliance/client/target vulnerabilities belong to their owners, with provider assurance for the service. |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Platform owns endpoint target/approval evidence and target-service restriction; network team owns VNet, routing, firewall and DNS configuration/effective path validation. |
| D: Detection, incident monitoring and response | shared: ORG-D | Platform owns endpoint target/approval evidence and target-service restriction; network team owns VNet, routing, firewall and DNS configuration/effective path validation. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Platform owns endpoint target/approval evidence and target-service restriction; network team owns VNet, routing, firewall and DNS configuration/effective path validation. |
| R: Encryption and protection at rest | not_resource_local: ORG-S | Private endpoint is a network interface/link, not a customer at-rest store; protection of target data, configuration exports and provider systems is assessed elsewhere. |
| K: Secrets, certificates and key lifecycle | not_resource_local: ORG-G | No resource-local application credential/key store. Target-service certificates and credentials remain in target checks; platform connection approval is authorization evidence. |

## 14. Azure Container Registries (ACR)

**Resource/evidence boundary:** Microsoft.ContainerRegistry/registries; repositories/artifacts, tokens/scopeMaps, replications and tasks

**Current executable encryption maturity only:** Supported scoped registry image/artifact encryption. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Registry administration and image pull/push rights differ; exact deployed digests, task identities and publisher provenance need evidence beyond registry configuration.

**Service sources:** [container-registry-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/container-registry-security-baseline), [registry-security](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-best-practices)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **ACR-I** Push/pull, administrator and task rights (direct) | AC-3, AC-6, IA-9 | adminUserEnabled, anonymousPullEnabled, roleAssignmentMode/ABAC where supported, tokens/scopeMaps and task/pull identities. | Approved repository-scoped pull/push/admin rights; admin/shared credentials justified; repository ABAC mode matched to actual role behavior. Apply domain I parameters. | ARM, AUTH, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACR-N** Registry ingress and data endpoints (direct) | SC-7, AC-4 | publicNetworkAccess, networkRuleSet, bypass, private endpoint/group IDs and regional data endpoint/replication paths. | All required registry/data endpoints meet approved exposure design; broad trusted-service access exceptions documented. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACR-R** Registry stored artifacts and copies (direct) | SC-28, SC-28(1) | Exact registry identity and encryption guarantee/configuration, replication scope and external export/pull dependencies. | Provider encryption accepted for stored registry artifacts; pulled layers and runtime writes are assessed on their destinations. Apply domain R parameters. | ARM, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACR-T** Registry API and image transport (direct) | SC-8, SC-8(1) | Service HTTPS guarantee and client registry configuration/certificate validation; any unencrypted/export paths. | Approved encrypted transfer and server verification; private endpoints alone do not establish image authenticity. Apply domain T parameters. | ARM, PROCESS, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACR-K** Repository tokens, credentials and optional CMK (direct) | IA-5, SC-12 | Token credential expiry metadata, scope maps, rotation/revocation records and optional encryption key/identity references. | Credentials are scoped and rotated; no registry passwords, task credentials or token values collected. Apply domain K parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACR-L** Login and repository operation audit (direct) | AU-2, AU-12, AU-5 | Available login/repository event categories, destinations, aggregate receipt and suspicious push/delete/pull detection. | Required artifact and authentication actions are logged and retained; SKU/category support recorded rather than inferred. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACR-C** Artifact immutability policy and task changes (direct) | CM-2, CM-3, CM-6, CM-14 | Repository write/delete attributes, tag/digest conventions, task/source/identity metadata and signature verification policy/records. | Approved artifacts and controlled promotion; mutable tags cannot stand in for immutable digest identity; selected signature policy is actually verified. Apply domain C parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACR-V** Stored image vulnerabilities and provenance (direct) | RA-5, SI-2, SI-7, SR-4 | Image digest inventory, scan timestamps/scope/results, SBOM/provenance/signature validation and remediation/rebuild records. | Required artifacts have current scans and traceable trusted provenance; paid scanning plan presence is not scan coverage or remediation. Apply domain V parameters. | DATA, GUEST, PROCESS, WIZ. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **ACR-B** Artifact availability and registry recovery (direct) | CP-9, CP-10, CP-4 | Replication/tier configuration, protected artifact/source copies, deletion retention options and tested registry/task rebuild and image pull. | Critical immutable digests recover within approved requirements; geo-replication or soft delete alone is not an isolated backup. Apply domain B parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: ACR-I, ORG-I | Push/pull, administrator and task rights |
| N: Public exposure, resource restrictions and private connectivity | direct: ACR-N | Registry ingress and data endpoints |
| R: Encryption and protection at rest | direct: ACR-R | Registry stored artifacts and copies |
| T: Transmission protection | direct: ACR-T | Registry API and image transport |
| K: Secrets, certificates and key lifecycle | direct: ACR-K | Repository tokens, credentials and optional CMK |
| L: Audit generation, retention, protection and collection health | direct: ACR-L, ORG-L | Login and repository operation audit |
| C: Secure configuration, change approval and drift | direct: ACR-C, ORG-C | Artifact immutability policy and task changes |
| V: Vulnerabilities, patching, versions and software supply chain | direct: ACR-V, ORG-V | Stored image vulnerabilities and provenance |
| B: Backup, recovery, restore tests and availability | direct: ACR-B, ORG-B | Artifact availability and registry recovery |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Registry administration and image pull/push rights differ; exact deployed digests, task identities and publisher provenance need evidence beyond registry configuration. |
| D: Detection, incident monitoring and response | shared: ORG-D | Registry administration and image pull/push rights differ; exact deployed digests, task identities and publisher provenance need evidence beyond registry configuration. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Registry administration and image pull/push rights differ; exact deployed digests, task identities and publisher provenance need evidence beyond registry configuration. |

## 15. backup vaults (BV)

**Resource/evidence boundary:** Microsoft.DataProtection/backupVaults and Microsoft.RecoveryServices/vaults; policies, backupInstances/protectedItems, jobs and recovery points

**Current executable encryption maturity only:** Supported vault-stored encryption for both families; item/job coverage absent. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Vault protection, source workload coverage, operational snapshots, hybrid agents and restore targets are distinct. Features depend on vault family/workload.

**Service sources:** [backup-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/backup-security-baseline), [backup-security](https://learn.microsoft.com/en-us/azure/backup/security-overview)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **BV-I** Backup, restore, delete and security administration (direct) | AC-3, AC-5, AC-6 | Vault/item RBAC, restore/delete/purge permissions, Resource Guard/multi-user authorization configuration and approval records. | Incompatible backup/security/delete duties separated; privileged destructive paths require selected approvals and only authorized restore destinations. Apply domain I parameters. | ARM, AUTH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **BV-N** Vault and protected-workload connectivity (direct) | SC-7, AC-4 | Family-supported public access/private endpoints, approved source/restore data paths and hybrid agent connectivity design. | Vault network settings match protection scenario; private endpoints do not imply all backup/restore traffic follows one path. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **BV-R** Vault encryption versus snapshots and restores (direct) | SC-28, SC-28(1) | Vault family/encryption properties and provider guarantee; key references if used; operational snapshot, source and restore store IDs. | Provider keys accepted for vault-held data; every out-of-vault copy is separately covered or flagged. Apply domain R parameters. | ARM, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **BV-T** Backup/restore transport and hybrid agents (direct) | SC-8, SC-8(1) | Workload/agent transport documentation, agent TLS configuration and client validation evidence. | Selected data paths and agents use approved encrypted protocols; vault storage encryption does not prove transport security. Apply domain T parameters. | PROCESS, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **BV-K** Optional CMK, agent/passphrase and credential custody (direct) | IA-5, SC-12 | Metadata-only optional key references, vault identity rights and protected hybrid credential/passphrase custody/recovery procedures. | Selected credentials/keys remain available, protected and recoverable through rotations; never collect passphrases or vault credential files. Apply domain K parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **BV-L** Backup failures, deletion events and monitoring health (direct) | AU-2, AU-12, AU-5 | Jobs/alerts and diagnostics, failed/missed backups, destructive changes, aggregate recent success and alert routing. | Missed/failed jobs, deletion/security changes and monitoring gaps are detected and assigned; successful jobs do not establish data integrity alone. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **BV-C** Soft delete, immutability and policy change (direct) | CM-2, CM-3, CM-6 | Family-specific soft-delete/immutability/MUA settings, policy retention/schedule and protected-item exclusions/change approvals. | Safeguards match approved threat/retention policy; no duration invented or immutable lock enabled by assessment tooling. Apply domain C parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **BV-V** Backup agent and managed vault maintenance (direct) | SI-2, SA-22, SA-9 | Hybrid agent/extension versions/health and advisories; managed vault provider assurance. | Customer agents are supported/remediated; provider vault maintenance has evidenced inheritance and is not confused with workload patching. Apply domain V parameters. | ARM, GUEST, PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **BV-B** Protected-item completeness and recovery evidence (direct) | CP-9, CP-9(1), CP-10, CP-4 | Reconcile source inventory to protected items/instances, policies, jobs and recovery points; authorized restores with integrity and application tests. | Every required source has current recoverable protection meeting RPO/RTO; exclusions and unprotected resources explicit; both vault families handled independently. Apply domain B parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: BV-I, ORG-I | Backup, restore, delete and security administration |
| N: Public exposure, resource restrictions and private connectivity | direct: BV-N | Vault and protected-workload connectivity |
| R: Encryption and protection at rest | direct: BV-R | Vault encryption versus snapshots and restores |
| T: Transmission protection | direct: BV-T | Backup/restore transport and hybrid agents |
| K: Secrets, certificates and key lifecycle | direct: BV-K | Optional CMK, agent/passphrase and credential custody |
| L: Audit generation, retention, protection and collection health | direct: BV-L, ORG-L | Backup failures, deletion events and monitoring health |
| C: Secure configuration, change approval and drift | direct: BV-C, ORG-C | Soft delete, immutability and policy change |
| V: Vulnerabilities, patching, versions and software supply chain | direct: BV-V, ORG-V | Backup agent and managed vault maintenance |
| B: Backup, recovery, restore tests and availability | direct: BV-B, ORG-B | Protected-item completeness and recovery evidence |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Vault protection, source workload coverage, operational snapshots, hybrid agents and restore targets are distinct. Features depend on vault family/workload. |
| D: Detection, incident monitoring and response | shared: ORG-D | Vault protection, source workload coverage, operational snapshots, hybrid agents and restore targets are distinct. Features depend on vault family/workload. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Vault protection, source workload coverage, operational snapshots, hybrid agents and restore targets are distinct. Features depend on vault family/workload. |

## 16. App Configuration (APPC)

**Resource/evidence boundary:** Microsoft.AppConfiguration/configurationStores; replicas, snapshots and Key Vault references

**Current executable encryption maturity only:** Supported service stored-value encryption; values not fetched. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Configuration readers/writers, secret references, snapshots and replica/client failover require separate control evidence.

**Service sources:** [appconfig](https://learn.microsoft.com/en-us/azure/azure-app-configuration/secure-azure-app-configuration)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **APPC-I** Configuration data roles and access-key fallback (direct) | AC-3, AC-6, IA-9 | disableLocalAuth, identity and data reader/owner versus control-plane roles; client Entra authentication design. | Only approved read/write principals; local keys justified; ARM administration and data access assessed separately. Apply domain I parameters. | ARM, AUTH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPC-N** Store and replica private/public access (direct) | SC-7, AC-4 | publicNetworkAccess/private endpoint state, replica IDs/locations and client endpoint selection. | Store/replica paths satisfy approved exposure/data-location requirements with network team connectivity evidence. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPC-R** Configuration store and external values (direct) | SC-28, SC-28(1) | Store identity/encryption guarantee and optional CMK reference; exported snapshots/client caches and linked Key Vault boundaries. | Provider-managed protection accepted for service data; external exports, caches and referenced secrets independently covered. Apply domain R parameters. | ARM, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPC-T** SDK endpoint and refresh transport (direct) | SC-8, SC-8(1) | Service HTTPS guarantee, application/provider endpoint and certificate-validation tests across replicas. | All retrieval/refresh/failover paths use approved encrypted transport and valid endpoint trust. Apply domain T parameters. | PROCESS, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPC-K** Key Vault references and refresh lifecycle (direct) | IA-5, SC-12 | Reference type/target metadata from owner-safe export, identities, optional key references and secret/certificate refresh/rotation tests. | Secrets are kept in approved secret custody and consumers refresh/revoke them per policy; do not enumerate configuration values. Apply domain K parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPC-L** Configuration access/change and refresh failures (direct) | AU-2, AU-12, AU-5 | HTTP request/audit categories available, administrative changes, 401/403/failure aggregates and diagnostic receipt. | Required changes/access failures reach monitoring and retention; availability metrics do not replace data-plane event requirements. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPC-C** Feature flag/configuration deployment safety (direct) | CM-2, CM-3, CM-6 | Snapshot metadata/IDs, labels and approved feature/configuration rollout records, least-privileged writer and rollback tests. | Approved last-known-good versions and change review operate; schema/value safety assessed through owner-controlled reviews without exposing secrets. Apply domain C parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPC-V** Managed store and application provider SDK (inherited) | SA-9, SI-2, SA-22 | Service assurance and client provider/library version, dependency vulnerabilities and release notices. | Customer SDKs and configuration-consuming applications are supported/remediated while service platform duties are inherited. Apply domain V parameters. | PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **APPC-B** Snapshots, deletion recovery and replica failover (direct) | CP-9, CP-10, CP-4 | Snapshot retention, soft-delete/purge protection, replicas, protected configuration exports and client failover/restore exercises. | Selected rollback/disaster recovery meets RPO/RTO; immutable configuration snapshots and geo-replication are not automatically independent backups. Apply domain B parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: APPC-I, ORG-I | Configuration data roles and access-key fallback |
| N: Public exposure, resource restrictions and private connectivity | direct: APPC-N | Store and replica private/public access |
| R: Encryption and protection at rest | direct: APPC-R | Configuration store and external values |
| T: Transmission protection | direct: APPC-T | SDK endpoint and refresh transport |
| K: Secrets, certificates and key lifecycle | direct: APPC-K | Key Vault references and refresh lifecycle |
| L: Audit generation, retention, protection and collection health | direct: APPC-L, ORG-L | Configuration access/change and refresh failures |
| C: Secure configuration, change approval and drift | direct: APPC-C, ORG-C | Feature flag/configuration deployment safety |
| V: Vulnerabilities, patching, versions and software supply chain | inherited: APPC-V, ORG-V | Managed store and application provider SDK |
| B: Backup, recovery, restore tests and availability | direct: APPC-B, ORG-B | Snapshots, deletion recovery and replica failover |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Configuration readers/writers, secret references, snapshots and replica/client failover require separate control evidence. |
| D: Detection, incident monitoring and response | shared: ORG-D | Configuration readers/writers, secret references, snapshots and replica/client failover require separate control evidence. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Configuration readers/writers, secret references, snapshots and replica/client failover require separate control evidence. |

## 17. Application Insights (AI)

**Resource/evidence boundary:** Microsoft.Insights/components; WorkspaceResourceId, SDK/OpenTelemetry instrumentation, private-link scopes and exports

**Current executable encryption maturity only:** Partial; scoped telemetry encryption depends on resolved Log Analytics workspace. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Instrumentation, telemetry privacy, sampling, ingestion identity, query access and linked workspace are different evidence boundaries.

**Service sources:** [azure-monitor-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/azure-monitor-security-baseline), [appinsights-auth](https://learn.microsoft.com/en-us/azure/azure-monitor/app/azure-ad-authentication), [monitor-logs](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/best-practices-logs), [monitor-private](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/private-link-vm-kubernetes)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **AI-I** Telemetry ingestion and query authorization (direct) | AC-3, AC-6, IA-9 | DisableLocalAuth, ingestion identity/role mapping, workspace/resource query access and any legacy API key inventory metadata. | Approved ingestion/query identities only; instrumentation/connection identifiers are not treated as authentication credentials or access-control proof. Apply domain I parameters. | ARM, AUTH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AI-N** Ingestion/query exposure and private-link path (direct) | SC-7, AC-4 | PublicNetworkAccessForIngestion/Query, private-link scope associations/access modes, workspace/DCE linkage and SDK endpoints. | Both ingestion and query paths satisfy approved exposure design; network owner validates shared AMPLS/DNS interactions. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AI-R** Workspace-backed telemetry and exports (direct) | SC-28, SC-28(1) | Component WorkspaceResourceId, successful linked workspace encryption evidence and export destination inventory. | Telemetry store is resolved and scoped protection verified; classic/unresolved storage is not covered by a generic Monitor assertion. Apply domain R parameters. | ARM, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AI-T** Telemetry SDK and exporter transport (direct) | SC-8, SC-8(1) | SDK/exporter endpoint scheme, proxy/collector hops and TLS certificate-validation evidence. | Telemetry uses approved encrypted paths through every collector/proxy hop, not just the final Azure endpoint. Apply domain T parameters. | PROCESS, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AI-K** Ingestion identity, legacy keys and web-test certificates (direct) | IA-5, SC-17 | Identity design and legacy API-key purpose/expiry metadata; availability-test credential/certificate custody references only. | Permitted credentials/certificates follow lifecycle policy; avoid raw connection strings, test headers, tokens and test URLs containing credentials. Apply domain K parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AI-L** Instrumentation receipt, sampling and collection health (direct) | AU-2, AU-12, AU-5 | Instrumentation/SDK configuration, sampling/caps, linked tables, aggregate recent events/lag and outage/ingestion alerts. | Required security audit is complete enough for purpose; sampled application telemetry cannot be claimed as exhaustive access audit. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AI-C** Instrumentation/privacy and alert configuration drift (direct) | CM-2, CM-3, CM-6, SI-12 | Approved instrumentation/redaction/sampling/retention settings, synthetic-test metadata and change records. | Changes preserve required audit detail and approved privacy minimization; query URLs/bodies and user identifiers are reviewed before collection. Apply domain C parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AI-V** SDK, collector and application dependency support (direct) | RA-5, SI-2, SA-22 | OpenTelemetry/SDK/exporter and application version/SBOM/scan records, supported instrumentation configuration and provider assurance. | Customer instrumentation is supported/remediated; managed telemetry service maintenance does not upgrade application libraries. Apply domain V parameters. | GUEST, PROCESS, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AI-B** Monitoring recovery and retained telemetry access (direct) | CP-2, CP-9, CP-10, CP-4 | IaC for component/workspace/alerts, approved telemetry retention/export strategy, instrumentation redeploy and monitoring restoration tests. | Required historic telemetry and monitoring functions can recover; workspace retention does not guarantee an independent recoverable copy. Apply domain B parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: AI-I, ORG-I | Telemetry ingestion and query authorization |
| N: Public exposure, resource restrictions and private connectivity | direct: AI-N | Ingestion/query exposure and private-link path |
| R: Encryption and protection at rest | direct: AI-R | Workspace-backed telemetry and exports |
| T: Transmission protection | direct: AI-T | Telemetry SDK and exporter transport |
| K: Secrets, certificates and key lifecycle | direct: AI-K | Ingestion identity, legacy keys and web-test certificates |
| L: Audit generation, retention, protection and collection health | direct: AI-L, ORG-L | Instrumentation receipt, sampling and collection health |
| C: Secure configuration, change approval and drift | direct: AI-C, ORG-C | Instrumentation/privacy and alert configuration drift |
| V: Vulnerabilities, patching, versions and software supply chain | direct: AI-V, ORG-V | SDK, collector and application dependency support |
| B: Backup, recovery, restore tests and availability | direct: AI-B, ORG-B | Monitoring recovery and retained telemetry access |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Instrumentation, telemetry privacy, sampling, ingestion identity, query access and linked workspace are different evidence boundaries. |
| D: Detection, incident monitoring and response | shared: ORG-D | Instrumentation, telemetry privacy, sampling, ingestion identity, query access and linked workspace are different evidence boundaries. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Instrumentation, telemetry privacy, sampling, ingestion identity, query access and linked workspace are different evidence boundaries. |

## 18. Managed Grafana (GRAF)

**Resource/evidence boundary:** Microsoft.Dashboard/grafana; managed private endpoints, data sources, service accounts, dashboards and folders

**Current executable encryption maturity only:** Unsupported; documented encryption is research only. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Workspace access does not automatically preserve data-source access restrictions; shared managed-identity queries and dashboard sharing need explicit review.

**Service sources:** [grafana](https://learn.microsoft.com/en-us/azure/managed-grafana/secure-azure-managed-grafana), [grafana-encryption](https://learn.microsoft.com/en-us/azure/managed-grafana/encryption), [grafana-private](https://learn.microsoft.com/en-us/azure/managed-grafana/how-to-set-up-private-access)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **GRAF-I** Grafana roles and data-source authorization (direct) | AC-3, AC-6, IA-9 | Grafana Admin/Editor/Viewer assignments, folder/dashboard permissions, service-account scopes and data-source current-user versus shared identity modes. | Approved least privilege at workspace and data source; a dashboard viewer must not gain unintended data through a broad shared managed identity. Apply domain I parameters. | ARM, AUTH, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **GRAF-N** Workspace ingress and data-source egress (direct) | SC-7, AC-4 | publicNetworkAccess/private endpoint status, managed private endpoints, deterministic egress design and approved data-source targets. | Both inbound and outbound paths match policy; private workspace configuration does not make its SSO endpoint private or isolate every data source. Apply domain N parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **GRAF-R** Grafana configuration/data and source stores (direct) | SC-28, SC-28(1) | Exact workspace identity and current Grafana documented storage/encryption guarantee; data-source store boundaries. | Provider encryption substantiated for Grafana-owned data; source databases and exported dashboards/snapshots separately assessed. Apply domain R parameters. | ARM, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **GRAF-T** Browser and each data-source transport (direct) | SC-8, SC-8(1), SC-17 | Service TLS assurance, redacted data-source scheme/TLS validation flags and trust/certificate metadata. | Approved encryption and verification for each data source; do not assume external plugins/endpoints inherit Azure-managed transport guarantees. Apply domain T parameters. | DATA, PROCESS, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **GRAF-K** Service-account tokens and data-source credentials (direct) | IA-5, SC-12 | apiKey/service-account enablement, token expiry/role/last-use metadata and data-source credential custody/rotation evidence. | Automated tokens are justified, scoped, expired/rotated and revocable; do not collect token values or secureJsonData. Apply domain K parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **GRAF-L** Authentication, administrative and datasource monitoring (direct) | AU-2, AU-12, AU-5 | Available Grafana diagnostic categories, login/request/administrative event requirements, destinations and aggregate health. | Required event types are emitted/retained and missing categories recorded; dashboard request metrics alone do not prove all administrative audit. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **GRAF-C** Snapshot sharing, plugins and version-specific settings (direct) | CM-2, CM-3, CM-6, CM-7 | External snapshot sharing, plugin/data-source allowlist, config/version metadata and approved changes; CSRF setting only where version exposes it. | No unapproved public snapshots/plugins/features; settings evaluated against actual Grafana major version and managed-service restrictions. Apply domain C parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **GRAF-V** Managed Grafana and enabled plugin lifecycle (direct) | SA-9, SI-2, SA-22, SR-6 | Workspace major version, enabled plugin/vendor inventory, security advisories and provider update responsibilities. | Supported service/version and reviewed plugin supplier risks; do not assume arbitrary plugin installation or every plugin's patches are customer-controlled. Apply domain V parameters. | ARM, DATA, PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **GRAF-B** Dashboard/configuration recovery and availability (direct) | CP-9, CP-10, CP-4 | Zone redundancy, safe dashboard/data-source configuration backup metadata, alternate-region design and rebuild/rebind exercise. | Recover approved dashboards, alerting and data-source access within limits; zone redundancy is not cross-region disaster recovery or dashboard backup. Apply domain B parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: GRAF-I, ORG-I | Grafana roles and data-source authorization |
| N: Public exposure, resource restrictions and private connectivity | direct: GRAF-N | Workspace ingress and data-source egress |
| R: Encryption and protection at rest | direct: GRAF-R | Grafana configuration/data and source stores |
| T: Transmission protection | direct: GRAF-T | Browser and each data-source transport |
| K: Secrets, certificates and key lifecycle | direct: GRAF-K | Service-account tokens and data-source credentials |
| L: Audit generation, retention, protection and collection health | direct: GRAF-L, ORG-L | Authentication, administrative and datasource monitoring |
| C: Secure configuration, change approval and drift | direct: GRAF-C, ORG-C | Snapshot sharing, plugins and version-specific settings |
| V: Vulnerabilities, patching, versions and software supply chain | direct: GRAF-V, ORG-V | Managed Grafana and enabled plugin lifecycle |
| B: Backup, recovery, restore tests and availability | direct: GRAF-B, ORG-B | Dashboard/configuration recovery and availability |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Workspace access does not automatically preserve data-source access restrictions; shared managed-identity queries and dashboard sharing need explicit review. |
| D: Detection, incident monitoring and response | shared: ORG-D | Workspace access does not automatically preserve data-source access restrictions; shared managed-identity queries and dashboard sharing need explicit review. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Workspace access does not automatically preserve data-source access restrictions; shared managed-identity queries and dashboard sharing need explicit review. |

## 19. Managed Prometheus (PROM)

**Resource/evidence boundary:** Microsoft.Monitor/accounts; DCR/DCE associations, AKS/Arc collectors, ruleGroups and Grafana links

**Current executable encryption maturity only:** Unsupported Azure Monitor workspace; not Log Analytics. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Ingestion and query have distinct endpoints/permissions/private paths; metric labels, collector completeness and 18-month service retention need explicit requirements review.

**Service sources:** [prometheus-workspace](https://learn.microsoft.com/en-us/azure/azure-monitor/metrics/azure-monitor-workspace-overview), [prometheus-private](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/private-link-azure-monitor-workspace), [prometheus-access](https://learn.microsoft.com/en-us/azure/azure-monitor/metrics/azure-monitor-workspace-manage-access), [prometheus-query](https://learn.microsoft.com/en-us/azure/azure-monitor/metrics/prometheus-resource-scoped-queries), [monitor-private](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/private-link-vm-kubernetes)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **PROM-I** Metrics ingestion and query scope (direct) | AC-3, AC-6, IA-9 | Workspace access-control mode, workspace/resource-context roles, DCR write/ingestion identities and Grafana identity grants. | Approved principals can ingest/query only intended resource populations; workspace mode and source-resource rights considered together. Apply domain I parameters. | ARM, AUTH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PROM-N** Ingestion versus query private connectivity (direct) | SC-7, AC-4 | Workspace public access/private endpoint target prometheusMetrics; DCE/DCR/AMPLS and collector links; approved client connectivity tests. | Both paths satisfy policy; the workspace query private endpoint alone is not evidence of private remote-write/configuration ingestion. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PROM-R** Azure Monitor workspace metric storage (direct) | SC-28, SC-28(1) | Exact Microsoft.Monitor/accounts identity and current workspace documentation stating Microsoft-managed at-rest encryption; export/source boundaries. | Use the Prometheus workspace guarantee, never a Log Analytics resource as a substitute; external copies assessed separately. Apply domain R parameters. | ARM, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PROM-T** Scrape, remote write and query paths (direct) | SC-8, SC-8(1) | Collector scrape scheme and TLS validation from reviewed configuration, remote-write/query endpoint TLS and workload client tests. | Required encryption covers workload-to-collector and collector-to-service hops; Azure query TLS does not imply every scrape target is encrypted. Apply domain T parameters. | K8S, PROCESS, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PROM-K** Scrape/remote-write identities and credential references (direct) | IA-5, IA-9 | Collector workload identity/role metadata and redacted scrape credential/certificate references, expiry/rotation tests. | Credentials and client trust follow policy; no Kubernetes secrets or unfiltered scrape configuration collected. Apply domain K parameters. | ARM, K8S, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PROM-L** Scrape coverage, ingestion loss and rule health (direct) | AU-5, SI-4 | Collector/DCR associations, expected scrape-target inventory, aggregate up/last-sample/ingestion errors, rule evaluation and alert delivery health. | Monitoring coverage and freshness meet approved criteria; time-series metrics are not a substitute for security audit logs of access/administrative actions. Apply domain L parameters. | ARM, K8S, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PROM-C** DCR, scrape, cardinality and label privacy baseline (direct) | CM-2, CM-3, CM-6, SI-12 | Approved DCR/rule groups and safe scrape/relabel metadata, cardinality controls, prohibited-label design tests and changes. | Collection rules match approved metrics with no sensitive/PII label data; review fixed service retention against requirements rather than inventing a retention toggle. Apply domain C parameters. | ARM, K8S, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PROM-V** Collector images and managed metrics platform (direct) | RA-5, SI-2, SA-22, SA-9 | Actual collector image/version and scan/support records; managed service update assurance and advisories. | Customer-deployed collectors/exporters supported/remediated; hosted metrics platform duties evidenced separately. Apply domain V parameters. | ARM, K8S, GUEST, PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **PROM-B** Metric continuity and monitoring rebuild (direct) | CP-2, CP-10, CP-4 | DCR/rules/collector/Grafana configuration backups, retention constraints, loss tolerance and tested regional/collector recovery. | Design meets acceptable metric-loss and restoration objectives; service retention is not a selectable independent backup/restore feature. Apply domain B parameters. | ARM, K8S, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: PROM-I, ORG-I | Metrics ingestion and query scope |
| N: Public exposure, resource restrictions and private connectivity | direct: PROM-N | Ingestion versus query private connectivity |
| R: Encryption and protection at rest | direct: PROM-R | Azure Monitor workspace metric storage |
| T: Transmission protection | direct: PROM-T | Scrape, remote write and query paths |
| K: Secrets, certificates and key lifecycle | direct: PROM-K | Scrape/remote-write identities and credential references |
| L: Audit generation, retention, protection and collection health | direct: PROM-L, ORG-L | Scrape coverage, ingestion loss and rule health |
| C: Secure configuration, change approval and drift | direct: PROM-C, ORG-C | DCR, scrape, cardinality and label privacy baseline |
| V: Vulnerabilities, patching, versions and software supply chain | direct: PROM-V, ORG-V | Collector images and managed metrics platform |
| B: Backup, recovery, restore tests and availability | direct: PROM-B, ORG-B | Metric continuity and monitoring rebuild |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Ingestion and query have distinct endpoints/permissions/private paths; metric labels, collector completeness and 18-month service retention need explicit requirements review. |
| D: Detection, incident monitoring and response | shared: ORG-D | Ingestion and query have distinct endpoints/permissions/private paths; metric labels, collector completeness and 18-month service retention need explicit requirements review. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Ingestion and query have distinct endpoints/permissions/private paths; metric labels, collector completeness and 18-month service retention need explicit requirements review. |

## 20. Log Analytics Workspaces (LA)

**Resource/evidence boundary:** Microsoft.OperationalInsights/workspaces; tables, dataExports, linked clusters, DCR/DCE and private-link associations

**Current executable encryption maturity only:** Supported scoped workspace data and saved-query encryption. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Workspace, resource-context and table query rights differ; audit generation at source, table retention, ingestion transformations and purge permissions need separate evidence.

**Service sources:** [azure-monitor-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/azure-monitor-security-baseline), [monitor-logs](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/best-practices-logs), [monitor-export](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-data-export), [monitor-private](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/private-link-vm-kubernetes)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **LA-I** Workspace, resource and table authorization (direct) | AC-3, AC-6, AU-9 | Workspace access-control mode, inherited/resource-context/table data roles, shared-key agent use and purge/delete permissions. | Query/write/delete rights fit approved duties; resource-scoped access and table permissions considered together; sensitive security tables have restricted access. Apply domain I parameters. | ARM, AUTH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **LA-N** Query, ingestion and export boundaries (direct) | SC-7, AC-4 | PublicNetworkAccessForIngestion/Query, AMPLS access modes, DCE/DCR associations and dataExports destination IDs. | Both ingestion/query and external exports match approved flow/location restrictions with shared network validation. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **LA-R** Workspace stored logs, queries and exports (direct) | SC-28, SC-28(1) | Workspace identity and service guarantee; optional dedicated-cluster/CMK links and every export destination. | Provider keys accepted for the workspace scope; optional CMK configuration is not confused with base encryption and exports are independently assessed. Apply domain R parameters. | ARM, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **LA-T** Agent, collection and query transport (direct) | SC-8, SC-8(1) | Agent/DCE transport design, TLS settings/version support, client query trust and network owner test records. | Approved encrypted transport covers custom collectors and all ingestion/query paths, including proxies. Apply domain T parameters. | ARM, GUEST, PROCESS, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **LA-K** Agent credentials and optional key lifecycle (direct) | IA-5, SC-12 | Managed identity versus legacy shared-key design, rotation/revocation records, optional cluster encryption key lifecycle. | Permitted agent/static credentials and optional keys follow lifecycle requirements; do not call workspace sharedKeys APIs. Apply domain K parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **LA-L** Table retention, query audit and ingestion health (direct) | AU-4, AU-5, AU-9, AU-11, AU-12 | tables retention/totalRetention/plan, LAQueryLogs configuration, daily cap, DCR destinations/transforms, export integrity and last-event/lag aggregates. | Every required dataset is retained/retrievable and protected from purge/unauthorized query; cap/transform/ingestion failures cause actionable alerts. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **LA-C** DCR transforms, tables and export change control (direct) | CM-2, CM-3, CM-6 | Approved tables/plans/transforms/exports, saved query/alert definitions and change approvals; redacted transformations reviewed by owner. | Changes preserve required audit content and privacy minimization; delete/retention changes and permission drift are reviewed. Apply domain C parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **LA-V** Agents, query clients and managed service (direct) | RA-5, SI-2, SA-22, SA-9 | AMA/collector/extension versions/health, migration/support evidence and provider platform assurance. | Customer collectors are current and healthy; extension installed or managed service status does not establish actual collection or patching. Apply domain V parameters. | ARM, GUEST, PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **LA-B** Retained evidence availability and export recovery (direct) | CP-9, CP-10, CP-4 | Workspace replication options if selected, supported export-table coverage, immutable copy requirements, protected config and retrieval/rebuild exercise. | Required audit history and monitoring can be restored/retrieved within limits; export covers supported new data only, not an automatic historical full backup. Apply domain B parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: LA-I, ORG-I | Workspace, resource and table authorization |
| N: Public exposure, resource restrictions and private connectivity | direct: LA-N | Query, ingestion and export boundaries |
| R: Encryption and protection at rest | direct: LA-R | Workspace stored logs, queries and exports |
| T: Transmission protection | direct: LA-T | Agent, collection and query transport |
| K: Secrets, certificates and key lifecycle | direct: LA-K | Agent credentials and optional key lifecycle |
| L: Audit generation, retention, protection and collection health | direct: LA-L, ORG-L | Table retention, query audit and ingestion health |
| C: Secure configuration, change approval and drift | direct: LA-C, ORG-C | DCR transforms, tables and export change control |
| V: Vulnerabilities, patching, versions and software supply chain | direct: LA-V, ORG-V | Agents, query clients and managed service |
| B: Backup, recovery, restore tests and availability | direct: LA-B, ORG-B | Retained evidence availability and export recovery |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Workspace, resource-context and table query rights differ; audit generation at source, table retention, ingestion transformations and purge permissions need separate evidence. |
| D: Detection, incident monitoring and response | shared: ORG-D | Workspace, resource-context and table query rights differ; audit generation at source, table retention, ingestion transformations and purge permissions need separate evidence. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Workspace, resource-context and table query rights differ; audit generation at source, table retention, ingestion transformations and purge permissions need separate evidence. |

## 21. Virtual Machines (VM)

**Resource/evidence boundary:** Microsoft.Compute/virtualMachines; disks/NICs/extensions/instanceView; guest OS, applications and remote stores

**Current executable encryption maturity only:** Partial host and declared disk metadata; guest/temp/remote stores incomplete. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Customer owns guest OS, installed software, local administration and data recovery; Microsoft host responsibilities do not include guest configuration.

**Service sources:** [virtual-machines-linux-virtual-machines-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/virtual-machines-linux-virtual-machines-security-baseline), [virtual-machines-windows-virtual-machines-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/virtual-machines-windows-virtual-machines-security-baseline), [vm-security](https://learn.microsoft.com/en-us/azure/virtual-machines/security-policy)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **VM-I** Azure administration and guest privileged access (direct) | AC-3, AC-6, AC-17, IA-2 | VM login roles/Entra extension configuration, local admin/sudo/SSH/RDP policy, managed identity scope and approved remote-access records. | Approved guest/control-plane administrators only, strong selected authentication and limited remote administration; ARM role list does not enumerate local accounts. Apply domain I parameters. | ARM, AUTH, GUEST, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VM-N** NIC exposure and host/service boundaries (direct) | SC-7, AC-4 | NIC/public IP/LB links, guest listening-service/firewall metadata and network-team effective NSG/routing evidence. | Required management/application paths restricted; no invented VM publicNetworkAccess switch; network team owns shared network changes. Apply domain N parameters. | ARM, GUEST, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VM-R** OS/data disks, cache/temp and remote mounts (direct) | SC-28, SC-28(1) | Disk encryption references, encryptionAtHost, ephemeral/temp/cache classification and guest mount/store inventory. | All in-scope data paths have scoped protection; managed-disk SSE alone is not proof for temporary disks, cache, guest exports or remote stores. Apply domain R parameters. | ARM, GUEST, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VM-T** Guest application and management encryption (direct) | SC-8, SC-8(1), SC-17 | SSH/RDP/TLS application configuration, certificates and endpoint/client validation tests. | Approved secure transport on each listening/outbound service; no inference from VM type or one TLS endpoint. Apply domain T parameters. | GUEST, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VM-K** Guest secrets, SSH keys and certificates (direct) | IA-5, SC-12, SC-17 | Metadata-only certificate/SSH key inventory, vault references and renewal/revocation/custody records. | Credentials are not embedded in images/scripts or broadly accessible; lifetimes/rotation meet approved requirements without reading key material. Apply domain K parameters. | GUEST, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VM-L** Guest security events, clocks and agent health (direct) | AU-2, AU-12, AU-5, SC-45 | OS audit policy and NTP configuration, AMA/DCR/EDR health, security/syslog event aggregates and routing/retention. | Selected guest events arrive with reliable timestamps; extension presence and Azure Activity Log alone are insufficient. Apply domain L parameters. | ARM, GUEST, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VM-C** Guest hardening, boot integrity and drift (direct) | CM-2, CM-3, CM-6, CM-7, SI-7 | SecurityProfile/boot controls where supported, machine configuration assessments, exposed services and baseline/change evidence. | Approved OS/boot/application baseline enforced for the VM generation/workload; unsupported features explicitly reviewed. Apply domain C parameters. | ARM, GUEST, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VM-V** Guest patching, malware defense and software support (direct) | RA-5, SI-2, SI-3, SA-22 | Actual patch assessments/install results, EDR signatures/health, OS/package/SBOM scans and image version/support records. | Complete fresh scan/patch/malware coverage and timely remediation; automatic-patch setting is not completed patch evidence. Apply domain V parameters. | ARM, GUEST, PROCESS, WIZ. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VM-B** Application-consistent backup and VM recovery (direct) | CP-9, CP-9(1), CP-10, CP-4 | Disk/app consistency and backup coverage, recovery points, availability zone/set design and tested restore with application checks. | Required guest and external state recovers within RPO/RTO; crash-consistent snapshot or host availability alone does not establish application recovery. Apply domain B parameters. | ARM, GUEST, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: VM-I, ORG-I | Azure administration and guest privileged access |
| N: Public exposure, resource restrictions and private connectivity | direct: VM-N | NIC exposure and host/service boundaries |
| R: Encryption and protection at rest | direct: VM-R | OS/data disks, cache/temp and remote mounts |
| T: Transmission protection | direct: VM-T | Guest application and management encryption |
| K: Secrets, certificates and key lifecycle | direct: VM-K | Guest secrets, SSH keys and certificates |
| L: Audit generation, retention, protection and collection health | direct: VM-L, ORG-L | Guest security events, clocks and agent health |
| C: Secure configuration, change approval and drift | direct: VM-C, ORG-C | Guest hardening, boot integrity and drift |
| V: Vulnerabilities, patching, versions and software supply chain | direct: VM-V, ORG-V | Guest patching, malware defense and software support |
| B: Backup, recovery, restore tests and availability | direct: VM-B, ORG-B | Application-consistent backup and VM recovery |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Customer owns guest OS, installed software, local administration and data recovery; Microsoft host responsibilities do not include guest configuration. |
| D: Detection, incident monitoring and response | shared: ORG-D | Customer owns guest OS, installed software, local administration and data recovery; Microsoft host responsibilities do not include guest configuration. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Customer owns guest OS, installed software, local administration and data recovery; Microsoft host responsibilities do not include guest configuration. |

## 22. Virtual Machine Scale Sets (VMSS)

**Resource/evidence boundary:** Microsoft.Compute/virtualMachineScaleSets; Uniform/Flexible instances, disks, NICs, images and applications

**Current executable encryption maturity only:** Partial scale-set model only; instance enumeration/drift incomplete. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Model and every live instance need reconciliation, including upgrade skew, ephemeral instances, image digests, stateful stores and capacity dependencies.

**Service sources:** [virtual-machine-scale-sets-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/virtual-machine-scale-sets-security-baseline), [vmss-upgrade](https://learn.microsoft.com/en-us/azure/virtual-machine-scale-sets/virtual-machine-scale-sets-upgrade-policy), [vm-security](https://learn.microsoft.com/en-us/azure/virtual-machines/security-policy)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **VMSS-I** Model and instance identity/administrator rights (direct) | AC-3, AC-6, AC-17, IA-2 | Scale-set/instance login roles and identities, guest admin policy and attached identity permissions across orchestration modes. | Approved rights on every instance, not only the model; guest and control-plane administration assessed separately. Apply domain I parameters. | ARM, AUTH, GUEST, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VMSS-N** Per-instance exposure and shared frontend (direct) | SC-7, AC-4 | NetworkProfile/model and actual NIC/public IP/LB references, guest listeners and network-owner effective path evidence. | All instances and frontend/backend paths match approved restrictions; newly scaled instances inherit verified policy. Apply domain N parameters. | ARM, GUEST, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VMSS-R** Model versus instance storage protection (direct) | SC-28, SC-28(1) | Model and instance encryptionAtHost/disk settings, actual attached/ephemeral/temp disks, remote mounts and discrepancy inventory. | Every relevant instance/store is covered; a compliant model cannot prove older instances adopted it or protect unknown temporary data. Apply domain R parameters. | ARM, GUEST, PROVIDER. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VMSS-T** Management, application and backend transport (direct) | SC-8, SC-8(1), SC-17 | Frontend termination and backend protocols, per-instance TLS/SSH/RDP and certificate rollout/validation evidence. | All required hops and instances enforce approved encryption; load-balancer TLS does not prove backend TLS. Apply domain T parameters. | GUEST, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VMSS-K** Image and instance credential lifecycle (direct) | IA-5, SC-12, SC-17 | Identity/vault references, image secret-scan results, per-instance certificate expiry and rotation/scale-out tests. | No baked-in reusable secrets; new and existing instances receive current credentials and revoke retired access. Apply domain K parameters. | ARM, GUEST, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VMSS-L** Instance audit coverage through scaling and upgrades (direct) | AU-2, AU-12, AU-5, SC-45 | Instance inventory joined to agent/DCR/EDR heartbeat, guest event/time policy and deletion/scaling change audit. | Every expected instance reports selected audit events; terminated/failed-to-onboard instances remain visible coverage gaps. Apply domain L parameters. | ARM, GUEST, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VMSS-C** Upgrade policy and instance-model drift (direct) | CM-2, CM-3, CM-6 | orchestrationMode, upgradePolicy, latestModelApplied/instance model metadata, health/rolling policy and deployment approvals. | Actual instances converge to approved model within allowed interval; manual/automatic/rolling policy selection alone is not convergence evidence. Apply domain C parameters. | ARM, GUEST, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VMSS-V** Image, OS and extension patch coverage (direct) | RA-5, SI-2, SI-3, SA-22 | Image version/digest, per-instance OS/package scans/patch results, automatic upgrade records and EDR health. | Complete actual-instance remediation and supported image lifecycle; rebuilt/scaled instances cannot silently reintroduce vulnerable images. Apply domain V parameters. | ARM, GUEST, PROCESS, WIZ. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **VMSS-B** Capacity rebuild and state recovery (direct) | CP-2, CP-9, CP-10, CP-4 | Orchestration-specific backup support, image/IaC versions, app external state, zones/capacity and recovery/rolling-failure exercises. | State and capacity recover within requirements; do not presume Uniform and Flexible have identical VM backup support or that stateless model covers all applications. Apply domain B parameters. | ARM, GUEST, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: VMSS-I, ORG-I | Model and instance identity/administrator rights |
| N: Public exposure, resource restrictions and private connectivity | direct: VMSS-N | Per-instance exposure and shared frontend |
| R: Encryption and protection at rest | direct: VMSS-R | Model versus instance storage protection |
| T: Transmission protection | direct: VMSS-T | Management, application and backend transport |
| K: Secrets, certificates and key lifecycle | direct: VMSS-K | Image and instance credential lifecycle |
| L: Audit generation, retention, protection and collection health | direct: VMSS-L, ORG-L | Instance audit coverage through scaling and upgrades |
| C: Secure configuration, change approval and drift | direct: VMSS-C, ORG-C | Upgrade policy and instance-model drift |
| V: Vulnerabilities, patching, versions and software supply chain | direct: VMSS-V, ORG-V | Image, OS and extension patch coverage |
| B: Backup, recovery, restore tests and availability | direct: VMSS-B, ORG-B | Capacity rebuild and state recovery |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Model and every live instance need reconciliation, including upgrade skew, ephemeral instances, image digests, stateful stores and capacity dependencies. |
| D: Detection, incident monitoring and response | shared: ORG-D | Model and every live instance need reconciliation, including upgrade skew, ephemeral instances, image digests, stateful stores and capacity dependencies. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Model and every live instance need reconciliation, including upgrade skew, ephemeral instances, image digests, stateful stores and capacity dependencies. |

## 23. Automation accounts (AUTO)

**Resource/evidence boundary:** Microsoft.Automation/automationAccounts; runbooks, runtimeEnvironments/modules, webhooks, jobs, assets and Hybrid Runbook Workers

**Current executable encryption maturity only:** Unsupported; no Automation detail/encryption rules. All other proposed checks below are discovery-only.

**Shared ownership and assessment context:** Runbook author/publisher/operator, account/worker identities, job payload confidentiality and Hybrid Worker host controls require separate assessment.

**Service sources:** [automation-baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/automation-security-baseline), [automation-data](https://learn.microsoft.com/en-us/azure/automation/automation-managing-data), [automation-encryption](https://learn.microsoft.com/en-us/azure/automation/automation-secure-asset-encryption)

| Check / domain / responsibility | Candidate NIST controls | Evidence to obtain | Candidate acceptance condition | Permissions / gap |
| --- | --- | --- | --- | --- |
| **AUTO-I** Runbook authoring, execution and runtime identity (direct) | AC-3, AC-5, AC-6, IA-9 | Account/worker identities, roles allowing edit/publish/start jobs or asset use, source control identity and approved operation roles. | Powerful runtime identity cannot be exercised by unapproved authors/operators; execution rights evaluated as potential credential/identity use. Apply domain I parameters. | ARM, AUTH, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AUTO-N** Account endpoints, webhooks and worker connectivity (direct) | SC-7, AC-4 | publicNetworkAccess/private endpoint support, webhook enabled/expiry metadata without URLs, worker location and approved outbound dependencies. | Each account/webhook/worker path meets approved boundary; private account configuration does not imply every webhook or hybrid dependency is private. Apply domain N parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AUTO-R** Secure assets, code and job/output stores (direct) | SC-28, SC-28(1) | Account encryption identity/optional key metadata, documented secure-asset/runbook coverage and job/export/log-store classification. | Provider-managed encryption accepted for documented scopes; plaintext variables, output streams and exported scripts require explicit handling and redaction evidence. Apply domain R parameters. | ARM, PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AUTO-T** Worker, webhook and runbook outbound transport (direct) | SC-8, SC-8(1) | Worker TLS/runtime metadata and runbook endpoint/validation review; approved webhook client transport tests. | All required paths use approved encryption/validation; account TLS does not prove arbitrary runbook outbound protocol safety. Apply domain T parameters. | ARM, GUEST, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AUTO-K** Automation assets, webhook tokens and certificate expiry (direct) | IA-5, SC-12, SC-17 | Asset type/name/encrypted flag/expiry metadata from safe exports, vault references and rotation/revocation records. | Sensitive variables are protected and credentials rotate; never retrieve asset values, webhook URLs, private certificates or secret-bearing job output. Apply domain K parameters. | ARM, DATA, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AUTO-L** Job status, administrative changes and audit delivery (direct) | AU-2, AU-12, AU-5 | Diagnostic JobLogs/JobStreams configuration and safe job status aggregates, change actors and destination/receipt/retention. | Job failures and privileged operations monitored; output redacted before archival because streams may contain secrets and personal data. Apply domain L parameters. | ARM, LOG, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AUTO-C** Published code, source control and execution changes (direct) | CM-2, CM-3, CM-5, CM-6 | Runbook draft/published revision/hash metadata, runtime/module/source-control configuration and approval/test/rollback records. | Only approved tested runbooks and dependencies execute; no raw script or source-control token retrieval required for inventory. Apply domain C parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AUTO-V** Runtime, modules and Hybrid Worker hosts (direct) | RA-5, SI-2, SA-22, SR-4 | RuntimeEnvironment/module versions and provenance, extension-based Hybrid Worker version/OS/scan/patch reports and retirement notices. | Supported worker/runtime/modules and remediated host vulnerabilities; provider service maintenance does not patch hybrid hosts or customer modules. Apply domain V parameters. | ARM, GUEST, PROVIDER, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |
| **AUTO-B** Account rebuild and protected asset reconstitution (direct) | CP-9, CP-10, CP-4 | Versioned runbook/config/module sources, protected asset reissuance plan, worker recreation and tested execution recovery. | Rebuild meets RTO and safely reestablishes identities/assets; Automation has no general native backup, so a documented tested alternative is required. Apply domain B parameters. | ARM, PROCESS. No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation. |

**Coverage and shared evidence:**

| Domain | Disposition / evidence references | Boundary rationale |
| --- | --- | --- |
| I: Identity, authentication, authorization and privileged access | direct: AUTO-I, ORG-I | Runbook authoring, execution and runtime identity |
| N: Public exposure, resource restrictions and private connectivity | direct: AUTO-N | Account endpoints, webhooks and worker connectivity |
| R: Encryption and protection at rest | direct: AUTO-R | Secure assets, code and job/output stores |
| T: Transmission protection | direct: AUTO-T | Worker, webhook and runbook outbound transport |
| K: Secrets, certificates and key lifecycle | direct: AUTO-K | Automation assets, webhook tokens and certificate expiry |
| L: Audit generation, retention, protection and collection health | direct: AUTO-L, ORG-L | Job status, administrative changes and audit delivery |
| C: Secure configuration, change approval and drift | direct: AUTO-C, ORG-C | Published code, source control and execution changes |
| V: Vulnerabilities, patching, versions and software supply chain | direct: AUTO-V, ORG-V | Runtime, modules and Hybrid Worker hosts |
| B: Backup, recovery, restore tests and availability | direct: AUTO-B, ORG-B | Account rebuild and protected asset reconstitution |
| O: Inventory, ownership and lifecycle | shared: ORG-O | Runbook author/publisher/operator, account/worker identities, job payload confidentiality and Hybrid Worker host controls require separate assessment. |
| D: Detection, incident monitoring and response | shared: ORG-D | Runbook author/publisher/operator, account/worker identities, job payload confidentiality and Hybrid Worker host controls require separate assessment. |
| G: Governance, access review, exceptions, privacy and shared controls | shared: ORG-G, ORG-P, ORG-H, ORG-S, ORG-M, ORG-A, ORG-I | Runbook author/publisher/operator, account/worker identities, job payload confidentiality and Hybrid Worker host controls require separate assessment. |
