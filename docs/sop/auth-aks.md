# AuthN/AuthZ SOP - AKS (Prod)

## Cluster Auth
- AAD-enabled AKS; Azure RBAC for Kubernetes.
- Admins via Entra group; developers with limited namespaces.

## Workload Identity
- Enable workload identity; ServiceAccounts federated to user-assigned identities.
- Avoid legacy pod identity; no kubelet identities for app creds.

## Network
- Private cluster preferred; Azure CNI; limit API server access; Azure Policy addon.
- NetworkPolicies: default deny; allow only required namespaces/ports.

## Secrets
- Use CSI Secret Store with Key Vault provider; no plain secrets in manifests.

## Ingress
- WAF/AGIC or Nginx with mTLS/OIDC as needed; restrict Temporal UI; backend via WAF.

## Auditing
- Enable audit logs to Log Analytics; Azure Policy for baseline.
# SOP: AKS (Prod)
- Cluster: private or with authorized IPs; Azure CNI; workload identity enabled.
- Identities: service accounts per workload with federated credentials; bind to user-assigned MI.
- RBAC: least privilege Azure roles on MI; Kubernetes RBAC (namespaces, roles, rolebindings).
- Network Policies: default deny; allow API→Zep, Worker→Temporal, API→Postgres; block egress except required.
- Ingress: WAF/APIM in front of API/MCP; internal services cluster-only.
- Secrets: CSI Secret Store + Key Vault provider; no k8s secrets with static creds.
- Auditing: enable Azure Policy add-on; audit logs to Log Analytics; alert on forbidden/denied events.
# Auth SOP – AKS (Prod)

## Cluster
- Private cluster; Azure CNI; Azure Policy addon; audit logs to Log Analytics.
- Enable workload identity; disable legacy pod-managed identities.

## Identity
- ServiceAccounts per workload with federated identity to UAI; least privilege role bindings.
- No kubelet AAD pod identity.

## Network
- NetworkPolicies: default deny; allow api→zep, worker→temporal, ui limited.
- Ingress via WAF/APIM only; restrict kube-api by IP/VNet peering.

## Secrets
- CSI Key Vault provider for secrets; prefer MI where possible.

## RBAC
- Admin via AAD groups; no local accounts; use ClusterRoles scoped per team.
# SOP: AKS (Prod)

## Identity
- Enable workload identity; federated ServiceAccounts per workload (api, worker, temporal, zep).
- Bind to user-assigned MI with least privilege.

## AuthZ
- Kubernetes RBAC: devops (cluster-admin limited), app teams (namespace-scoped), readonly (view).

## Network
- Private cluster optional; Azure CNI; network policies default-deny per namespace.
- Ingress with WAF; mTLS for internal services where applicable.

## Secrets
- Use CSI Secrets Store with Key Vault provider; no plain Secrets for prod secrets.

## Monitoring
- Azure Monitor for containers; audit kube-apiserver; alert on privilege escalations.

