# Azure Policy as an evidence source

Azure Policy supplies provider-defined configuration evaluations and NIST SP 800-53 Rev. 5 mappings. This program reads all returned states as **provider-asserted evidence**. The intended architecture uses direct predicates for identified gaps; the current collector still runs direct collection before adding Policy. See the [current checkpoint](HOME_LAB_BUILD_STATUS.md).

Collection uses Policy Insights directly and does not depend on the Defender for Cloud dashboard. The assignment procedure below records the reviewed lab configuration; assess the actual initiative version, effects and existing assignments before adapting it to work.

## What the initiative contains

Built-in initiative `179d1daa-458f-4e47-8086-2a68d0d6c38f`, **NIST SP 800-53 Rev. 5**, reviewed 2026-09-20:

| Resolved effect | Definitions |
| --- | --- |
| `Manual` | 481 |
| `AuditIfNotExists` | 96 |
| `Audit` | 112 |
| `modify` | 2 |
| `deployIfNotExists` | 2 |
| **Total** | **693** |

The 481 `Manual` definitions are attestation placeholders for organizational controls. They confirm the same finding this program reached independently: most of SP 800-53 is not observable from a resource API and closes through attributed records. Policy's `Manual` effect holds an attestation; it is not automated evidence.

## Assignment posture

This is an **assessment-only** assignment. Three independent barriers prevent it from changing anything:

1. `--enforcement-mode DoNotEnforce` — no effect is enforced; compliance is still evaluated and reported.
2. An `overrides` block forces the only four definitions that could alter resources to `Disabled`.
3. The assignment's managed identity is granted **no roles**, so remediation cannot execute even if it were triggered.

The four overridden definitions are all Guest Configuration enablement:

| Reference ID | Effect | What it would otherwise do |
| --- | --- | --- |
| `3cf2ab00-13f1-4d0c-8971-2ac904541a7e` | modify | Add a system-assigned identity to VMs with no identity |
| `497dff13-db2a-4c0f-8603-28fa3b331ab6` | modify | Add a system-assigned identity to VMs with a user-assigned identity |
| `385f5831-96d4-41db-9a3c-cd3af78aaae6` | deployIfNotExists | Deploy the Windows Guest Configuration extension |
| `331e8ea8-378a-410f-a2e5-ae22f38bb0da` | deployIfNotExists | Deploy the Linux Guest Configuration extension |

These have no `effect` parameter, so they cannot be neutralized through assignment parameters — the override selector is the supported mechanism.

Azure rejects an assignment that *contains* `Modify` or `DeployIfNotExists` definitions unless a managed identity is attached, even when enforcement is disabled and those definitions are overridden. The identity therefore exists for validation only. Confirm it stays inert:

```sh
az role assignment list --assignee <assignment principalId> --all -o table   # must return nothing
```

## Creating the assignment

Scope deliberately: this account holds Owner at the tenant root and on a `PROD` management group. Assign at the narrowest scope that covers the resources under assessment, never at root by default.

```sh
cat > overrides.json <<'JSON'
[
  {
    "kind": "policyEffect",
    "value": "Disabled",
    "selectors": [
      {
        "kind": "policyDefinitionReferenceId",
        "in": [
          "3cf2ab00-13f1-4d0c-8971-2ac904541a7e",
          "497dff13-db2a-4c0f-8603-28fa3b331ab6",
          "385f5831-96d4-41db-9a3c-cd3af78aaae6",
          "331e8ea8-378a-410f-a2e5-ae22f38bb0da"
        ]
      }
    ]
  }
]
JSON

az policy assignment create \
  --name nist-800-53-r5-audit \
  --display-name "NIST SP 800-53 Rev. 5 (audit-only, evidence collection)" \
  --policy-set-definition 179d1daa-458f-4e47-8086-2a68d0d6c38f \
  --scope /subscriptions/<SUBSCRIPTION_ID> \
  --enforcement-mode DoNotEnforce \
  --overrides @overrides.json \
  --mi-system-assigned --location <REGION>
```

Then verify the posture before trusting any result from it:

```sh
az policy assignment show --name nist-800-53-r5-audit --scope /subscriptions/<SUBSCRIPTION_ID> \
  --query "{enforcement:enforcementMode, overrides:length(overrides), identity:identity.type}"
az policy state trigger-scan --subscription <SUBSCRIPTION_ID> --no-wait
```

Initial evaluation is not immediate; a triggered scan still takes time to populate, and Policy re-evaluates on its own cycle afterwards.

## Removing it

```sh
az policy assignment delete --name nist-800-53-r5-audit --scope /subscriptions/<SUBSCRIPTION_ID>
```

Deleting the assignment removes the identity with it. Because the identity never held a role and enforcement was disabled, nothing needs to be unwound.

## Reading the results as evidence

