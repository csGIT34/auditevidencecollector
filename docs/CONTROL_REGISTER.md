# Control-indexed evidence register

Evidence is collected per resource. Auditors ask per control. This register inverts the index: for each NIST SP 800-53 control it lists every saved observation that references it, what failed, and what is still missing. It re-evaluates nothing — it reads a saved assessment, so a register regenerated from the same archived run is identical.

```sh
python -m cloud_governance control-register --input report.json --report register.md --json register.json
python -m cloud_governance control-register --input report.json --tailoring tailoring.json --report register.md
python -m cloud_governance control-register --template tailoring.json
```

`--input` is the saved assessment JSON that `collect` or `assess` writes. `--operational` optionally contributes attributed operating records. No path overwrites its input, and no output replaces an existing file.

## What this register is not

**No status means a control is satisfied.** That determination belongs to an assessor under SP 800-53A and depends on organization-defined parameters, operating effectiveness across an assessment period, and objectives no cloud API observes. This register reports what evidence exists, nothing further.

| Status | Meaning |
| --- | --- |
| `FINDINGS_PRESENT` | At least one mapped observation failed its supplied criterion. |
| `INCOMPLETE_EVIDENCE` | Mapped observations exist but include UNKNOWN, ERROR, UNSUPPORTED or recorded gaps. |
| `AUTOMATED_EVIDENCE_COLLECTED` | Every mapped observation met its criterion at collection time. Still not a control determination. |
| `ATTRIBUTED_EVIDENCE_ONLY` | Only human or provider records reference this control; no automated observation. |
| `INHERITED_CLAIMED` | An approved tailoring declares inheritance. This tool does not evaluate the provider assurance report, its scope, period or exceptions. |
| `EXCLUDED` | An approved tailoring excludes the control, with a recorded rationale and approver. |
| `NOT_ASSESSED` | Nothing in this run references the control. |

## Declaring tailoring

Without a tailoring file every control reads `UNDECLARED`, nothing is excluded or inherited, and coverage cannot be judged complete. The register says so on its first page.

`--template` writes a draft covering the controls your deployed resource types implicate, so the declaration starts from a file rather than a blank page. Review every row, then set `status` to `approved`.

```json
{
  "schema_version": "1.0",
  "id": "your-approved-tailoring-id",
  "version": "1",
  "status": "approved",
  "controls": {
    "AC-6": {"disposition": "IN_SCOPE", "owner": "Cloud platform security"},
    "PE-3": {"disposition": "INHERITED", "owner": "Azure platform",
             "rationale": "Datacenter physical access sits inside the provider boundary.",
             "assurance_reference": "Authorized provider assurance report, scope and period"},
    "PT-6": {"disposition": "EXCLUDED", "owner": "Privacy office",
             "rationale": "No federal system of records applies to this system.",
             "approver": "Privacy officer", "reviewed_on": "2026-09-20"}
  }
}
```

Rules the validator enforces: an inherited or excluded control requires a written rationale; an excluded control also requires a named approver; an unknown control label is rejected. **A draft tailoring never excludes or inherits anything** — those controls stay `NOT_ASSESSED` and the register records that the disposition was not honored. `approved` records an operator assertion; the application does not independently authenticate approval.

[examples/control-tailoring.json](../examples/control-tailoring.json) is a worked synthetic example, not organizational policy.

## Scope: controls your resources implicate

Two different questions produce two different numbers, and the register reports both.

| Question | Controls |
| --- | --- |
| Implicated by the 23 deployed Azure resource types | 48 |
| Organization-wide candidates in the family review | 189 |

Creating a storage account does not implicate PE-3 or PS-3. Those remain organization-wide candidates with other owners. `--template` therefore defaults to the 48 resource-implicated controls; `--template-scope candidate` emits all 189 when the wider program register is wanted. Each control row carries `service_applicable` so an auditor can separate the two without recounting.

Of the 48, evidence exists for the controls whose predicates ran in that specific collection. A control referenced only by Microsoft Graph predicates shows `NOT_ASSESSED` in an ARM-only run — the register reports what the run proves, not what the tool could collect.

## Governing references

| Reference | Role |
| --- | --- |
| [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) | Control catalog and assessment procedures behind every status in this register. |
| [NIST SP 800-144](https://csrc.nist.gov/pubs/sp/800/144/final) | *Guidelines on Security and Privacy in Public Cloud Computing* (December 2011, active). Public-cloud outsourcing guidance. |

SP 800-144 publishes recommendations, not assessable control identifiers, so **it produces no control status here**. Its nine key issue areas — Governance, Compliance, Trust, Architecture, Identity and Access Management, Software Isolation, Data Protection, Availability and Incident Response (§4.1–4.9) — index the same evidence and frame the provider/customer split that the `INHERITED` disposition records. Its §5 outsourcing lifecycle governs the preliminary, coincident and concluding activities around this evidence, not the evidence itself.

## Relationship to the other reports

The encryption assessment and the configuration predicates remain the systems of record for their observations; this register only indexes them and never alters a saved result. Each evidence item keeps its originating reference (`rule_id` or `check_id`) and resource ID so an auditor can trace a control row back to the exact observation, its criterion and its verification command in the [exact-run PDF](LOCAL_ARCHIVE_PDF.md).
