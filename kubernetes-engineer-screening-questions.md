# Kubernetes Engineer Screening Questions

Pass = 4 of 5. Each question allows one nudge; if they can't go further after it, mark it failed.

We are not looking for textbook answers. We want people who have broken and fixed these things in production. Each question has a "what a real answer sounds like" note; if the candidate never volunteers a story like those, ask "tell me about a time this bit you." No story, no pass.

---

## Q1. Private AKS networking

**Ask:** "We run private AKS clusters only, in a hub-and-spoke network with all egress through Azure Firewall. Explain how a private cluster differs from a public one, how an engineer on the corporate network reaches the API server, how an internal app gets exposed, and what breaks when egress is forced through a firewall."

**One allowed nudge:** "OK, so how does my laptop on the office network actually connect to it?"

> **Recruiter note: "private endpoint" alone is a FAIL.** Almost every candidate will say "the API server uses a private endpoint." That is the definition, not the answer. To pass they must explain all three of the following, unprompted or after the one nudge: (1) **DNS**: the API server name resolves through a Private DNS zone that must be linked to the hub network or forwarded from corporate DNS. If they never say the word DNS, they have not run one of these. (2) **Network path**: peering, ExpressRoute or VPN into the spoke, or a jumpbox, Bastion or `az aks command invoke`. (3) **Egress rules**: the firewall must allow AKS's required destinations or nodes never come up. If they stop at "private endpoint" after the nudge, mark it failed and move on.

**Expected answer**

- A private cluster's API server has no public IP. It is reached through a Private Endpoint in the cluster VNet plus a Private DNS zone named `privatelink.<region>.azmk8s.io`, or through API Server VNet Integration. "Authorized IP ranges" is the public-cluster control and does not apply here.
- Reaching it needs both a network path and DNS. The private DNS zone is linked to the hub VNet, or corporate DNS forwards to an Azure Private DNS Resolver. Most "I can't reach the cluster" tickets turn out to be DNS.
- Internal exposure uses a LoadBalancer Service annotated `service.beta.kubernetes.io/azure-load-balancer-internal: "true"`, optionally pinned to a subnet, fronted by an ingress controller or Application Gateway for Containers. No public IP anywhere. Private DNS records point at the internal load balancer IP.
- Forced egress means a route table sending `0.0.0.0/0` to the firewall with the cluster set to `outboundType: userDefinedRouting`. Nodes fail to bootstrap or go NotReady unless the firewall allows AKS's required FQDNs: MCR, ACR, Entra login endpoints, OS update repos and `*.hcp.<region>.azmk8s.io`. This needs application rules or the `AzureKubernetesService` FQDN tag, not only IP-based network rules.
- CNI choice: Azure CNI Overlay gives pods a private CIDR and avoids VNet IP exhaustion. Azure CNI with a pod subnet gives routable pod IPs, needed if on-prem must reach pods directly. Kubenet is deprecated.
- Bonus: Private Link for ACR and Key Vault, Cilium data plane and NetworkPolicy, CoreDNS forwarding to Azure DNS at `168.63.129.16` with conditional forwarders for on-prem domains, NSG on the node subnet.

**Must hear:** private DNS zone and how the hub resolves it, network path, internal load balancer annotation, `userDefinedRouting` and required egress FQDNs.

**Red flags**

- Says "private endpoint" and nothing more, even after the nudge.
- Never says DNS.
- Offers authorized IP ranges or NSGs as what makes the cluster private.
- Has never heard of `outboundType` or AKS egress requirements.
- Proposes a public load balancer "just temporarily."

> **Recruiter note: what a real answer sounds like.** Break/fix: "the cluster upgrade hung because the firewall blocked a new FQDN," "nobody could kubectl from the office until we linked the DNS zone to the hub." Design decisions: "we went with CNI Overlay because the pod-subnet model was eating /22s per cluster," "we chose API Server VNet Integration over a private endpoint so we didn't have to manage the DNS zone links in every spoke," "we put ACR behind Private Link and hit egress problems until we added its DNS zone too."

---

## Q2. Zero-downtime cluster upgrades

**Ask:** "You have to upgrade a production AKS cluster two Kubernetes minor versions with no user-visible downtime. Walk me through it: what you check before, how the upgrade actually moves pods, what you configure on workloads so they survive it, and what goes wrong most often."

**One allowed nudge:** "What stops the upgrade from evicting all the pods of one app at once?"

> **Recruiter note: "click upgrade in the portal" or "run `az aks upgrade`" is a FAIL.** The command is the easy part. This question is about whether they understand what happens to running applications during the upgrade. If they never say **PodDisruptionBudget** (or "PDB") on their own or after the nudge, mark it failed. If they say PDB but cannot explain that a badly written one **stalls the whole upgrade**, mark it weak.

