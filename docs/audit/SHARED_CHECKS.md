# Shared and organizational evidence checks

These records are explicitly referenced by service/domain rows. Their applicability, owner and scope require approval; metadata does not prove their operation. All are discovery-only. See [method and permissions](METHOD.md).

### ORG-I: Effective access and privileged human access

**Domain:** I · **Responsibility:** shared · **Owner:** Named organization/control owner; service owner supplies scoped population and operating samples

**Evidence:** ARM inherited/conditional/deny role assignments, PIM records, tenant policies and sampled sign-ins; group/guest resolution; approved access register and completed review/removal tickets.

**Candidate acceptance:** Approved effective rights, MFA/elevation and break-glass controls operate for the selected populations; review decisions and removals are timely. Tenant policy presence alone is not enforcement evidence.

**Permissions / evidence planes:** AUTH, GRAPH, GAUDIT, PROCESS (definitions in [METHOD.md](METHOD.md)). **Parameters:** I.

**NIST mapping and limit:** **AC-2** — Manage authorization lifecycle, including disabled/deleted/stale accounts; a list is only the starting population. **AC-3** — Verify that the actual service/data plane enforces the approved authorization decision. **AC-5** — Separate incompatible approval, administration, key and audit duties. **AC-6** — Compare effective permissions with the approved business need and minimum scope. **AC-6(7)** — Review user privileges and remove or reassign unnecessary rights; require review outcomes. **IA-2** — Identify/authenticate human organizational users through tenant and workload controls. **IA-2(1)** — Require the selected MFA mechanism for privileged accounts; machine identities are assessed separately. **IA-8** — Assess external/guest user authentication where those users are allowed. Supports this check boundary only; no whole-control conclusion.

**800-53A references:** ac-2_obj, ac-3_obj, ac-5_obj, ac-6_obj, ac-6.7_obj, ia-2_obj, ia-2.1_obj, ia-8_obj. Official EXAMINE/INTERVIEW/TEST method/object records are in [the control index](nist-control-index.json); method selection and depth/coverage remain assessor decisions.

**Automation / maturity:** Deterministic metadata comparison plus owner review; operating/test evidence remains separate. DISCOVERY_ONLY; no executable check added

**Gap:** No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation.

**Sources:** [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)

### ORG-O: Inventory, ownership and information location

**Domain:** O · **Responsibility:** shared · **Owner:** Named organization/control owner; service owner supplies scoped population and operating samples

**Evidence:** Authorized scope register plus complete ARM/Graph/Kubernetes populations; provider/type/SKU/region, lifecycle, owner, classification, dependency edges and reconciled IaC/CMDB records.

**Candidate acceptance:** Every owned resource/object and required child/dependency has an accountable owner and classification; inventory gaps are reconciled. Missing tags are one signal, not proof of unknown ownership.

**Permissions / evidence planes:** ARM, GRAPH, K8S, PROCESS (definitions in [METHOD.md](METHOD.md)). **Parameters:** O.

**NIST mapping and limit:** **CM-8** — Reconcile a complete owned component/dependency inventory and lifecycle. **CM-12** — Locate and classify information across stores, regions and external destinations. **RA-2** — Categorize the system and information to drive risk-based control selection. **RA-9** — Determine critical components and dependencies that drive recovery and prioritization. Supports this check boundary only; no whole-control conclusion.

**800-53A references:** cm-8_obj, cm-12_obj, ra-2_obj, ra-9_obj. Official EXAMINE/INTERVIEW/TEST method/object records are in [the control index](nist-control-index.json); method selection and depth/coverage remain assessor decisions.

**Automation / maturity:** Deterministic metadata comparison plus owner review; operating/test evidence remains separate. DISCOVERY_ONLY; no executable check added

**Gap:** No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation.

**Sources:** [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)

### ORG-L: Audit retention, integrity and collection health

**Domain:** L · **Responsibility:** shared · **Owner:** Named organization/control owner; service owner supplies scoped population and operating samples

**Evidence:** Event category requirements; source-to-destination settings; table retention/export/immutability and reader/purge rights; aggregate latest event/time-lag/capacity; collector failures and recovery records.

