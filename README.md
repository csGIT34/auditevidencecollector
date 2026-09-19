# Azure encryption-at-rest evidence

A working, read-only Python CLI for Azure platform engineers. It inventories **every resource type returned by ARM in the selected subscriptions**, applies exact service-specific rules, and reports unsupported types and incomplete evidence explicitly. Microsoft/provider-managed keys are accepted; customer-managed keys are not required.

**Canonical local repository:** `/home/zerocool/github/cloud-governance`. The previous folder at `/home/zerocool/Documents/ChatGPT/Cloud Governance` contains a pointer and a preserved pre-move archive. Make future changes here.

This is an initial technical evidence tool, provisionally mapped to NIST SP 800-53 SC-28 and SC-28(1). It is not a full RCSA assessment, certification, or claim that all application data is protected. A successful resource result applies to the stated scope and evidence basis.

## Run offline now

Python 3.11+ is required. Runtime and tests use the Python standard library; there are no runtime packages to download. Run from the repository:

```sh
cd /home/zerocool/github/cloud-governance
python3 -m azure_at_rest collect \
  --fixture examples/demo-fixture.json \
  --snapshot evidence/demo-snapshot.json \
  --json evidence/demo.json \
  --report evidence/demo.md
```

The fixture is synthetic and makes **no Azure calls, authentication calls or chargeable cloud operations**. It deliberately produces exit code **1**: 34 resources, 21 PASS, 3 FAIL, 7 UNKNOWN, 1 ERROR, 1 UNSUPPORTED and 1 NOT_APPLICABLE. The three failed resource rows represent two underlying conditions: a database with TDE disabled (also reflected on its parent) and Kusto cache-disk encryption disabled. A denied Storage read and workload-storage gaps keep coverage incomplete.

Open [the committed synthetic report](examples/demo-report.md) to see the output without running anything. Its identifiers and findings are examples, not tenant evidence.

```sh
python3 -m unittest discover -v
python3 -m azure_at_rest catalog
python3 -m azure_at_rest assess \
  --input evidence/demo-snapshot.json \
  --json evidence/reassessment.json \
  --report evidence/reassessment.md
```

`assess` does not refresh Azure state. It applies the current rules to the saved, timestamped observation. Reports record a canonical snapshot SHA-256 digest for correlation; snapshots are editable files, not signed attestations.

Optional packaging, if you already have setuptools/pip available: `python3 -m pip install -e .` provides the `azure-at-rest` command. Running the module directly does not need installation.

## Live collection — optional, not yet integration-tested

**No live Azure tenant or subscription has been accessed or tested during development.** Personal subscription credentials must not be used without further user direction. The offline test suite never invokes live collection.

After authorization, an operator can run a smoke test **locally** against existing resources. It uses Azure public-cloud ARM management-plane metadata GETs only. It does not provision resources, use a hosted runner, read blobs/database rows, enable diagnostic logs, activate paid services or modify Azure configuration. Offline testing is the established path when no new Azure charges are permitted. Existing subscriptions/resources retain their normal costs; the tool does not assess those costs.

Requirements: Azure CLI installed, an existing authorized sign-in for the correct tenant, public Azure cloud, and metadata read permissions. The tool only requests a short-lived ARM token through `az account get-access-token`; it never runs `az login` or changes the active subscription/cloud.

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

To add a service: research its Microsoft guarantee and exceptions, add an exact type and reviewed API version, collect only necessary metadata, implement any configurable-state/dependency logic, and add positive, disabled, missing, denied and partial-inventory fixtures. Do not classify an entire provider or all its children by name. Keep unsupported types visible. An additional future adapter can emit the sanitized snapshot contract (for example, separately obtained Wiz evidence); no Wiz integration is implemented here.

No deployment, enforcement, remediation, key rotation, secret reads, messaging, remote repository creation or cloud mutation is part of this tool.

## Future integration direction

Core collection, control evaluation, evidence output and any future core storage path must remain deterministic Python/API operations with **no runtime AI/model dependency or model-call costs**. Versioned structured evidence, stable resource/rule IDs, timestamps, coverage results and replayable snapshots are the foundation for future frequent collection and retained history.

Optional future consumers may include MCP clients used by internal AI tools, uploaded Markdown/PDF knowledge-base documents, APIs and posture dashboards. They can consume core evidence without making collection or evaluation depend on a model. No MCP server, AI integration, dashboard, scheduler, hosting or evidence-storage service is implemented or provisioned here. No runtime AI does not imply free hosting/storage; those choices and costs remain undecided, and no personal Azure spending is authorized.
