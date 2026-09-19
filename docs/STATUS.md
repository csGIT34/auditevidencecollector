# Current implementation and validation status

Updated 2026-09-19. **Source release 0.5.0 (locally validated; expanded checks not live-verified).** This page is the current status; dated validation records describe their named versions and are not rolling acceptance claims.

| Capability | Current state | Evidence / limits |
| --- | --- | --- |
| Azure encryption-at-rest collector, assessment, immutable local/Blob archives and exact-run PDFs | Implemented | Offline tests and [personal live pipeline checks](../infra/personal-lab/REPEAT_VALIDATION.md). A technical result does not establish full NIST control effectiveness. |
| Azure Functions, explicit UAMI, separate runtime/evidence storage | Implemented | Personal Azure still contains v0.3.2, stopped with operations disabled and no timer. The local 0.4.0 cleanup/error refactor is not a new live-deployment claim. |
| Local reliability changes | Implemented in 0.4.0 | Credential cleanup runs even if Blob cleanup fails. HTTP uses a dedicated structured execution error; response codes and safe envelopes are preserved. |
| Wiz normalized evidence import, inventory/finding correlation and historical replay | Implemented and tested locally | [Wiz guide](WIZ_INTEGRATION.md), strict project-defined contract, synthetic CLI demonstration, preservation and failure tests. No native Wiz API/authentication/export mapping has been validated. |
| Representative scale measurements | Local synthetic validation | [Benchmark method/results](LOCAL_SCALE_VALIDATION.md); mixed inventories through the actual collector/archive/PDF pipeline. No cloud throughput or production-capacity claim. |
| CI | Automated local validation | Python tests and builds on Linux/macOS, documentation links, small scale regression, Linux packaged Functions runtime, isolated Terraform mocked plans. No Azure/Wiz credentials required. |
| Multi-control configuration/identity predicates | Implemented; local validation | 115 predicates across all 23 service entries; [scope and use](CONFIGURATION_ASSESSMENTS.md). This is partial support for wider objectives, not whole-service/control completion. |
| All-service NIST program | Incomplete | 215 research objectives; every objective remains open or partially supported in the [delivery register](audit/delivery-register.json). |
| Workplace deployment | Pending workplace inputs and acceptance | Use existing workplace infrastructure patterns and [runtime contract](WORKPLACE_RUNTIME_CONTRACT.md). Home Terraform is not the workplace deployment. |

The previous 0.4.0 release passed 143 Python tests, four Terraform mocked plans and 22 packaged Functions runtime checks. Version 0.5.0 passed 175 Python tests with zero skips and 22 checks in the packaged local Azure Functions runtime. The synthetic ARM/Graph run exercised 115 predicates across 23 service entries (114 PASS, one intentional expired-credential FAIL); its 100-page PDF was rendered and visually reviewed. The original v0.3.1 live archive loads with every original file hash unchanged. These are local checks, not a new Azure deployment or whole-objective acceptance. The original retained v0.3.1 live archive also loaded under 0.4.0 with every object hash unchanged. See [release notes](../CHANGELOG.md).

## Full-project completion

The broader audit system is **incomplete**. Track required implementation, workplace acceptance and lab cleanup in the [project completion plan](PROJECT_COMPLETION_PLAN.md). The 215 proposed checks are the delivery inventory; the new predicate register provides explicit partial implementation links.

## Start locally

1. Follow [macOS/Linux development](MACOS_DEVELOPMENT.md) and run `python scripts/validate.py`.
2. Exercise the full [synthetic Wiz demo](WIZ_INTEGRATION.md#offline-demo).
3. Run [scale benchmarks](LOCAL_SCALE_VALIDATION.md) and the packaged Functions runtime smoke test.
4. Use the [architecture and extension guide](ARCHITECTURE.md) before changing evidence contracts or adding a collector.

## Remaining workplace-specific work

- Bind the approved tenant, identities, resource population, caller authorization, network/DNS and storage to the existing infrastructure patterns.
- Obtain the real Wiz schema/export contract and read scopes. Implement/review its native-to-normalized mapping and, if desired, a live authenticated transport. Reuse the tested importer/reconciler; do not reinterpret issue severities as encryption or NIST findings.
- Validate real API coverage/denials, observations and scan dates, latency, memory, scheduling, retention and operational recovery.
- After successful handoff, preserve needed source/evidence and destroy the temporary personal lab using [its teardown guide](../infra/personal-lab/README.md#phase-5-authorized-project-only-cleanup-after-successful-workplace-handoff). Recheck delayed charges. No cleanup monitor or scheduled teardown is implied by these documents.

Current source and exact-commit validation are available in the [repository](https://github.com/csGIT34/auditevidencecollector) and [CI](https://github.com/csGIT34/auditevidencecollector/actions/workflows/offline.yml). Public documentation excludes personal identifiers, evidence, secrets and Terraform state.
