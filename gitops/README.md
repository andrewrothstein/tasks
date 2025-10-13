# Local GitOps Manifests

This directory contains Flux-based GitOps manifests for deploying ArgoCD and its dependencies.

## Structure

```
gitops/
├── clusters/
│   ├── ephemeral/base/          # For Kind, K3d (NodePort access)
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   └── argocd.yaml
│   │
│   └── on-prem/base/            # For Harvester, K3s (Tailscale ingress)
│       ├── kustomization.yaml
│       ├── namespace.yaml
│       ├── helm-repos.yaml      # Flux HelmRepositories
│       ├── tailscale-operator.yaml
│       ├── metrics-server.yaml
│       └── argocd.yaml          # ArgoCD with Tailscale ingress
```

## Deployment Order (Flux manages this automatically)

For on-prem clusters:

1. **Helm Repositories** - argo, tailscale, metrics-server
2. **Tailscale Operator** - Required for Tailscale ingress
3. **Metrics Server** - Cluster metrics
4. **ArgoCD** - Depends on Tailscale operator, deployed with Tailscale ingress

## Bootstrap Methods

### Method 1: Local Flux Bootstrap (Recommended for testing)

```bash
# Set Tailscale credentials
export TAILSCALE_OPERATOR_CLIENT_ID=xxx
export TAILSCALE_OPERATOR_CLIENT_SECRET=xxx

# Bootstrap Harvester with Flux
CLUSTER_TYPE=on-prem CLUSTER_NAME=harvester task -t bootstrap-flux-local.yml bootstrap

# Monitor deployment
flux get helmreleases -A
watch kubectl get pods -n argocd
```

### Method 2: Direct kubectl apply (Quick test)

```bash
# Apply manifests directly
kubectl apply -k gitops/clusters/on-prem/base/

# Watch deployment
watch kubectl get pods -n argocd -n tailscale
```

## On-Prem (Harvester/K3s) Configuration

The on-prem configuration deploys:

### 1. Tailscale Operator
- Namespace: `tailscale`
- Provides Tailscale ingress class
- Requires: `TAILSCALE_OPERATOR_CLIENT_ID` and `TAILSCALE_OPERATOR_CLIENT_SECRET`

### 2. Metrics Server
- Namespace: `kube-system`
- Provides cluster metrics
- Configured with `--kubelet-insecure-tls` for development

### 3. ArgoCD
- Namespace: `argocd`
- Single replica deployment
- **Tailscale Ingress**: `argocd.elephant-frog.ts.net`
- Ingress class: `tailscale`
- Depends on Tailscale operator being ready

## Accessing ArgoCD

### On Harvester (on-prem)
```bash
# Via Tailscale ingress (once deployed)
https://argocd.elephant-frog.ts.net

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d
```

### On Kind (ephemeral)
```bash
# Via NodePort
http://localhost:30080

# Or port-forward
kubectl port-forward -n argocd svc/argocd-server 8080:443
https://localhost:8080
```

## Monitoring Flux

```bash
# Check Flux status
flux check

# View all Flux resources
flux get all

# View Kustomizations
flux get kustomizations

# View HelmReleases
flux get helmreleases -A

# Force reconciliation
task -t bootstrap-flux-local.yml sync
```

## Troubleshooting

### Tailscale Operator Issues
```bash
# Check operator logs
kubectl logs -n tailscale deployment/tailscale-operator

# Verify secrets
kubectl get secret -n tailscale operator-oauth
```

### ArgoCD Not Starting
```bash
# Check HelmRelease status
flux get helmrelease argocd -n argocd

# Check ArgoCD events
kubectl get events -n argocd --sort-by='.lastTimestamp'

# Check pod logs
kubectl logs -n argocd deployment/argocd-server
```

### Flux Not Syncing
```bash
# Check GitRepository status
flux get source git local-gitops

# Check Kustomization status
flux get kustomization cluster-on-prem

# View reconciliation logs
flux logs
```

## Customization

### Change Tailscale Domain
Edit `gitops/clusters/on-prem/base/argocd.yaml`:
```yaml
global:
  domain: your-domain.ts.net

server:
  ingress:
    hosts:
      - your-domain.ts.net
```

### Add More Dependencies
Add to `gitops/clusters/on-prem/base/kustomization.yaml`:
```yaml
resources:
  - your-app.yaml
```

Create `your-app.yaml` as a Flux HelmRelease.

## Benefits of This Approach

1. **All in tasks repo** - No external GitOps repository needed
2. **Version controlled** - Manifests tracked in git
3. **Flux manages dependencies** - Tailscale deployed before ArgoCD
4. **Declarative** - Desired state in YAML
5. **Easy testing** - Apply directly with kubectl or Flux
6. **Cluster-type specific** - Different configs for ephemeral vs on-prem