**Candidate acceptance:** Required events arrive with identity/action/target/time/outcome, remain protected/retrievable for approved retention, and monitored failures trigger correction. Activity Log is not all data-plane audit.

**Permissions / evidence planes:** ARM, AUTH, LOG, PROCESS (definitions in [METHOD.md](METHOD.md)). **Parameters:** L.

**NIST mapping and limit:** **AU-2** — Select and justify the security-relevant events that must be logged. **AU-3** — Confirm records contain the approved identity, action, target, time and outcome fields. **AU-4** — Size and monitor audit storage capacity to prevent loss. **AU-5** — Detect and respond to failed collection, ingestion gaps or unavailable audit destinations. **AU-8** — Ensure audit timestamps support event ordering and correlation. **AU-9** — Protect audit records and audit tooling from unauthorized read, change and deletion. **AU-11** — Retain the required audit records for the organization-defined interval. **AU-12** — Generate the required audit events at the service and workload boundaries. **SC-45** — Verify selected system clock synchronization; do not infer guest time from Azure host time. Supports this check boundary only; no whole-control conclusion.

**800-53A references:** au-2_obj, au-3_obj, au-4_obj, au-5_obj, au-8_obj, au-9_obj, au-11_obj, au-12_obj, sc-45_obj. Official EXAMINE/INTERVIEW/TEST method/object records are in [the control index](nist-control-index.json); method selection and depth/coverage remain assessor decisions.

**Automation / maturity:** Deterministic metadata comparison plus owner review; operating/test evidence remains separate. DISCOVERY_ONLY; no executable check added

**Gap:** No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation.

**Sources:** [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)

### ORG-C: Approved change and configuration baseline

**Domain:** C · **Responsibility:** shared · **Owner:** Named organization/control owner; service owner supplies scoped population and operating samples

**Evidence:** Versioned approved IaC/configuration, policy assignment/effect/exemption and latest evaluation, change/approval/build records, Activity Log metadata, drift comparisons and emergency change samples.

**Candidate acceptance:** Observed settings match approved baseline or current owner-approved exceptions; changes have impact analysis and tested rollback. Policy compliance alone does not prove all resources or process performance.

**Permissions / evidence planes:** ARM, AUTH, PROCESS (definitions in [METHOD.md](METHOD.md)). **Parameters:** C.

**NIST mapping and limit:** **CM-2** — Establish a versioned, approved service/workload configuration baseline. **CM-3** — Link changes to approval, validation, rollout and recovery records. **CM-4** — Assess security/privacy impact before relevant changes. **CM-5** — Restrict who or what can change the configuration or deployed workload. **CM-6** — Compare observed security settings against the tailored approved configuration. Supports this check boundary only; no whole-control conclusion.

**800-53A references:** cm-2_obj, cm-3_obj, cm-4_obj, cm-5_obj, cm-6_obj. Official EXAMINE/INTERVIEW/TEST method/object records are in [the control index](nist-control-index.json); method selection and depth/coverage remain assessor decisions.

**Automation / maturity:** Deterministic metadata comparison plus owner review; operating/test evidence remains separate. DISCOVERY_ONLY; no executable check added

**Gap:** No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation.

**Sources:** [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)

### ORG-V: Vulnerability evidence and remediation accountability

**Domain:** V · **Responsibility:** shared · **Owner:** Named organization/control owner; service owner supplies scoped population and operating samples

**Evidence:** Authoritative software/image inventory; direct scanner or optional Wiz/Defender reports with coverage, age, digest/host, severity; remediation tickets, retest and unsupported-version exceptions.

**Candidate acceptance:** Required assets scanned within approved windows; vulnerabilities and unsupported components remediated or risk accepted before deadlines; exclusions and unavailable scans remain explicit. Root-cause analysis only for selected flaws.

**Permissions / evidence planes:** ARM, GUEST, PROCESS, WIZ (definitions in [METHOD.md](METHOD.md)). **Parameters:** V.

