# Version 0.3.0 validation record

Validated locally on Linux with Python 3.12 on 2026-09-19. This is an offline software validation record, not evidence of an Azure deployment, tenant assessment, macOS run or compliance certification.

| Check | Observed result |
| --- | --- |
| Pinned developer environment | `python scripts/validate.py`: **105 tests passed, zero skips**; all installed constrained package versions matched. `pip check` passed. |
| Assessment and preservation regression | Existing encryption conclusions, CLI behavior, FileStore publication, historical hashes, partial-failure semantics and exact-run selection remained covered. No broader collectors were added. |
| Azure adapters | Fake credentials/transports covered explicit identity selection, refresh/expiry, tenant mismatch, permission errors, bounded retries, pagination, concurrent create conflicts and ambiguous upload acknowledgement. A real Blob SDK with a fake HTTP transport verified `If-None-Match: *` for single uploads and multipart commit. No service request reached Azure. |
| Host operations | SDK binding metadata and handler tests covered the key-protected POST route, exact run ID, disabled defaults, explicit timer schedule, no startup collection, independent report generation, safe errors, budgets and overlap. Concurrent PDF tests preserved earlier objects. |
| Clean distribution install | Built wheel and source distribution. Installed the wheel with Azure/PDF extras into a fresh runtime-only virtual environment from a local wheelhouse; `pip check` passed. From outside the checkout, the installed package collected the fixture, saved a run, loaded its packaged research context and generated its exact-ID PDF. |
| Linux source package | Allowlisted ZIP contained 22 source/config/data files. Extracted it and installed pinned runtime dependencies under `.python_packages/lib/site-packages`. Python with site initialization disabled loaded those dependencies, packaged context and both configured SDK function definitions. This was an import/metadata check, not a Functions host startup. |
| Synthetic PDF | 67 pages, 219,040 bytes; 34 resources: 21 PASS, 3 FAIL, 7 UNKNOWN, 1 ERROR, 1 UNSUPPORTED and 1 NOT_APPLICABLE. Coverage remained incomplete. Saved execution and PDF-generation provenance were distinct. All page text stayed within page bounds; revised scope/provenance pages were rendered and visually inspected. |
| Research integrity | Catalog validator: 23 services, 276 domain cells, 20 families, 215 proposed checks, 208 NIST references and 60 sources. Packaged applicability outline matched the catalog. |

The synthetic example uses `offline_fixture`, local storage, no claimed tenant/identity and unverified retention. Its assessment failure is expected fixture data, not a failed execution. The existing sample and all previous archive objects remain unchanged.

Not executed: macOS or GitHub Actions jobs; Azure Functions Core Tools startup; live managed identity, ARM, Blob or host-storage connections; caller/network authorization; platform deployment; production latency, memory, concurrency or retention checks. Neither a 34-resource fixture nor a mocked SDK transport establishes production scale or cloud permissions. The checked-in Linux/macOS CI workflow is available for a later authorized source push.

Workplace acceptance still requires explicit tenant, subscriptions, user-assigned identity, separate runtime/evidence storage, approved caller/network restrictions, a UTC schedule, hosting plan/deployment inputs and measured workload headroom. Follow [AZURE_FUNCTIONS.md](AZURE_FUNCTIONS.md) and [MACOS_DEVELOPMENT.md](MACOS_DEVELOPMENT.md). No Azure resource, role, remote repository or paid service was created, and no source was pushed.