**Expected answer**

- Before: check `az aks get-upgrades`. AKS supports one minor version at a time, so this is two sequential upgrades. Scan for removed APIs with `kubectl-convert`, Pluto or the AKS deprecated-API check. Confirm add-ons and CRDs such as ArgoCD, cert-manager and CSI drivers support the target version. Test in a lower environment first, or bring up a new node pool and migrate.
- Mechanics: the control plane upgrades first, then node pools. AKS adds surge nodes (`maxSurge`), then cordons and drains old nodes one at a time. Drain honours PodDisruptionBudgets. Node soak time and planned maintenance windows limit the blast radius.
- Workload configuration that makes it survivable:
    - A PDB with `minAvailable` or `maxUnavailable`. A PDB that can never be satisfied, such as `minAvailable: 1` on a one-replica deployment, blocks the drain and stalls the upgrade until AKS times out and fails the node.
    - At least two replicas spread across nodes or zones with `topologySpreadConstraints` or anti-affinity.
    - Correct readiness probes so new pods do not take traffic early, plus a `preStop` hook and `terminationGracePeriodSeconds` so in-flight requests finish. They should be able to explain the race between endpoint removal and SIGTERM, which is why a short `sleep` in `preStop` is common.
    - Deployment `maxUnavailable: 0` with a `maxSurge` for the app's own rollouts.
- What goes wrong: unsatisfiable PDBs stalling the drain, pods with local `emptyDir` state, single-replica services, removed API versions breaking Helm charts or ArgoCD sync, not enough subnet IPs or quota for surge nodes, and long-running Jobs killed mid-run.
- Bonus: auto-upgrade channels and the node OS channel, upgrading system and user node pools separately, migrating to a second node pool with taints instead of upgrading in place, `kubectl drain --ignore-daemonsets --delete-emptydir-data` semantics, watching events for `EvictionBlocked`.

**Must hear:** one minor at a time, deprecated API check, cordon and drain honours PDB, a PDB can block the drain, readiness plus `preStop` plus grace period, multiple replicas spread across nodes.

**Red flags**

- "Just click upgrade in the portal."
- Does not know what a PDB is, or that it can stall an upgrade.
- Cannot explain why users see 502 errors during a rollout.
- Never mentions API deprecations.
- Thinks a single replica with a liveness probe is enough.

> **Recruiter note: the 502 test.** A good follow-up is "why do users sometimes get 502s for a few seconds when a pod is replaced, even with readiness probes?" The right answer is about the pod receiving SIGTERM before the load balancer has stopped sending it traffic, fixed with a `preStop` sleep and a long enough grace period. Anyone who has run a busy production cluster has been burned by this and will answer quickly. A blank look here means they have only run clusters where nobody noticed the outages.

> **Recruiter note: what a real answer sounds like.** "The upgrade sat at 60% for two hours because one team had a PDB with `minAvailable: 1` on a single replica," "we ran out of IPs in the subnet when the surge nodes came up," "the 1.25 upgrade broke half our Helm charts because of the PodSecurityPolicy removal." Design decisions: "we run Pluto in CI so deprecated APIs never reach the cluster," "we upgrade by standing up a new node pool and shifting workloads with taints rather than in place, so rollback is just cordoning the new pool," "we enforce a default PDB and two replicas through a Kyverno policy because teams kept forgetting," "we set `maxSurge` to 33% after the 1-node default made upgrades take all night."

---

## Q3. Failed pod triage and rollback

**Ask:** "You deploy a new version and the pods are stuck. One is in `CrashLoopBackOff`, one is in `Pending`, and one is in `ImagePullBackOff`. What does each status mean, what commands do you run to find the cause, and how do you get production back to a working state quickly?"

**One allowed nudge:** "The container already crashed, so `kubectl logs` shows nothing. What now?"

> **Recruiter note: this is the baseline question.** Anyone calling themselves a Kubernetes engineer must pass this without hesitation. It is deliberately the easiest of the five. If they struggle here, the interview can stop; do not let a strong Q4 or Q5 answer compensate. The tell is the nudge: a real engineer says `--previous` instantly. Someone who has to think about it has not debugged many crashes.

**Expected answer**