**NIST mapping and limit:** **RA-5** — Establish current scanning/monitoring scope and analyze vulnerability results. **SI-2** — Track tested flaw remediation to completion against approved deadlines. **SI-2(7)** — Investigate causes of selected flaws to prevent recurrence; a closed scanner finding is insufficient. **SI-5** — Receive, evaluate and act on relevant advisories. **SA-22** — Replace unsupported components or document approved alternatives and risk treatment. Supports this check boundary only; no whole-control conclusion.

**800-53A references:** ra-5_obj, si-2_obj, si-2.7_obj, si-5_obj, sa-22_obj. Official EXAMINE/INTERVIEW/TEST method/object records are in [the control index](nist-control-index.json); method selection and depth/coverage remain assessor decisions.

**Automation / maturity:** Deterministic metadata comparison plus owner review; operating/test evidence remains separate. DISCOVERY_ONLY; no executable check added

**Gap:** No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation.

**Sources:** [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)

### ORG-B: Recovery requirements and demonstrated restore

**Domain:** B · **Responsibility:** shared · **Owner:** Named organization/control owner; service owner supplies scoped population and operating samples

**Evidence:** BIA, dependency/runbook inventory, backup jobs/recovery points, integrity results and authorized restoration/failover exercise reports with measured RPO/RTO and application validation.

**Candidate acceptance:** Selected backup/rebuild strategy meets approved data-loss and outage limits; recovery tests succeed and defects close. Replication, retention and successful backup jobs do not prove recoverability.

**Permissions / evidence planes:** ARM, PROCESS (definitions in [METHOD.md](METHOD.md)). **Parameters:** B.

**NIST mapping and limit:** **CP-2** — Maintain a dependency-aware contingency plan with assigned recovery roles. **CP-4** — Exercise recovery against explicit success criteria and remediate deficiencies. **CP-6** — Provide an alternate storage arrangement when the selected recovery design requires it. **CP-7** — Provide an alternate processing arrangement when availability requirements require it. **CP-9** — Back up the required data, system state and documentation, and protect the backup. **CP-9(1)** — Test backup reliability and integrity rather than relying on a success flag alone. **CP-10** — Demonstrate controlled recovery and reconstitution to the defined service state. Supports this check boundary only; no whole-control conclusion.

**800-53A references:** cp-2_obj, cp-4_obj, cp-6_obj, cp-7_obj, cp-9_obj, cp-9.1_obj, cp-10_obj. Official EXAMINE/INTERVIEW/TEST method/object records are in [the control index](nist-control-index.json); method selection and depth/coverage remain assessor decisions.

**Automation / maturity:** Deterministic metadata comparison plus owner review; operating/test evidence remains separate. DISCOVERY_ONLY; no executable check added

**Gap:** No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation.

**Sources:** [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)

### ORG-D: Security detection and incident response

**Domain:** D · **Responsibility:** shared · **Owner:** Named organization/control owner; service owner supplies scoped population and operating samples

**Evidence:** Service threat scenarios; alert/rule/action-group configuration, agent/ingestion health, sampled alerts and investigations, incident tickets, notification and authorized exercise results.

**Candidate acceptance:** Approved detections reach accountable responders within agreed times; triage, containment, evidence preservation and recovery are demonstrated. An enabled Defender/Wiz plan is not operational effectiveness.

**Permissions / evidence planes:** ARM, LOG, PROCESS, WIZ (definitions in [METHOD.md](METHOD.md)). **Parameters:** D.

**NIST mapping and limit:** **AU-6** — Review/analyze events and act on findings; collection enabled is insufficient. **SI-4** — Detect suspicious activity with monitored and tested coverage, not only an enabled plan. **IR-3** — Test the incident response capability and record corrections. **IR-4** — Handle incidents through detection, analysis, containment, eradication and recovery. **IR-5** — Track and document incidents and relevant monitoring activity. **IR-6** — Report incidents to required recipients within approved time limits. **IR-8** — Maintain and exercise an approved response plan for the system. Supports this check boundary only; no whole-control conclusion.

**800-53A references:** au-6_obj, si-4_obj, ir-3_obj, ir-4_obj, ir-5_obj, ir-6_obj, ir-8_obj. Official EXAMINE/INTERVIEW/TEST method/object records are in [the control index](nist-control-index.json); method selection and depth/coverage remain assessor decisions.

