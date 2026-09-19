# Cloud governance evidence and audit program

Start with [current implementation status](docs/STATUS.md), [architecture](docs/ARCHITECTURE.md), and the [local Wiz workflow](docs/WIZ_INTEGRATION.md).

**Program scope: all applicable NIST controls across the authoritative 23 Azure services.** Start with the [program-wide control/evidence catalog](docs/audit/README.md), [service matrix](docs/audit/SERVICE_MATRIX.md), [all-family review](docs/audit/NIST_FAMILY_REVIEW.md) and [implementation backlog](docs/audit/IMPLEMENTATION_BACKLOG.md). The catalog records 215 proposed checks across 12 domains and all 20 NIST families; it is provisional research, not implemented control coverage or tenant findings.

The currently executable capability is a read-only encryption-at-rest Python CLI for Azure platform engineers. It inventories **every resource type returned by ARM in the selected subscriptions or optional resource-group scope**, applies exact service-specific rules, and reports unsupported types and incomplete evidence explicitly. Microsoft/provider-managed keys are accepted; customer-managed keys are not required.

**Development:** macOS or Linux with Python 3.12. **Production target:** Azure Functions with an explicitly selected managed identity and separate retained-evidence Blob storage. Start with [portable setup](docs/MACOS_DEVELOPMENT.md) and the [workplace Functions guide](docs/AZURE_FUNCTIONS.md). The bounded [personal-lab validation](infra/personal-lab/REPEAT_VALIDATION.md) now passes repeated HTTP requests, managed-identity collection and current/historical PDF generation with original evidence preserved. Workplace acceptance is separate.

The [0.3.0 validation record](docs/VALIDATION_0_3_0.md) separates the completed offline checks from the remaining workplace deployment gates.

This is an initial technical evidence tool, provisionally mapped to NIST SP 800-53 SC-28 and SC-28(1). It is not a full RCSA assessment, certification, or claim that all application data is protected. A successful resource result applies to the stated scope and evidence basis.

The [home-only Terraform lab](infra/personal-lab/README.md) has a documented, stopped test deployment; each new deployment requires its own cost/resource review. Workplace infrastructure uses existing patterns through the [runtime contract](docs/WORKPLACE_RUNTIME_CONTRACT.md). The optional RG scope confines collection to a single approved group.

## Save a run and produce an auditor PDF

Version **0.4.0** preserves the local archive and separate historical PDF operation and adds an optional Azure Functions/Blob hosting layer. The auditor receives one self-contained PDF; internal JSON preserves the collected facts and saved conclusions for reproducibility. Existing encryption collectors are unchanged. The 0.3.2 report corrections remain; 0.4.0 adds local Wiz evidence import/comparison and reliability/tooling improvements. Historical archives remain frozen.

```sh
python3 -m pip install '.[pdf]'
python3 -m azure_at_rest collect --fixture examples/demo-fixture.json --store ./evidence/archive
python3 -m azure_at_rest runs --store ./evidence/archive
# Use the exact r-... ID printed above; the demo collection exits 1 intentionally.
python3 -m azure_at_rest pdf --store ./evidence/archive --run-id YOUR_EXACT_RUN_ID
```

Each collection and PDF generation creates new archived objects. Historical rendering verifies the selected run and uses its saved facts, conclusions and context without recollection or reassessment. Incomplete/corrupt runs cannot be reported as complete. The PDF contains findings, criteria, observations, dependency references, errors and broader audit gaps inside the document.

See [local workflow and failure semantics](docs/LOCAL_ARCHIVE_PDF.md), the [workplace Azure handoff](docs/WORKPLACE_AZURE_HANDOFF.md), and [ready-to-use implementation](docs/prompts/AZURE_ADAPTER_IMPLEMENTATION.md) / [validation prompts](docs/prompts/AZURE_ADAPTER_VALIDATION.md). The optional Azure adapter and Functions triggers are implemented, tested offline and validated in the personal lab; deployment and acceptance in the work tenant remain workplace steps. Both hosted operations default disabled. No database or runtime AI is required. The local filesystem adapter requires POSIX support. ReportLab is optional for core collection and required for PDFs.

## Run offline now

Python 3.11+ is required. Collection, assessment and JSON archiving use the Python standard library. PDF output uses the optional ReportLab extra; PDF extraction tests use optional pypdf. For the complete development/test dependencies, follow [the venv setup](docs/MACOS_DEVELOPMENT.md); its validation gate rejects skipped checks. Run from the repository:

```sh
# From the cloned repository root, with your virtual environment active
python3 -m azure_at_rest collect \
  --fixture examples/demo-fixture.json \
  --snapshot evidence/demo-snapshot.json \
  --json evidence/demo.json \
  --report evidence/demo.md
```

