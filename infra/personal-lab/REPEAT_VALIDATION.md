# Repeated-request fix and completed live pipeline checks

Validated 2026-09-19. **The observed HTTP 503 failure is resolved in the personal lab with HTTP concurrency 16 and a maximum of one on-demand instance per function group.** A second scoped collection and both current/historical PDF publications completed. The app is stopped with operations disabled. These are personal-lab functional results, not workplace or compliance approval.

## Validated configuration

The only live Terraform change was:

```text
functionAppConfig.scaleAndConcurrency.triggers.http.perInstanceConcurrency: 1 -> 16
```

The existing 2-GiB memory size, one-instance maximum, zero always-ready instances, UAMI, storage permissions, operator-only inbound restriction and disabled SCM basic authentication were retained. Four mocked Terraform plan checks passed, including a regression assertion for the validated HTTP setting. The reviewed plan updated one Function App property; it created or replaced no original resource.

Low HTTP concurrency reproduced failures before the application handler in both the original app and fresh minimal apps in East US and West US 2. Changing response Content-Length did not fix it. A temporary ceiling of 40 permitted eight requests, but each reported a fresh worker counter; that ceiling was not adopted. With a single instance and HTTP concurrency 16, the minimal app handled **24 consecutive requests on the same process, counter 1 through 24**, in about 0.3-0.4 seconds each after its first request. This is a measured configuration mitigation; the internal Azure cause is not established, and production load sizing is not inferred from a small lab.

On the original app with the unchanged v0.3.2 runtime package, the original curl client then passed **20 consecutive authenticated invalid-run requests** with the expected HTTP 400 application response, plus missing/wrong-key HTTP 401 checks. All 22 responses completed within 1.728 seconds; authenticated responses were below 0.370 seconds. This verifies repeated real handler dispatch and key rejection without generating audit work.

The [earlier investigation](DISPATCH_INVESTIGATION.md) and [initial live record](LIVE_VALIDATION.md) remain historical evidence of the failure and earlier fixes. Their previous blocked/final-state descriptions are superseded by this record.

## Completed live collection and reports

The deployed package is application v0.3.2, PDF renderer 1.2, unchanged rule version `2026.09.19.1`; SHA-256 `3315e44847a164e79788eadf3bfa80ae3af626000a5b93cb75f7f0ada6b66fc0`. Runtime application bytes match the published source; later changes concern packaging, infrastructure, tests and guides.

| Check | Observed result |
| --- | --- |
| Second collection | One manual HTTP 202 invocation; collection completed at 20:56:36 UTC. Selected RG only, five resources, complete inventory, zero collection errors. |
| Managed identity | New saved provenance records the configured UAMI and successful authenticated ARM tenant/subscription preflight. Blob publication used the hosted managed-identity adapter. |
| Findings | PASS 2 storage accounts, NOT_APPLICABLE 1 identity, UNKNOWN 1 Function App, UNSUPPORTED 1 plan. Overall INCOMPLETE is the expected coverage conclusion, not an execution failure. |
| New-run PDF | HTTP 201 in 1.812 seconds; generated at 20:57:44 UTC, 114,816 bytes, 20 pages. New RG-scoped verification instructions are present. |
| Historical PDF after newer run | HTTP 201 in 0.573 seconds; generated at 20:57:45 UTC, 114,792 bytes, 20 pages. It retains the original collection time, v0.3.1 facts/context and source-manifest association while recording current renderer 1.2. |
| Original preservation | All nine original objects matched their previously saved SHA-256 values before and after the new work. No original run/PDF was overwritten. Twenty completed archive/probe objects remain after adding one five-object run and two three-object reports. |
| Request validation after live work | A valid saved run ID with an extra field returned HTTP 400 in 0.164 seconds without generating a report. |
| PDF review | Both PDFs were rendered and visually inspected across all 20 pages; titles, tables, scope, provenance, report associations, verification commands and page numbering were checked. Embedded Vera fonts were confirmed. |

The original historical run retains its known wider inventory-command limitation; regeneration preserves historical context instead of silently rewriting it. Use the new-run report for corrected RG-scoped suggestions. The original PDF binary is also retained.

An early trigger-synchronization attempt after changing app settings returned a host error before any collection was invoked. The corrected sequence required the protected runtime host status and actual function list to be ready before synchronizing ARM metadata. Only after both indexes agreed was the collection invoked. Collection was then disabled and the timer removed before reports. No work invocation was automatically retried.

## Repeatable local validation

`scripts/smoke_functions_runtime.py` tests a built Linux amd64 deployment ZIP in Microsoft's pinned Functions image with temporary local keys, a loopback-only port, one CPU and 2 GiB, without Azure credentials or enabled operations. It checks indexing, absence of a timer, two key denials and 20 authenticated validation requests over fresh connections. It writes package/image/version/results privately and removes its container. Cleanup was also verified after simulated startup and log-retrieval failures.

The tested local image runs host `4.1053.200.7`, whereas the recorded Flex host is `4.1054.250.26428`; local success is not a simulation of Flex's front end. The offline gate passed **121 tests, zero skips**, and this additional **22-check runtime smoke test** passed locally and in [Linux CI for the smoke-test commit](https://github.com/csGIT34/auditevidencecollector/actions/runs/35468264740). The same CI run passed the macOS offline gate and builds. The current [workflow](https://github.com/csGIT34/auditevidencecollector/actions/workflows/offline.yml) runs the runtime check on Linux as well as the existing two-OS validation.

## Shutdown, costs and handoff

The temporary comparison apps/plans and their separate package container were removed using their isolated Terraform state. No new logging workspace, Application Insights resource, always-ready allocation, public endpoint exception, provider registration, quota increase, notification or recurring task remains. The original project resources and evidence remain for the authorized cleanup after workplace handoff.

HTTP concurrency 16 does not increase the one-instance-per-group ceiling. The existing [cost model](COST.md) and entire-personal-bill limit below $25 still apply; diagnostic estimates are not a measured invoice. Runtime flags are false, the schedule is empty and the app is stopped between tests. The original lab expiry is unchanged. A final refreshed Terraform plan reported no changes. The final subscription resource inventory matched the five original lab resources plus two pre-existing resources; all temporary comparison resources were absent. The final MonthToDate Cost Management request succeeded but returned no posted rows, which does not establish zero charges or the final bill.

Next use the user's existing workplace infrastructure patterns and [runtime contract](../../docs/WORKPLACE_RUNTIME_CONTRACT.md). Work-tenant identity, caller authorization, private DNS/network, actual scope and load, schedule and retention still require workplace validation. An outside-operator-IP denial and the subscription's numeric Flex quota were not independently established here. The 23-service/20-family mapping remains applicability research; executable coverage is scoped encryption at rest.