**Automation / maturity:** Deterministic metadata comparison plus owner review; operating/test evidence remains separate. DISCOVERY_ONLY; no executable check added

**Gap:** No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation.

**Sources:** [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)

### ORG-G: Tailoring, risk, authorization and continuous assessment

**Domain:** G · **Responsibility:** shared · **Owner:** Named organization/control owner; service owner supplies scoped population and operating samples

**Evidence:** System boundary/architecture/data flows, selected baseline and RCSA, named control owners, assessment plan with depth/coverage, authorization decisions, risk register, POA&M and expiring exceptions.

**Candidate acceptance:** Responsible stakeholders approve applicability, parameters, inheritance and assessment scope; unresolved risks and stale evidence remain visible; exceptions have authority, scope, compensating measures and expiry.

**Permissions / evidence planes:** PROCESS (definitions in [METHOD.md](METHOD.md)). **Parameters:** G.

**NIST mapping and limit:** **PL-2** — Examine the system security and privacy plans responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PL-8** — Examine the security and privacy architectures responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PL-10** — Examine the baseline selection responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PL-11** — Examine the baseline tailoring responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PM-1** — Examine the information security program plan responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PM-5** — Examine the system inventory responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PM-9** — Examine the risk management strategy responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PM-31** — Examine the continuous monitoring strategy responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **CA-2** — Examine the control assessments responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **CA-3** — Examine the information exchange responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **CA-5** — Examine the plan of action and milestones responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **CA-6** — Examine the authorization responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **CA-7** — Examine the continuous monitoring responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **RA-3** — Assess threats, vulnerabilities, likelihood, impact and residual risk. **RA-7** — Track an approved response to identified risks, including time-bound acceptance. Supports this check boundary only; no whole-control conclusion.

**800-53A references:** pl-2_obj, pl-8_obj, pl-10_obj, pl-11_obj, pm-1_obj, pm-5_obj, pm-9_obj, pm-31_obj, ca-2_obj, ca-3_obj, ca-5_obj, ca-6_obj, ca-7_obj, ra-3_obj, ra-7_obj. Official EXAMINE/INTERVIEW/TEST method/object records are in [the control index](nist-control-index.json); method selection and depth/coverage remain assessor decisions.

**Automation / maturity:** Deterministic metadata comparison plus owner review; operating/test evidence remains separate. DISCOVERY_ONLY; no executable check added

**Gap:** No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation.

**Sources:** [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)

### ORG-P: Privacy, retention and information lifecycle

**Domain:** G · **Responsibility:** shared · **Owner:** Named organization/control owner; service owner supplies scoped population and operating samples

**Evidence:** Data map/classification, processing authority/purpose, consent and notices where required, privacy impact assessment, minimization/redaction tests, retention/deletion evidence and cross-region/vendor disclosures.

**Candidate acceptance:** Data collection/use/retention matches approved purpose and privacy obligations; no blanket PII exclusion for telemetry, logs, identifiers, cache data or app metadata. Apply legal-specific controls only after privacy review.

**Permissions / evidence planes:** PROCESS, DATA (definitions in [METHOD.md](METHOD.md)). **Parameters:** G.

**NIST mapping and limit:** **PM-18** — Examine the privacy program plan responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PM-23** — Examine the data governance body responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PT-2** — Examine the authority to process personally identifiable information responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PT-3** — Examine the personally identifiable information processing purposes responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PT-4** — Examine the consent responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PT-5** — Examine the privacy notice responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PT-7** — Examine the specific categories of personally identifiable information responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **RA-8** — Assess privacy impact where personal information is processed. **SI-12** — Retain and dispose of information in accordance with approved requirements. Supports this check boundary only; no whole-control conclusion.

**800-53A references:** pm-18_obj, pm-23_obj, pt-2_obj, pt-3_obj, pt-4_obj, pt-5_obj, pt-7_obj, ra-8_obj, si-12_obj. Official EXAMINE/INTERVIEW/TEST method/object records are in [the control index](nist-control-index.json); method selection and depth/coverage remain assessor decisions.