Compliance state is read from Policy Insights. Azure registers `policyStates/latest/queryResults` for **POST only** — a GET against the same URL returns `ResourceTypeNotSupported`, because the query specification travels in a request body. The call changes nothing, but the verb is POST, so it lives in `policy_query.py` rather than the GET-only resource collector: one allowlisted path, one pinned API version, an empty request body and the same response bounding as every resource read. The assignment and its initiative are ordinary GETs.

Policy evaluates at three scopes and all three are retained and labelled: `resource`, `resource_group` and `subscription`. In a real tenant most records are subscription scoped — 499 of 531 in the first lab run — so discarding them would throw away most of the evidence. A scoped result describes that scope, never each resource inside it, and the register records the mix. Results enter this program as a distinct evidence kind alongside the encryption rules, the scoped predicates and attributed records, and they are labelled as provider-asserted throughout.

Two boundaries apply and are preserved in the register:

- **The control mapping is Microsoft's, not yours.** A definition's association with a control is Microsoft's interpretation. It is supporting evidence, not your tailoring decision, and it never becomes an assessor determination.
- **`Compliant` is not control satisfaction.** It means a definition's condition matched at evaluation time, in the same way a scoped predicate meeting its criterion is not control satisfaction. The [control register](CONTROL_REGISTER.md) keeps that distinction in its status vocabulary.

Policy Insights supports continuation through `@odata.nextLink`; see Microsoft's [next-link contract](https://learn.microsoft.com/en-us/rest/api/policyinsights/policy-states/next-link?view=rest-policyinsights-2022-03-01). The live query filters by the complete assignment ID before collection, follows permitted continuation and uses no initial total `$top` cap. Continuation may not change origin, scope, API or filter. Local retention remains bounded at 5,000 rows, with one overflow row and explicit pagination completeness detecting truncation. Incomplete evidence cannot conclude compliant; findings already read remain visible. This is bounded evidence collection, not unlimited estate coverage.

Policy compliance also carries its own completeness problem: a resource type with no applicable definition simply produces no result, which must not read as a pass. Absent evaluation is recorded as absent, never as compliant.

## Collecting it unattended

A hosted run collects Policy when `CG_POLICY_ASSIGNMENT` specifies a legacy subscription assignment name or complete management-group/subscription/RG assignment ID. It is empty by default. One explicit selected subscription is currently required; an optional RG scope also bounds the Policy query. Derived control labels are frozen, but evaluated definition/version and effective-parameter snapshots are not yet captured. New [selected reports](EVIDENCE_REPORTS.md) retain Manual states as attributed context with UNKNOWN classification; the legacy PDF's placeholder suppression is not proof of authenticated attestations.

```sh
python -m cloud_governance collect --subscription <SUBSCRIPTION_ID> --policy-assignment nist-800-53-r5-audit
```

A configured assignment whose compliance cannot be read fails the operation. An empty result would be indistinguishable from a compliant estate, and this program does not archive that ambiguity.

### The reader's permissions

The collecting identity needs read access at three different places, and a denial at any one
of them stops the operation. A failed run names the read that was refused — `assignment`,
`initiative` or `policy_states` — because a bare `403` does not say which permission is
missing.

A custom role at subscription scope covers all three:

| Action | Read it authorizes |
| --- | --- |
| `Microsoft.Authorization/policyAssignments/read` | the assignment |
| `Microsoft.Authorization/policySetDefinitions/read` | its initiative |
| `Microsoft.Authorization/policyDefinitions/read` | the definitions the initiative names |
| `Microsoft.PolicyInsights/policyStates/queryResults/read` | the compliance query |
| `Microsoft.PolicyInsights/policyStates/queryResults/action` | the compliance query |
| `Microsoft.PolicyInsights/policyStates/read` | the compliance query |

The two `queryResults` entries are not interchangeable: the POST is authorized against both,
so a role holding only the `/action` is denied. Every action is a read; none of them permits
creating an assignment, changing one, or triggering remediation.

## Current assignment

| | |
| --- | --- |
| Scope | the lab subscription (identifier deliberately not recorded here) |
| Assignment | `nist-800-53-r5-audit` |
| Enforcement | `DoNotEnforce` |
| Overrides | 4 Guest Configuration definitions disabled |
| Identity roles | none |
| Created | 2026-09-20 |
| First evaluation | 531 records: 14 Compliant, 36 NonCompliant, 481 Unknown |

The 481 Unknown are the `Manual` definitions awaiting attestations, which is what an unattested organizational control should look like.

Those 481 records are not rendered in the auditor PDF. A `Manual` definition evaluates
nothing: Azure emits one record per definition to mark a control as awaiting an
organizational attestation, so the count is a property of Microsoft's initiative and not of
the estate — a subscription holding seven resources produces the same 481 rows as one
holding seven thousand. Rendering them as evidence rows put roughly 108 pages of "unknown"
into a 195-page report about seven resources. They remain in the saved JSON in full; the
PDF states the count, says their omission is not a pass, and lists the records that
actually evaluated something.

This is the lab subscription, not a workplace tenant. Repeat the procedure at the approved workplace scope during handoff.