- `CrashLoopBackOff`: the container starts and exits repeatedly and Kubernetes backs off between restarts. Commands: `kubectl logs <pod> --previous` and `kubectl describe pod` to see the exit code and reason. Common causes: application error, bad config or missing env var or secret, OOMKilled (exit code 137), or a liveness probe that is too aggressive.
- `Pending`: the scheduler cannot place the pod on a node. Command: `kubectl describe pod` and read the Events section. Common causes: not enough CPU or memory for the requests, a node selector, affinity rule or taint with no matching node, an unbound PVC, or the cluster autoscaler not scaling up.
- `ImagePullBackOff`: the node cannot pull the image. Common causes: wrong image name or tag, registry auth (on AKS, ACR not attached to the cluster or a missing `imagePullSecret`), or the registry unreachable through the firewall. On our private clusters, the firewall or ACR Private Link is a likely culprit.
- Recovery: `kubectl rollout undo deployment/<name>`, or in a GitOps shop revert the commit in Git. With a rolling update the old pods are still serving because the rollout stalls rather than taking the app down, provided readiness probes and `maxUnavailable` are set sensibly.
- Bonus: `kubectl get events --sort-by=.lastTimestamp`, `kubectl rollout status` and `rollout history`, `kubectl debug` with ephemeral containers, explaining liveness versus readiness versus startup probes. A candidate who says "in an ArgoCD environment a manual `rollout undo` gets reverted by selfHeal, so the fix must go through Git" understands how Q4 applies here.

**Must hear:** `describe` and Events, `logs --previous`, scheduling and resources for Pending, registry auth for ImagePull, `rollout undo` or Git revert.

**Red flags**

- "Delete the pod" or "restart the cluster" as the diagnosis.
- Does not know `--previous`.
- Cannot tell the three statuses apart.
- No rollback plan, or edits production directly with no mention of Git.

> **Recruiter note: listen for order.** Strong candidates diagnose in a fixed order: `describe` first, then logs, then events. They also say what they would do *before* diagnosing: roll back so users are unaffected, then investigate. A candidate who wants to debug live in production while users wait is a red flag even if the technical content is right.

> **Recruiter note: what a real answer sounds like.** "Exit code 137, turned out the new version needed more memory than the limit," "Pending for ten minutes because the autoscaler hit the VM quota in that region," "ImagePullBackOff after we moved ACR behind Private Link and forgot the DNS zone," "the liveness probe was killing it before the JVM finished starting, so we added a startup probe." Design decisions: "we set `maxUnavailable: 0` on every prod Deployment so a bad image never takes capacity away," "we pin image digests instead of tags so a re-pushed tag can't surprise us," "we added a `progressDeadlineSeconds` so a stuck rollout fails the pipeline instead of hanging forever."

---

## Q4. ArgoCD and GitOps

**Ask:** "Someone runs `kubectl edit` on a production Deployment that ArgoCD manages. What happens? And how would you manage 50 apps across dev, stage and prod clusters?"

**One allowed nudge:** "Does ArgoCD put it back automatically, or not? What decides that?"

> **Recruiter note: "it goes OutOfSync" is only half a pass.** Everyone who has opened the ArgoCD UI knows the red OutOfSync badge. The pass criterion is whether they know *what decides* if ArgoCD reverts the change: the **selfHeal** setting. They must also name **prune** as a separate setting. A candidate who uses those two words interchangeably, or does not know them, has clicked Sync in the UI but never configured ArgoCD. Mark failed.

**Expected answer**

- The app goes OutOfSync. If automated sync has `selfHeal` on, ArgoCD reverts it to match Git within a few minutes. Without `selfHeal` it stays drifted until someone syncs. `prune` is a separate setting that deletes resources removed from Git.
- Git is the source of truth. Changes go through a pull request, not kubectl.
- At scale they use ApplicationSets with git, cluster or matrix generators, or the app-of-apps pattern, with per-environment overlays in Kustomize or Helm values.
- AppProjects restrict which repos, clusters and namespaces each team can deploy to, backed by RBAC and SSO.
- Sync waves or hooks handle ordering, for example CRDs before the resources that use them.
- `ignoreDifferences` handles fields mutated by controllers, such as HPA replicas or webhook-injected fields.
- Secrets are never stored in plain Git. They use External Secrets Operator, Sealed Secrets or the Key Vault CSI driver. On our stack the expected answer ties this to Workload Identity from Q5.

**Must hear:** OutOfSync, `selfHeal`, `prune`, ApplicationSet or app-of-apps, a strategy for secrets.

**Red flags**

- "Our CI pipeline runs `kubectl apply` or `helm upgrade`." That is push-based deployment, not GitOps.
- Does not distinguish `selfHeal` from `prune`.
- Commits secrets to Git, encrypted or not, without naming a proper tool.
- Has only ever clicked Sync in the UI.