**Automation / maturity:** Deterministic metadata comparison plus owner review; operating/test evidence remains separate. DISCOVERY_ONLY; no executable check added

**Gap:** No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation.

**Sources:** [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)

### ORG-H: People, training and access lifecycle

**Domain:** G · **Responsibility:** shared · **Owner:** Named organization/control owner; service owner supplies scoped population and operating samples

**Evidence:** Role training/completion records; HR/security-controlled screening and access agreements; termination/transfer samples correlated to access revocations; third-party staff assurances.

**Candidate acceptance:** Personnel and privileged roles meet selected training, screening and access-lifecycle requirements; minimize personal data in audit copies. Resource metadata cannot establish these controls.

**Permissions / evidence planes:** PROCESS (definitions in [METHOD.md](METHOD.md)). **Parameters:** G.

**NIST mapping and limit:** **AT-2** — Examine the literacy training and awareness responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **AT-3** — Examine the role-based training responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **AT-4** — Examine the training records responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PS-2** — Examine the position risk designation responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PS-3** — Examine the personnel screening responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PS-4** — Examine the personnel termination responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PS-5** — Examine the personnel transfer responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PS-6** — Examine the access agreements responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PS-7** — Examine the external personnel security responsibilities relevant to this stated evidence boundary; require the control owner's assessment. Supports this check boundary only; no whole-control conclusion.

**800-53A references:** at-2_obj, at-3_obj, at-4_obj, ps-2_obj, ps-3_obj, ps-4_obj, ps-5_obj, ps-6_obj, ps-7_obj. Official EXAMINE/INTERVIEW/TEST method/object records are in [the control index](nist-control-index.json); method selection and depth/coverage remain assessor decisions.

**Automation / maturity:** Deterministic metadata comparison plus owner review; operating/test evidence remains separate. DISCOVERY_ONLY; no executable check added

**Gap:** No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation.

**Sources:** [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)

### ORG-S: Provider assurance, procurement and software suppliers

**Domain:** G · **Responsibility:** shared · **Owner:** Named organization/control owner; service owner supplies scoped population and operating samples

**Evidence:** Contracts, supplier inventories, responsibility matrix, current scoped assurance reports/bridge letters, exceptions, software provenance/SBOM and supplier notification agreements.

**Candidate acceptance:** Inherited claims match the service/tier/region and report period, customer responsibilities are assigned and supplier risks tracked. Public marketing/certification labels alone do not establish operating effectiveness.

**Permissions / evidence planes:** PROCESS, PROVIDER (definitions in [METHOD.md](METHOD.md)). **Parameters:** G.

**NIST mapping and limit:** **SA-4** — Examine the acquisition process responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **SA-9** — Obtain and evaluate assurance for externally provided system services. **SR-2** — Examine the supply chain risk management plan responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **SR-3** — Examine the supply chain controls and processes responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **SR-4** — Maintain software/component provenance from producer to deployed artifact. **SR-6** — Periodically assess suppliers and act on assurance limitations. **SR-8** — Examine the notification agreements responsibilities relevant to this stated evidence boundary; require the control owner's assessment. Supports this check boundary only; no whole-control conclusion.

**800-53A references:** sa-4_obj, sa-9_obj, sr-2_obj, sr-3_obj, sr-4_obj, sr-6_obj, sr-8_obj. Official EXAMINE/INTERVIEW/TEST method/object records are in [the control index](nist-control-index.json); method selection and depth/coverage remain assessor decisions.

**Automation / maturity:** Deterministic metadata comparison plus owner review; operating/test evidence remains separate. DISCOVERY_ONLY; no executable check added

**Gap:** No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation.

**Sources:** [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)

### ORG-M: Maintenance, media and physical dependencies

**Domain:** G · **Responsibility:** shared · **Owner:** Named organization/control owner; service owner supplies scoped population and operating samples

**Evidence:** Microsoft datacenter assurance scope; support-access authorization, maintenance records, on-prem/hybrid worker controls, backup/export handling and media disposal assurances.