The fixture is synthetic and makes **no Azure calls, authentication calls or chargeable cloud operations**. It deliberately produces exit code **1**: 34 resources, 21 PASS, 3 FAIL, 7 UNKNOWN, 1 ERROR, 1 UNSUPPORTED and 1 NOT_APPLICABLE. The three failed resource rows represent two underlying conditions: a database with TDE disabled (also reflected on its parent) and Kusto cache-disk encryption disabled. A denied Storage read and workload-storage gaps keep coverage incomplete.

Open [the committed synthetic report](examples/demo-report.md) to see the output without running anything. Its identifiers and findings are examples, not tenant evidence.

```sh
python3 scripts/validate.py
python3 -m azure_at_rest catalog
python3 -m azure_at_rest assess \
  --input evidence/demo-snapshot.json \
  --json evidence/reassessment.json \
  --report evidence/reassessment.md
```

`assess` does not refresh Azure state. It applies the current rules to the saved, timestamped observation. Reports record a canonical snapshot SHA-256 digest for correlation; snapshots are editable files, not signed attestations.

Optional packaging, if you already have setuptools/pip available: `python3 -m pip install -e .` provides the `azure-at-rest` command. Running the module directly does not need installation.

## Live collection — optional and explicitly scoped

The authorized personal lab completed two hosted RG-scoped collections and current/historical PDF generation; see the [live validation results](infra/personal-lab/REPEAT_VALIDATION.md). This does not establish coverage for other services, subscriptions or workplace environments. The offline test suite never invokes live collection. Obtain authorization for each new tenant/scope before collecting its evidence.

After authorization, an operator can run a smoke test **locally** against existing resources. It uses Azure public-cloud ARM management-plane metadata GETs only. It does not provision resources, use a hosted runner, read blobs/database rows, enable diagnostic logs, activate paid services or modify Azure configuration. Offline testing is the established path when no new Azure charges are permitted. Existing subscriptions/resources retain their normal costs; the tool does not assess those costs.

Requirements: Azure CLI installed, an existing authorized sign-in for the correct tenant, public Azure cloud, and metadata read permissions. The local CLI only requests a short-lived ARM token through `az account get-access-token`; it never runs `az login` or changes the active subscription/cloud.

```sh
# Substitute an existing subscription UUID after live testing is authorized.
python3 -m azure_at_rest collect \
  --subscription 11111111-1111-1111-1111-111111111111 \
  --snapshot evidence/snapshot.json \
  --json evidence/audit.json \
  --report evidence/audit.md
```

Repeat `--subscription UUID` for multiple subscriptions. Omit it to paginate all subscriptions visible to the CLI identity in its **current tenant**. This does not discover other tenants or subscriptions the identity cannot see. An explicit subscription outside that tenant can fail authentication/authorization; the report records incomplete collection. Sovereign clouds and Azure Stack are not implemented.

[Permissions and collection details](docs/COLLECTION.md) list the read operations and limitations. API versions are pinned; a provider/version/region mismatch results in an error, never a fallback pass.

## Reading the result

| Result | Meaning |
| --- | --- |
| PASS | Positive evidence for the stated resource scope: API configuration, an exact documented service guarantee supported by a successful identity read, or verified dependencies. |
| FAIL | Observed disabling state, or a resolved dependency with a confirmed failure. |
| UNKNOWN | Missing/contradictory fields, incomplete child listings, unresolved dependencies, an unreviewed tier or remaining workload storage gaps. |
| ERROR | A required resource or encryption read failed, including access denial or invalid response identity. |
| UNSUPPORTED | Discovered exact ARM type has no reviewed rule. It remains in the inventory and coverage report. |
| NOT_APPLICABLE | Explicitly justified narrow scope, such as a networking construct or SQL master's unsupported TDE mechanism. It does not certify associated workloads. |

| Exit | Meaning |
| --- | --- |
| 0 | Supported observed scope is satisfied, with no known failures or gaps. Still subject to report limitations. |
| 1 | At least one confirmed failure. `coverage_incomplete` independently indicates remaining gaps. |
| 2 | No confirmed failure, but evidence or coverage is incomplete, unsupported, denied or empty. |
| 3 | Local input/output or schema error; no raw error payload is printed. |

The report includes per-resource identity, collection/assessment timestamps, API and rule versions, scope, result/reason, safe evidence, dependencies, source links and gaps. Inventory traversal, child traversal, unsupported types and collection errors are summarized separately. A partial inventory can contain valid individual passes while the overall result remains incomplete.

## Auditor verification commands

Both report formats include per-resource `verification_commands`. Each entry contains the exact GET URL and API version, shell command and argv, selected-field query, what it checks, expected/saved values, interpretation and service documentation. The Markdown report places commands next to the resource evidence. Resolved dependencies include their separate reads; SQL parents include the child listing and each observed database's TDE request.

Use the commands only after live access is authorized, from a local POSIX shell with Azure CLI and read rights in the correct tenant/public cloud. They retrieve **current** state; they cannot recreate historical proof. Saved snapshots preserve their recorded API versions when generating commands. Generating a report never executes the commands.

