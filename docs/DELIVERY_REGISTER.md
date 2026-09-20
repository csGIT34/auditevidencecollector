# Check-level delivery register

[delivery-register.json](audit/delivery-register.json) is generated from the 215 research objectives and executable registries. It is a source handoff inventory, not a tenant assessment or approval record.

```sh
python scripts/control_delivery_register.py --check
python scripts/control_delivery_register.py --objective AUTO-V
```

The second command prints one objective and its linked implementations without changing any file. IDs include `ST-N`, `VM-R`, `AKS-V` and `ORG-I`. Regenerate after adding or changing registered collectors with `python scripts/control_delivery_register.py`; CI rejects stale output.

Each objective includes required evidence, organization criteria, proposed permission profiles, owner requirements, implementation references, encryption support, reporting routes and the remaining whole-objective acceptance boundary. The capability index resolves each configuration/workload/guest predicate to its collection plane, code, tests, criteria contract and permission guide. Configuration entries also include the pinned API, projected property and definition source. The test paths identify coverage to inspect and run; dated validation results remain in [status](STATUS.md).

Required collection planes and permission profiles describe the broader research objective. Implemented collection planes describe only the linked code. They are deliberately separate: ARM metadata cannot substitute for guest, Kubernetes or service data-plane facts. Permission profiles are not deployment grants or proof of effective access; review endpoint-specific permissions in the linked guides.

`PARTIAL_EXECUTABLE_SUPPORT` means some evidence exists for the objective. `NOT_IMPLEMENTED` means there is no registered automatic predicate/encryption support; the shared operational importer may still retain explicitly attributed evidence. Manual/inherited acceptance remains `NOT_ASSESSED`, live acceptance remains `NOT_VERIFIED`, and exclusions remain null unless separately reviewed. No objective is silently excluded or marked complete by the generator.

The register is schema 2.0. Earlier fields and objective IDs are retained; the capability index, proposed permission definitions and traceability fields are additive. This is a development artifact, outside immutable evidence archives. Regenerating it never rewrites historical assessment results. The current index does not imply that native Wiz or guest-vendor integration is implemented, or that all variants of an objective are covered.
