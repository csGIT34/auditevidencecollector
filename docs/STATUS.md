# Current implementation and validation status

Updated 2026-09-19. **Source release 0.8.1 (local tests passed; expanded reads not live-verified).** This page is the current status; dated validation records describe their named versions and are not rolling acceptance claims.

| Capability | Current state | Evidence / limits |
| --- | --- | --- |
| Azure encryption-at-rest collector, assessment, immutable local/Blob archives and exact-run PDFs | Implemented | Offline tests and [personal live pipeline checks](../infra/personal-lab/REPEAT_VALIDATION.md). A technical result does not establish full NIST control effectiveness. |
| Azure Functions, explicit UAMI, separate runtime/evidence storage | Implemented | Personal Azure still contains v0.3.2, stopped with operations disabled and no timer. The local 0.4.0 cleanup/error refactor is not a new live-deployment claim. |
| Local reliability changes | Implemented in 0.4.0 | Credential cleanup runs even if Blob cleanup fails. HTTP uses a dedicated structured execution error; response codes and safe envelopes are preserved. |
| Wiz normalized evidence import, inventory/finding correlation and historical replay | Implemented and tested locally | [Wiz guide](WIZ_INTEGRATION.md), strict project-defined contract, synthetic CLI demonstration, preservation and failure tests. No native Wiz API/authentication/export mapping has been validated. |
| Representative scale measurements | Local synthetic validation | [Benchmark method/results](LOCAL_SCALE_VALIDATION.md); mixed inventories through the actual collector/archive/PDF pipeline. No cloud throughput or production-capacity claim. |
| CI | Automated local validation | Python tests and builds on Linux/macOS, documentation links, small scale regression, Linux packaged Functions runtime, isolated Terraform mocked plans. No Azure/Wiz credentials required. |
| Multi-control configuration/identity predicates | Implemented; local validation | 165 predicates across all 23 service entries; [scope and use](CONFIGURATION_ASSESSMENTS.md). This is partial support for wider objectives, not whole-service/control completion. |
| Saved-run comparison and configurable freshness | Implemented locally in 0.5.1 | [Exact-run comparisons](SAVED_RUN_COMPARISON.md) separate facts, criteria, outcomes and lost evidence; configured age windows keep stale/future configuration observations UNKNOWN. |
| Operational records and evidence supplements | Implemented locally | [Import and hosting guide](OPERATIONAL_EVIDENCE.md). Attributed statements remain separate from automated findings. |
| All-service NIST program | Incomplete | 215 research objectives; every objective remains open or partially supported in the [delivery register](audit/delivery-register.json). |
| Workplace deployment | Pending workplace inputs and acceptance | Use existing workplace infrastructure patterns and [runtime contract](WORKPLACE_RUNTIME_CONTRACT.md). Home Terraform is not the workplace deployment. |

Version 0.5.1 passed 188 Python tests with zero skips and 22 packaged local Functions runtime checks. A 19-page synthetic comparison/freshness report was rendered and visually reviewed. Exact v0.3.1 and v0.5.0 archives remain readable with every original file hash unchanged. Saved-run comparison records criteria changes and lost evidence separately. The deployed personal lab is unchanged and stopped.

The previous 0.4.0 release passed 143 Python tests, four Terraform mocked plans and 22 packaged Functions runtime checks. Version 0.5.0 passed 175 Python tests with zero skips and 22 checks in the packaged local Azure Functions runtime. The synthetic ARM/Graph run exercised 115 predicates across 23 service entries (114 PASS, one intentional expired-credential FAIL); its 100-page PDF was rendered and visually reviewed. The original v0.3.1 live archive loads with every original file hash unchanged. These are local checks, not a new Azure deployment or whole-objective acceptance. The original retained v0.3.1 live archive also loaded under 0.4.0 with every object hash unchanged. See [release notes](../CHANGELOG.md).

Version 0.6.0 passed 199 tests with zero skips and 22 packaged local Functions runtime checks. Its synthetic all-service run evaluates 140 predicates (139 PASS, one intentional expired-credential FAIL). The 113-page PDF was rendered and visually reviewed, including inherited custom-role permissions and delegated consent. No cloud changes were made.

Version 0.7.0 passed 207 local tests with zero skips. Diagnostic routing and protected-backup populations are fixture-tested; no live deployment is implied.

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

Version 0.8.0 passed 219 tests with zero skips and 28 checks in the final packaged Linux Functions runtime, including both optional operational endpoints. Required operational evidence identifies missing/current/conflicting assertions without overwriting automated results. The three-page operational supplement and all 128 pages of the v0.7.0 configuration report were rendered and visually reviewed. Historical 0.3.1, 0.5.0 and 0.7.0 archives loaded with every original file hash unchanged. No Azure resources were changed.

Version 0.8.1 adds actual Uniform VMSS instance population/model comparison. All 223 local tests passed with zero skips. Flexible instance membership, guest configuration and image/patch findings remain separate unfinished work.

The 0.8.1 Linux deployment package passed 28 local Functions runtime checks. Its all-service fixture produced 165 configuration results (164 PASS, one intentional expired-credential FAIL, no UNKNOWN/ERROR); the new instance-result PDF page was rendered and visually checked. Original run objects remained unchanged during report generation. These are synthetic checks, not live Azure validation.