Synthetic examples are marked **DO NOT RUN**; demo IDs do not identify deployed resources. Unsupported/not-applicable resources receive inventory-only commands, and unknown/denied results retain their limitations. An identity read is not cryptographic proof: apply the linked Microsoft guarantee only within its stated scope. Configurable mechanisms such as TDE require the separate state read.

List commands show one page with a `more_pages` indicator. Traverse all pages independently; a missing match on one page is inconclusive. Queries select metadata and omit settings/secret values and SAS-bearing URLs; Azure CLI applies projections locally after receiving the ARM response. Keep the projections and avoid debug/raw-response logging. No generated command requests keys, secrets, application data or cloud mutation.

See [Azure CLI REST documentation](https://learn.microsoft.com/en-us/cli/azure/reference-index?view=azure-cli-latest#az-rest) and [query behavior](https://learn.microsoft.com/en-us/cli/azure/use-azure-cli-successfully-query?view=azure-cli-latest).

## Coverage

The [authoritative 23-service program scope](docs/PROGRAM_SCOPE.md) maps the user's service list to current coverage, missing collection planes and deployment-family questions. It governs program scope across selected controls; the current code still assesses only encryption at rest (SC-28 / SC-28(1)).

The [exact rule matrix](docs/COVERAGE.md) is the source for supported ARM types, assessed scopes and Microsoft documentation. Broadly:

- Reviewed service guarantees cover Storage; managed disks/snapshots/images; PostgreSQL/MySQL Flexible Server; Cosmos DB accounts including MongoDB API; Azure DocumentDB Mongo clusters (formerly MongoDB vCore); ACR; backup vault storage; Log Analytics; Event Hubs; Premium Service Bus; AI Search; App Configuration values; Key Vault secrets; and reviewed Redis Enterprise SKUs.
- SQL Database, SQL Managed Instance databases and Synapse dedicated SQL pools require explicit TDE endpoint evidence. SQL parents enumerate databases. Kusto requires its separate VM disk-encryption flag as well as the documented backing-storage guarantee.
- AKS, VMs/VMSS, Functions/App Service, Container Apps and Synapse workspaces produce partial workload evidence and explicit gaps. The collector resolves known ARM references and enumerates supported child collections, but does not inspect cluster credentials, application settings or secret connection strings to infer storage.
- Classic Redis persistence, newer Managed Redis SKUs, non-Premium Service Bus and classic Application Insights remain unverified where the current rule lacks sufficient evidence.
- MongoDB Atlas, self-hosted MongoDB internals, Managed HSM, NetApp, Databricks, Data Factory, Service Fabric, HDInsight and other unlisted types have no full rule. Discovery does not imply support. Runtime/data-plane dependencies and arbitrary child types are not exhaustively inventoried.

Private endpoints are explicitly in program scope for resource-local evidence and shared ownership; their current encryption rule is inventory-only and justified N/A. VNet/routing/shared-network administration remains outside the platform scope. Other listed network constructs retain narrow encryption applicability explanations. No network changes are performed.

## Design and extension

`collector.py` supplies a GET-only ARM adapter, bounded retries/pagination and an offline transport. `safety.py` validates resource identity and projects allowlisted evidence. `catalog.py` pins exact types, API versions, scopes and sources. `assessment.py` evaluates evidence and dependencies. `verification.py` creates auditor read commands as data; `report.py` and `cli.py` generate reports and exit status. Tests exercise the same collector path used for live runs.

To add a service: research its Microsoft guarantee and exceptions, add an exact type and reviewed API version, collect only necessary metadata, implement any configurable-state/dependency logic, and add positive, disabled, missing, denied and partial-inventory fixtures. Do not classify an entire provider or all its children by name. Keep unsupported types visible. The [Wiz integration](docs/WIZ_INTEGRATION.md) validates a separate normalized evidence contract and compares it with saved ARM runs. It preserves both sources without treating Wiz findings as ARM observations or changing Azure conclusions. A native Wiz API/export mapper still requires workplace schema/access validation.

ARM collection performs no enforcement, remediation, key rotation or application-secret reads. The optional Blob adapter writes only archive objects in the configured existing container. No resource provisioning, deployment, role changes, messaging or remote repository creation is performed by the tool.

## Future integration direction

Core collection, control evaluation, evidence output and any future core storage path must remain deterministic Python/API operations with **no runtime AI/model dependency or model-call costs**. Versioned structured evidence, stable resource/rule IDs, timestamps, coverage results and replayable snapshots are the foundation for future frequent collection and retained history.

Optional future consumers may include MCP clients used by internal AI tools, uploaded Markdown/PDF knowledge-base documents, APIs and posture dashboards. They can consume core evidence without making collection or evaluation depend on a model. No MCP server, AI integration or dashboard is implemented. The personal Azure lab has completed bounded live collection/report checks and is currently stopped, with no timer or enabled operations. Cloud resources were explicitly authorized for that temporary lab; retained storage may still incur charges. See [current status](docs/STATUS.md) and the [cost/teardown guide](infra/personal-lab/README.md). Workplace infrastructure, scope and acceptance remain separate.
