# Runtime contract

Run production in Azure Functions v4 on Linux x86_64 Python 3.12 using existing infrastructure patterns. Use an explicitly attached user-assigned managed identity and its client ID. Configure authorized tenant and explicit subscription/RG scope; production must not fall back to workstation credentials.

Use separate accounts for Functions coordination storage and retained evidence. Supply an existing evidence container and prefix. The application creates evidence objects but does not provision accounts/containers. Create-only writes and hashes do not establish WORM retention. Configure retention, recovery and audit ownership separately.

Use `deploy/app-settings.example.json` and the [configuration guide](AZURE_FUNCTIONS.md). Keep collection/report flags disabled until acceptance. Review metadata permissions for every enabled source, including tenant-wide Graph scope when enabled. Configure tenant caller authentication and network restrictions in addition to Function keys; keep keys in headers and approved secret mechanisms.

Build using pinned dependencies:

```sh
python scripts/build_functions_package.py --output dist/functions-runtime.zip
python scripts/smoke_functions_runtime.py --package dist/functions-runtime.zip --output ../functions-runtime-check --operational --workload --guest
```

Build on Linux x86_64 Python 3.12. The smoke test requires Docker and a new output directory; image downloads may require network access. `scripts/package_functions.py` produces source only, without dependencies. Never deploy a workstation virtual environment.

Validate actual identity, permissions and denials, network/DNS, storage conflicts, caller authentication, source pagination and report latency/memory before enabling an approved schedule. Cooperative budgets are not hard cancellation. Collection has no checkpoint/resume or exactly-once guarantee. Historical report generation verifies exact archived IDs and never recollects or reassesses source evidence.

Record actual checks and operating decisions in [status](STATUS.md). Local checks do not establish live acceptance.
