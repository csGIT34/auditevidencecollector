# Control-indexed evidence register

Evidence is collected per resource. Auditors ask per control. This register inverts the index: for each NIST SP 800-53 control it lists every saved observation that references it, what failed, and what is still missing. It re-evaluates nothing — it reads a saved assessment, so a register regenerated from the same archived run is identical.

```sh
python -m azure_at_rest control-register --input report.json --report register.md --json register.json
python -m azure_at_rest control-register --input report.json --purview purview.json --report register.md
python -m azure_at_rest control-register --template purview.json
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
| `INHERITED_CLAIMED` | An approved purview declares inheritance. This tool does not evaluate the provider assurance report, its scope, period or exceptions. |
| `EXCLUDED` | An approved purview excludes the control, with a recorded rationale and approver. |
| `NOT_ASSESSED` | Nothing in this run references the control. |

## Declaring purview

Without a purview file every control reads `UNDECLARED`, nothing is excluded or inherited, and coverage cannot be judged complete. The register says so on its first page.

`--template` writes a draft covering all candidate controls from the [family review](audit/NIST_FAMILY_REVIEW.md) so the declaration starts from a file rather than a blank page. Review every row, then set `status` to `approved`.

```json
{
  "schema_version": "1.0",
  "id": "your-approved-purview-id",
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

Rules the validator enforces: an inherited or excluded control requires a written rationale; an excluded control also requires a named approver; an unknown control label is rejected. **A draft purview never excludes or inherits anything** — those controls stay `NOT_ASSESSED` and the register records that the disposition was not honored. `approved` records an operator assertion; the application does not independently authenticate approval.

[examples/control-purview.json](../examples/control-purview.json) is a worked synthetic example, not organizational policy.

## Current coverage

Against the 189 candidate controls in the family review, the synthetic all-service run produces:

| | Controls |
| --- | --- |
| With automated evidence | 38 |
| `NOT_ASSESSED` | 151 |

That gap is the honest state of the program, and it is the point of this register: it makes the remaining work visible per control instead of implied by a predicate count. Families with no automated evidence at all — AT, CA, IR, MA, MP, PE, PL, PM, PS, PT — are organizational or provider-owned by design. They close through declared inheritance and attributed records, not through collectors. See the [project completion plan](PROJECT_COMPLETION_PLAN.md) for the remaining technical families.

## Relationship to the other reports

The encryption assessment and the configuration predicates remain the systems of record for their observations; this register only indexes them and never alters a saved result. Each evidence item keeps its originating reference (`rule_id` or `check_id`) and resource ID so an auditor can trace a control row back to the exact observation, its criterion and its verification command in the [exact-run PDF](LOCAL_ARCHIVE_PDF.md).
