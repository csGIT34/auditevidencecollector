# Applicability coverage audit

Catalog 2026-09-19.2; reviewed 2026-09-19. **23 services × 12 domains = 276 considered cells; 20 NIST families reviewed.** This is research coverage, never a pass rate or deployed inventory claim.

215 proposed evidence checks: 202 service-specific and 13 shared. 208 distinct current NIST control/enhancement references (including family-review candidates/policy controls) validated against the official source. **Zero new control collectors implemented by this catalog.**

D = direct service evidence; S = shared/process evidence; H = inherited provider evidence; B = no resource-local mechanism, with a documented boundary rationale and shared/dependency checks. All cells have resolvable check references. D is not automated, implemented or passed.

| # | Service | I | N | R | T | K | L | C | V | B | O | D | G |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | Event Hubs | D | D | D | D | D | D | D | H | D | S | S | S |
| 02 | AKS | D | D | D | D | D | D | D | D | D | S | S | S |
| 03 | App registrations | D | D | H | D | D | D | D | D | D | S | S | S |
| 04 | Event Grid | D | D | D | D | D | D | D | H | D | S | S | S |
| 05 | Storage Accounts | D | D | D | D | D | D | D | H | D | S | S | S |
| 06 | Cosmos DB | D | D | D | D | D | D | D | H | D | S | S | S |
| 07 | Managed Redis | D | D | D | D | D | D | D | H | D | S | S | S |
| 08 | Function Apps | D | D | D | D | D | D | D | D | D | S | S | S |
| 09 | Key Vaults | D | D | D | D | D | D | D | H | D | S | S | S |
| 10 | PostgreSQL Flexible Servers | D | D | D | D | D | D | D | D | D | S | S | S |
| 11 | Azure Container Apps | D | D | D | D | D | D | D | D | D | S | S | S |
| 12 | user-assigned managed identities | D | D | B | D | D | D | D | B | D | S | S | S |
| 13 | private endpoints | D | D | B | D | B | D | D | B | D | S | S | S |
| 14 | Azure Container Registries | D | D | D | D | D | D | D | D | D | S | S | S |
| 15 | backup vaults | D | D | D | D | D | D | D | D | D | S | S | S |
| 16 | App Configuration | D | D | D | D | D | D | D | H | D | S | S | S |
| 17 | Application Insights | D | D | D | D | D | D | D | D | D | S | S | S |
| 18 | Managed Grafana | D | D | D | D | D | D | D | D | D | S | S | S |
| 19 | Managed Prometheus | D | D | D | D | D | D | D | D | D | S | S | S |
| 20 | Log Analytics Workspaces | D | D | D | D | D | D | D | D | D | S | S | S |
| 21 | Virtual Machines | D | D | D | D | D | D | D | D | D | S | S | S |
| 22 | Virtual Machine Scale Sets | D | D | D | D | D | D | D | D | D | S | S | S |
| 23 | Automation accounts | D | D | D | D | D | D | D | D | D | S | S | S |

## Domain legend

- **I:** Identity, authentication, authorization and privileged access
- **N:** Public exposure, resource restrictions and private connectivity
- **R:** Encryption and protection at rest
- **T:** Transmission protection
- **K:** Secrets, certificates and key lifecycle
- **L:** Audit generation, retention, protection and collection health
- **C:** Secure configuration, change approval and drift
- **V:** Vulnerabilities, patching, versions and software supply chain
- **B:** Backup, recovery, restore tests and availability
- **O:** Inventory, ownership and lifecycle
- **D:** Detection, incident monitoring and response
- **G:** Governance, access review, exceptions, privacy and shared controls

## Explicit limitations and unresolved decisions

- No live population, permissions or audit-period evidence was inspected. Existence or absence of any deployment is unknown.
- App registration Graph objects, Event Grid families, modern Redis database children, Grafana, Prometheus and Automation need new collectors; existing encryption coverage remains separately documented.
- Configuration evidence does not replace authorization decisions, access reviews, HR/training, provider assurance, log review, remediation outcomes, restore exercises or incident handling.
- Private endpoints and managed identities remain in scope despite narrow at-rest N/A. Networks have shared owners; no network administration is authorized.
- All proposed API properties/paths must be checked against the selected cloud/tier/API version and permission model before implementation; unsupported fields become gaps rather than negative/positive defaults.
- Event Grid subtypes, backup family, modern Redis SKU, Functions hosting, Cosmos API/Mongo variants and tenant application population remain scope decisions. They do not prevent recording the candidate checks.
- A research cell only establishes that the domain was considered. Approval of applicability/criteria and real evidence collection remain separate work.

Run `python3 docs/audit/validate_catalog.py` to reproduce structural/control/source coverage checks.