**Candidate acceptance:** Provider physical/host duties are evidenced and inherited only within their boundary; customer hybrid infrastructure, admin workstations, exported data and support access remain assigned.

**Permissions / evidence planes:** PROCESS, PROVIDER (definitions in [METHOD.md](METHOD.md)). **Parameters:** G.

**NIST mapping and limit:** **MA-2** — Examine the controlled maintenance responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **MA-4** — Examine the nonlocal maintenance responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **MA-5** — Examine the maintenance personnel responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **MP-2** — Examine the media access responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **MP-4** — Examine the media storage responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **MP-5** — Examine the media transport responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **MP-6** — Examine the media sanitization responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PE-2** — Examine the physical access authorizations responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PE-3** — Examine the physical access control responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PE-6** — Examine the monitoring physical access responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PE-11** — Examine the emergency power responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PE-13** — Examine the fire protection responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PE-14** — Examine the environmental controls responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PE-16** — Examine the delivery and removal responsibilities relevant to this stated evidence boundary; require the control owner's assessment. **PE-17** — Examine the alternate work site responsibilities relevant to this stated evidence boundary; require the control owner's assessment. Supports this check boundary only; no whole-control conclusion.

**800-53A references:** ma-2_obj, ma-4_obj, ma-5_obj, mp-2_obj, mp-4_obj, mp-5_obj, mp-6_obj, pe-2_obj, pe-3_obj, pe-6_obj, pe-11_obj, pe-13_obj, pe-14_obj, pe-16_obj, pe-17_obj. Official EXAMINE/INTERVIEW/TEST method/object records are in [the control index](nist-control-index.json); method selection and depth/coverage remain assessor decisions.

**Automation / maturity:** Deterministic metadata comparison plus owner review; operating/test evidence remains separate. DISCOVERY_ONLY; no executable check added

**Gap:** No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation.

**Sources:** [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)

### ORG-A: Customer application security and resiliency

**Domain:** G · **Responsibility:** shared · **Owner:** Named organization/control owner; service owner supplies scoped population and operating samples

**Evidence:** Threat models, code/dependency/configuration reviews, CI security tests, signed artifact/provenance records, input/error/logging tests and critical-workload resiliency design review.

**Candidate acceptance:** Customer-created code and pipelines meet selected secure-development requirements and have operating test evidence; SA-15(13)/SA-24 require explicit selection, not automatic new mandates.

**Permissions / evidence planes:** PROCESS, GUEST (definitions in [METHOD.md](METHOD.md)). **Parameters:** G.

**NIST mapping and limit:** **SA-10** — Maintain developer configuration/version and change records. **SA-11** — Test developed code and security behavior; configuration scans are insufficient. **SA-15** — Assess the development process and tools for customer software. **SA-15(13)** — Define machine-consumable logging syntax for developed components, if this enhancement is selected. **SA-24** — Evaluate cyber-resilient design for critical customer-developed systems, if selected. **SI-7** — Verify executable/configuration integrity and investigate unexpected changes. **SI-10** — Validate inputs at application, event or configuration trust boundaries. **SI-11** — Handle errors without disclosing sensitive implementation or customer data. Supports this check boundary only; no whole-control conclusion.

**800-53A references:** sa-10_obj, sa-11_obj, sa-15_obj, sa-15.13_obj, sa-24_obj, si-7_obj, si-10_obj, si-11_obj. Official EXAMINE/INTERVIEW/TEST method/object records are in [the control index](nist-control-index.json); method selection and depth/coverage remain assessor decisions.

**Automation / maturity:** Deterministic metadata comparison plus owner review; operating/test evidence remains separate. DISCOVERY_ONLY; no executable check added

**Gap:** No adapter for this proposed check; validate exact API/version, safe fields, permissions and coverage before implementation.

**Sources:** [nist-oscal](https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json), [mcsb](https://learn.microsoft.com/en-us/security/benchmark/azure/), [rbac](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions), [nist53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [nist53a](https://csrc.nist.gov/pubs/sp/800/53/a/r5/final)