> **Recruiter note: the secrets follow-up.** Ask: "Where do the database passwords live?" A pass names one of External Secrets Operator, Sealed Secrets or the Key Vault CSI driver and can say why. "In a Kubernetes Secret" is not an answer; ask where that Secret comes from. "In the Git repo, base64 encoded" is an instant fail: base64 is not encryption, and anyone who thinks it is should not have production access.

> **Recruiter note: what a real answer sounds like.** "Someone hot-fixed prod with kubectl and selfHeal reverted it three minutes later, mid-incident, so now we know to pause auto-sync first," "prune deleted a namespace because a folder got renamed in the repo," "the HPA and ArgoCD fought over the replica count until we added `ignoreDifferences`," "the CRDs synced after the resources that used them until we set sync waves." Design decisions: "we chose ApplicationSets with a cluster generator over app-of-apps because adding a cluster became a label instead of a PR," "we turned selfHeal on in prod but off in dev so developers can experiment," "we picked External Secrets Operator over Sealed Secrets so rotating a secret in Key Vault didn't need a Git commit," "one AppProject per team so nobody can deploy into another team's namespace."

---

## Q5. AKS Workload Identity (federated auth)

**Ask:** "A pod on AKS needs to read from Azure Key Vault with no secrets or passwords stored anywhere. How do you set it up, end to end?"

**One allowed nudge:** "How does Entra know that *this* pod is allowed to be that identity and not some other pod?"

> **Recruiter note: "managed identity" alone is a FAIL.** Every Azure engineer says "use a managed identity." The question is how a pod, which is not an Azure resource, gets to *be* that identity. The pass requires the words **federated identity credential** (or "federated credential" or "workload identity federation") and **OIDC issuer**, and they must state that the credential is tied to a specific Kubernetes **ServiceAccount** in a specific namespace. If after the nudge they cannot explain the link between the ServiceAccount and the identity, mark it failed. If they answer with **AAD Pod Identity**, mark it failed: that product is retired and using it shows they have not touched this in years.

**Expected answer:** they name Microsoft Entra Workload ID and give these steps.

1. Enable the OIDC issuer and workload identity on the AKS cluster.
2. Create a user-assigned managed identity, or an app registration.
3. Create a federated identity credential on it with issuer = the cluster's OIDC URL, subject = `system:serviceaccount:<namespace>:<serviceaccount>`, audience = `api://AzureADTokenExchange`.
4. Annotate the Kubernetes ServiceAccount with `azure.workload.identity/client-id` and label the pod `azure.workload.identity/use: "true"`.
5. The mutating webhook injects a projected ServiceAccount token and environment variables. The Azure SDK (`DefaultAzureCredential` or `WorkloadIdentityCredential`) exchanges that token for an Entra access token.
6. Grant the identity an Azure RBAC role on the Key Vault, for example Key Vault Secrets User.

- Bonus: knows AAD Pod Identity is deprecated and this replaces it. Knows the subject must match namespace and ServiceAccount exactly, which is the most common failure. Mentions the Key Vault CSI driver or External Secrets Operator on top of this. Knows the limit of 20 federated credentials per identity. On our private clusters, notes that Key Vault should be reached over Private Link and that the pod needs egress to `login.microsoftonline.com` through the firewall.

**Must hear:** OIDC issuer, federated credential, ServiceAccount annotation, managed identity, RBAC role assignment, no secrets.

**Red flags**

- Stores a service principal client secret in a Kubernetes Secret.
- Recommends AAD Pod Identity as the current approach.
- "Just use the node or kubelet identity." Every pod on the node then shares that access.
- Cannot explain how the token exchange works.

> **Recruiter note: the "it's not working" follow-up.** Ask: "You set it all up and the pod gets `AADSTS70021: No matching federated identity record found`. What did you get wrong?" A pass answers immediately: the subject on the federated credential does not match the namespace or ServiceAccount name, or the issuer URL is wrong. That specific error is the rite of passage for this feature; someone who has done this for real has seen it.

> **Recruiter note: what a real answer sounds like.** "Typo in the namespace on the federated credential, took an hour to spot," "worked in dev, failed in prod because prod had a different ServiceAccount name," "forgot the `azure.workload.identity/use` label so the webhook never injected the token," "hit the 20 federated credential limit and had to split identities per team." Design decisions: "one managed identity per app, not per cluster, so blast radius stays small," "we use the Key Vault CSI driver for TLS certs but ESO for app secrets because the apps only read env vars," "we migrated off AAD Pod Identity a year before retirement so we weren't doing it under pressure," "we scoped RBAC to the individual vault, never the resource group."
