# Restricted Kubernetes workload evidence

This path imports a Kubernetes API export against one exact saved AKS resource. It projects safe fields before publication, assesses explicit criteria and archives a separate workload supplement. Source run facts and results are unchanged. For operator imports, exporter identity, cluster association, export time and completeness remain operator assertions. The separately enabled authenticated Functions collection path is described below.

Use [synthetic export](../examples/kubernetes-export.json) and [synthetic criteria](../examples/kubernetes-criteria.json) only with fixture runs. These intentionally contain secret canaries that must disappear from every archived/exported result. The criteria are software-test expectations, not a recommended or approved workplace baseline.

## Input and scope

The exact envelope contains `schema_version: "1.0"`, `kind: "kubernetes_export"`, `mode`, `cluster_id`, `collected_at`, `scope`, `pods` and `nodes`.

- `mode` is `synthetic` for fixture runs or `operator_export` for real collected runs.
- `cluster_id` is the lowercase exact ARM ID of an AKS resource already present in the selected source archive. Unknown clusters and non-AKS resources are rejected.
- `collected_at` is a timezone-qualified timestamp supplied by the exporter.
- `scope` contains exactly `namespace` (one namespace, or null for the supplied all-namespace view) and `pods_complete` (explicit boolean). A selected namespace cannot contain pods from another namespace.
- `pods` is a Kubernetes `v1` `PodList`, with metadata and items. A continuation token or positive remaining-item count keeps population coverage incomplete. Empty populations are incomplete, never an all-clear.
- `nodes` is a `v1` `NodeList`. Only node name and operating-system hints are used; the raw document is discarded. An empty node list is accepted. Pod `spec.os.name` or matching node OS identifies Linux/Windows; absent or conflicting OS leaves Linux-specific checks UNKNOWN. This does not assess node inventory completeness.

Limits: 4 MiB input; 1,000 pods and 1,000 total application/init/ephemeral containers per supplement. Larger scopes need explicitly scoped exports. The project does not silently truncate them or claim tenant-wide coverage. API exports can contain sensitive values: the importer reads the input in memory and never archives the raw export. The original-input SHA-256 is retained for linkage. Retain any original export under your own approved handling controls.

Projection retains pod UID/name/namespace, container name/kind, OS hint, declared image, recognized runtime SHA-256 and eight typed observations. It excludes environment values, commands, arguments, annotations, addresses, status messages, volumes and secret contents. Duplicate pod identities/container names/status entries and status entries for undeclared containers are rejected before any publication.

## Criteria and interpretation

Criteria contain `schema_version`, `id`, `version`, `status` and `checks`. The status is `draft` or `approved`; approval is an operator assertion. Check values must be booleans. Missing/draft criteria leave the corresponding result UNKNOWN.

| Predicate | Observed meaning |
| --- | --- |
| `host_namespaces` | Any of hostNetwork, hostPID or hostIPC is enabled |
| `privileged` | Container privileged setting |
| `allow_escalation` | AllowPrivilegeEscalation, including privileged/SYS_ADMIN cases |
| `run_as_non_root` | Container setting overrides pod inheritance; explicit UID 0 defeats a positive non-root assertion |
| `readonly_root` | ReadOnlyRootFilesystem setting |
| `declared_digest` | Declared image reference has an explicit SHA-256 digest, not merely a tag |
| `runtime_digest_known` | Container status supplies a recognized SHA-256 image identity; absent/unrecognized status stays UNKNOWN |
| `declared_runtime_digest_match` | Declared and reported SHA-256 values match; absence stays UNKNOWN |

Application, init and ephemeral containers are all assessed. Kubernetes defaults are applied for omitted privileged/host namespace/read-only-root flags and privilege escalation; unset runAsNonRoot remains UNKNOWN. Linux-specific checks stay UNKNOWN for Windows and unknown OS. Image digest equality is only a comparison of supplied values: it does not prove runtime integrity, signature trust or vulnerability-scan coverage. Multi-architecture image indexes and runtime image/config digests may legitimately differ; choose criteria with that distinction in mind. All returned pods are assessed, including completed/terminating pods retained in the export; no claim of current execution is made.

Supply `as_of` and a positive `max_age_seconds` up to one year. Stale/future exports leave results UNKNOWN. Partial population coverage remains visible even when an observed container fails. The selected scope, criteria, timestamps, rule version, source hash and NIST objective definitions are frozen; historical reads and PDFs do not rerun projection or assessment.

## Local CLI

```sh
python -m azure_at_rest kubernetes-import --store /absolute/archive --run-id r-EXACT --input export.json --criteria criteria.json --as-of 2026-09-20T02:00:00Z --max-age-seconds 3600
python -m azure_at_rest kubernetes-show --store /absolute/archive --evidence-id k-EXACT
python -m azure_at_rest kubernetes-pdf --store /absolute/archive --evidence-id k-EXACT
```

