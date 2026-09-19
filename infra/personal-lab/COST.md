# Personal lab: 30-day incremental cost model

Prepared 2026-09-19, East US, public USD retail, before tax. **Not a bill guarantee or permission to provision.** Terraform here is only for the home lab; workplace infrastructure uses the user's existing patterns. The user confirmed this subscription is intended for the project and will be short-lived until workplace handoff; this does not prove current bill rows or pending charges are zero. Existing personal subscription charges are separate and must be included in the user's **less-than-$25 total monthly bill** condition.

## Rates and complete proposed resource set

[Captured public rates](retail-rates-2026-09-19.json): Standard General Block Blob v2 Hot LRS capacity $0.0208/GB-month; write/list/create $0.05/10,000; read/other $0.004/10,000. Functions Flex on-demand $0.000026/GB-second and $0.000004/10 executions. [Internet egress](https://azure.microsoft.com/en-us/pricing/details/bandwidth/) from North America is modeled at $0.087/GB even if the shared first-100-GB allowance is unavailable. Ingress and same-region transfer are free under the referenced public pricing. No free compute grant, credit or discount is assumed.

Proposed resources: one RG, one UAMI, one FC1 plan/Function App, two StorageV2 Standard LRS Hot accounts, two explicit private containers, one SCM basic-auth policy, two custom role definitions and five role assignments (16 Terraform resources). The runtime may create host/key/lease containers in the runtime account. RBAC, the RG and UAMI have no independent usage charge in this model; the FC1 plan is billed through Function execution. SCM is configuration, not another paid service. One maximum on-demand 2-GB instance **per function group**; zero always-ready. HTTP/probe share one group and the timer is separate, so two instances may run concurrently.

No Azure Files share, queue/table binding, durable task backend, database, VM, VNet, private endpoint, NAT, public-IP resource, Premium plan, geo replication, diagnostic destination, paid logging workspace, Application Insights, Defender feature, retention lock or budget notification is proposed. A platform/policy dependency that introduces one requires a revised plan and estimate before proceeding. Host storage/API retries are included in the transaction assumptions, not claimed to be free.

## Full 30 days, without free allowances

| Component | Base usage | Base USD | Adverse usage | Adverse USD |
| --- | --- | ---: | --- | ---: |
| Combined runtime/package/evidence capacity | 2 GB average x 30/30 | 0.0416 | 10 GB average | 0.2080 |
| Combined write/list/create operations | 100,000 | 0.5000 | 1,000,000 | 5.0000 |
| Combined read/other operations | 100,000 | 0.0400 | 1,000,000 | 0.4000 |
| Execution memory-time | 100 x 60 seconds x 2 GB | 0.3120 | 500 x 120 seconds x 2 GB | 3.1200 |
| Invocation charges | 100 | 0.00004 | 500 | 0.0002 |
| Internet egress, PDFs/package retrieval | 1 GB | 0.0870 | 5 GB | 0.4350 |
| **Modeled incremental total** | | **0.98064** | | **9.1632** |

The capacity envelope includes several deployment package versions plus JSON/PDF/probe objects and host data; the local built package is measured in the validation record. The transaction envelope includes leases, host polling, indexing, deployment, assessment/report reads/writes, denied/conflicting requests and retries. Exact platform counts must be measured after an authorized test. There is no fixed per-storage-account charge for these standard Blob-only assumptions. Free grants, if still eligible and unused, lower the estimate; they are not needed to obtain the figures above.

These scenarios are bounded workload models, not maximum possible charges. One continuously executing 2-GB instance for 30 days alone is approximately **$134.78** at the quoted compute rate; even seven continuous days is about **$31.45**. A second scale group doubles compute exposure. Restricting scale does not enforce a $25 bill. Wrong schedules, leaked function keys, retry storms, external policy exports, unknown existing services and delayed metering can exceed the estimates.

Target the actual short lab at **under $2 incremental**, finish within 24 hours where practical, and require review again if observed or projected lab spend reaches $2 or activity exceeds the base envelope. Use a conservative **$12 incremental planning reserve**, plus tax and existing/expected personal charges, when checking whether the total can remain below $25. The reserve is not an Azure limit or permission to spend it. If existing charges or uncertainty consume that headroom, do not apply. Keep disabled defaults, restrict the operator /32, use at most two collections, three reports and two probes for acceptance, and target handoff/cleanup within seven days after preserving requested artifacts. Cleanup is authorized after successful workplace handoff; if handoff takes longer, disable the lab and review lifetime/cost instead of silently extending it or deleting early.

The earlier seven-day example ($0.55 storage; $0.86 storage+compute, fully billed) used 2 GB prorated for seven days, 100,000 transactions in each category and 100 one-minute invocations. It excluded explicit egress and existing costs. This record is a separate 30-day model, not an extrapolation of a measured lab bill.

## Financial gate

Read both calendar MonthToDate and BillingMonthToDate actuals and the forecast in their returned currency. Confirm the billing period, pending/delayed charges, existing recurring resources, support/marketplace commitments and taxes in the billing portal. Empty API rows or an unavailable forecast are **unresolved**, not $0. Keep actual personal billing responses outside this public-source repository. The private preflight record, not this generic template, records the observed account status.

Azure [spending limits](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/spending-limit) are not configurable custom dollar caps on Pay-As-You-Go. [Budgets](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets) notify; they do not stop resources automatically. No email/alert recipient has been supplied, so no notifications are configured. If an absolute guaranteed $25 bill is mandatory, do not run a chargeable PAYG lab: continue offline tests or independently review an eligible credit-limited offer without upgrading/enrolling automatically.

Sources: [Functions pricing](https://azure.microsoft.com/en-us/pricing/details/functions/), [Blob pricing](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/), [retail API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices), [managed identities](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview), [Flex scaling/quotas](https://learn.microsoft.com/en-us/azure/azure-functions/flex-consumption-plan). Refresh prices and inherited policies immediately before any approved apply.
