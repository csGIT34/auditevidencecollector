# Predicate execution plan

Working plan to close every remaining service objective for the Azure resource types this team deploys. Created 2026-09-20. Progress is recorded here as each section completes; a section is complete only when its predicates are API-verified, offline-tested, regenerated into the delivery register and passing the full gate.

Scope is the 23 deployed service entries. Organization-wide candidate controls with other owners (PE, PS, AT, PM, PL and every `XX-1` policy control) are outside this plan; they close through declared purview inheritance and attributed records. See the [control register](../CONTROL_REGISTER.md).

## Starting position

| | Count |
| --- | --- |
| Controls implicated by the deployed resource types | 48 |
| Of those, with executable evidence at 0.19.0 | 38 |
| Service objectives with no predicate at 0.19.0 | 95 |

Those 95 classify by the evidence plane their objective actually requires:

| Plane | Objectives | Notes |
| --- | --- | --- |
| ARM control plane | 68 | Implementable with the existing collector and predicate registry |
| Disposition only | 13 | No technical plane exists; provider or client-side facts no Azure API returns |
| Guest/agent reports | 6 | Through the existing typed guest import |
| Microsoft Graph | 5 | Through the existing Graph collector |
| Kubernetes API | 2 | Through the existing restricted Kubernetes import |
| Service data plane | 1 | Requires a reviewed data-plane contract |

## Sections

Ordered by ARM density, so the largest verified gains land first.

| # | Section | Objectives | Controls strengthened | Status |
| --- | --- | --- | --- | --- |
| S1 | Domain K — secrets, certificates and key lifecycle | 20 (19 ARM, 1 guest) | IA-5, SC-12, SC-17, IA-9 | IN PROGRESS — 4 of 20 |
| S2 | Domain C — secure configuration, change approval and drift | 17 (16 ARM, 1 Graph) | CM-2, CM-3, CM-6, CM-7, CM-14, SI-10, SI-12 | NOT STARTED |
| S3 | Domain B — backup, recovery and availability | 16 (15 ARM, 1 Graph) | CP-2, CP-4, CP-9, CP-9(1), CP-10 | NOT STARTED |
| S4 | Domain V — vulnerabilities, versions and supply chain | 15 (6 ARM, 3 guest, 6 disposition) | RA-5, SA-9, SA-11, SA-22, SC-13, SI-2, SI-7, SR-4, SR-6 | NOT STARTED |
| S5 | Domain T — transmission protection | 17 (5 ARM, 2 Kubernetes, 2 guest, 1 data plane, 6 disposition) | SC-8, SC-8(1), SC-17, IA-9, IA-13 | NOT STARTED |
| S6 | Domains N, L and R — exposure, audit generation, remaining at-rest | 10 (7 ARM, 2 Graph, 1 disposition) | AC-4, SC-7, AU-2, AU-5, AU-12, SC-28, SC-28(1), IA-13 | NOT STARTED |
| S7 | Dispositions and reconciliation | 13 disposition-only objectives | — | NOT STARTED |

## Section acceptance

Each section is complete when all of the following hold, not before:

1. Every property is read from the pinned Microsoft ARM template reference for the exact API version registered. No property is inferred from a sibling service.
2. Positive, negative, missing and invalid variants are offline-tested; secret-bearing payloads are proven excluded from the snapshot and report.
3. The delivery register regenerates and its gate passes, moving the listed objectives off `NOT_IMPLEMENTED`.
4. `python scripts/validate.py` passes with zero skips.
5. The control register shows the intended controls gaining evidence, measured before and after.

An objective that turns out to have no safely readable ARM property is moved to S7 with its reason recorded, rather than given a weak predicate. A gap is visible; a wrong PASS is not.

## Disposition-only objectives

These 13 have no technical collection plane and will not receive predicates. They close through attributed records or declared inheritance in the purview:

`AI-T`, `APPC-T`, `APPC-V`, `APPREG-R`, `BV-T`, `COS-V`, `EG-V`, `EH-V`, `KV-T`, `KV-V`, `PE-T`, `ST-V`, `UAMI-T`

They describe provider-internal behaviour or customer client-side code — SDK transport, managed engine internals, consuming application libraries — that no Azure management API reports.

## Progress log

Recorded as sections complete, with the measured before and after.

| Date | Section | Objectives closed | Predicates added | Controls gaining evidence | Tests |
| --- | --- | --- | --- | --- | --- |
| 2026-09-20 | S1 tranche 1 | ST-K, ACR-K, APPC-K, REDIS-K (95 → 91 open) | 4 key-reference predicates | IA-5, SC-12, SC-17 gain depth | 338 → 346 |