Use actual returned identifiers: prefix plus 32 hexadecimal characters. Criteria may be omitted to retain unassessed evidence. Import completion/exit zero means publication succeeded, not that workload criteria passed. The manifest includes the assessment summary. Each publication writes an intent first and a completion manifest last; hash verification rejects tampered or incomplete archives. PDF commands return the immutable object key and digest.

## Azure Functions

Set `CG_WORKLOAD_ENABLED=true` to register two optional Function-key-protected POST endpoints. Default is disabled. Existing identity, storage, expiry and execution-budget settings apply. These import/report operations need evidence Blob access, with no additional Kubernetes/ARM/Graph calls.

- `/api/workloads/kubernetes/import`: exact JSON keys `run_id`, `document`, `criteria` (object or null), `as_of`, `max_age_seconds`.
- `/api/workloads/kubernetes/reports`: exact JSON key `evidence_id`.

Use `x-functions-key`. Success returns 201; malformed envelopes return 400; overlapping same-process operations return 409; execution failures return a sanitized 500. Semantic document validation runs before publication. No raw input or provider exception is emitted to logs. Source authenticity and automatic live collection require a separate authorized collection path; possession of an upload key does not authenticate the original Kubernetes export.

References: [Pod API](https://kubernetes.io/docs/reference/kubernetes-api/core/pod-v1/), [security context defaults/inheritance](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/), [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/). These scoped predicates do not certify the full standards or close whole NIST objectives.

## Authenticated collection in Azure Functions

Version 0.11.0 adds an independently enabled, read-only collection endpoint. Set `CG_KUBERNETES_COLLECTION_ENABLED=true` and configure `CG_KUBERNETES_TARGET_JSON` as a JSON object with exactly:

- `cluster_id`: the lowercase ARM ID of one AKS cluster in the configured subscription/resource-group scope and the exact saved source run.
- `endpoint`: its HTTPS API server DNS name, with no credentials, port override, query or custom path.
- `ca_pem`: the public PEM CA certificate for that API server. No private key or kubeconfig is accepted.
- `namespace`: one namespace or `null` for cluster-wide pod listing.
- `criteria`: the same explicit workload criteria object used by the importer, or `null` for observations without approved decisions.
- `max_age_seconds`: a positive freshness limit, at most 31536000.

POST `{"run_id":"r-<saved-run-id>"}` to `/api/workloads/kubernetes/collect` with its Function key. No target, bearer token or criteria override is accepted in the request. The source run must be a live Azure run. The response identifies a separately archived Kubernetes supplement; generate its PDF through the existing workload report endpoint. Enable `CG_WORKLOAD_ENABLED` if that report endpoint is needed. A 201 means the archive completed: inspect `summary.coverage_incomplete` and `summary.conclusion` for evidence coverage and findings.

The host uses its configured UAMI to validate subscription/tenant metadata, read the exact AKS ARM resource, compare the configured API endpoint with its current `fqdn` or `privateFQDN`, and require managed Entra integration. It requests the public-cloud AKS server audience, then makes GET-only pod and node list requests with CA and hostname verification. It does not obtain administrator credentials or call credential-listing actions. Redirects and environment proxy forwarding are disabled. Private clusters require working Function-to-cluster routing and DNS.

Grant only the required ARM reads and Kubernetes `list` access to pods in the selected namespace (or cluster scope) and nodes at cluster scope, using the cluster's configured authorization system. Those API permissions can expose raw pod specifications in memory, including literal environment values. The collector discards excluded fields before archiving and never logs response bodies or tokens. Function-key authorization permits collection of the one configured target and still requires the existing host identity, evidence storage and execution settings.

Collection is bounded to 100 pages per list, 1000 pods, 10000 nodes, 1000 projected containers, and 4 MiB per response and assembled import document. Paging requires a consistent resource version within each list. Pod and node lists are independent snapshots. Denials, interrupted pagination, repeated tokens, version changes and population limits retain explicit collection states and incomplete coverage. Invalid projected data, combined document overflow, expired execution deadlines or archive failures fail the operation without publishing a completed supplement. The collection deadline and retry settings reuse the host settings. This endpoint is on demand; ARM's existing timer does not silently add Kubernetes collection.

Authenticated collection provenance is internal to this path. The external import endpoint cannot label an uploaded document as an authenticated live collection. Operator exports and prior supplements remain readable without reassessment. The adapter and Functions endpoint are tested locally; live AKS identity, RBAC, TLS and networking acceptance remain required at work. No AKS cluster was provisioned in the personal subscription.

Primary references: [AKS authentication and server audience](https://learn.microsoft.com/en-us/azure/aks/kubelogin-authentication), [Kubernetes consistent list pagination](https://kubernetes.io/docs/reference/using-api/api-concepts/).

The fresh cluster read uses [AKS ARM API 2024-10-01](https://github.com/Azure/azure-rest-api-specs/blob/main/specification/containerservice/resource-manager/Microsoft.ContainerService/aks/stable/2024-10-01/managedClusters.json).
