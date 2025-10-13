# GitOps-Based Cluster Bootstrapping

## Overview

This repository uses a **Flux → ArgoCD → ApplicationSets** pattern for cluster bootstrapping:

1. **Flux** bootstraps the cluster and deploys ArgoCD
2. **ArgoCD** is deployed by Flux as a base component
3. **ArgoCD ApplicationSets** handle all other application deployments

This approach eliminates complex conditional logic in Taskfiles - the cluster type determines which manifests get deployed via GitOps.

## Cluster Types

- **ephemeral**: Kind, K3d (local dev, no Tailscale, may have built-in metrics-server)
- **on-prem**: Harvester, K3s (Tailscale ingress, needs metrics-server)
- **cloud**: EKS, GKE, AKS (cloud LB, may have built-in metrics)

## Quick Start

### 1. Create and Bootstrap a Cluster

```bash
# Create Kind cluster
CLUSTER_TYPE=ephemeral CLUSTER_NAME=kind-dev task up

# Bootstrap with Flux → ArgoCD
task bootstrap

# Check status
task cluster-info
```

### 2. Sync Cluster State

```bash
# Trigger Flux reconciliation
task sync

# View ArgoCD UI
task argocd-ui
```

### 3. Switch to External Cluster

```bash
# Switch to Harvester
task use-harvester

# Bootstrap it
CLUSTER_TYPE=on-prem CLUSTER_NAME=harvester task bootstrap
```

## Available Commands

| Command | Description |
|---------|-------------|
| `task bootstrap` | Bootstrap cluster (Flux → ArgoCD) |
| `task sync` | Trigger Flux reconciliation |
| `task cluster-info` | Show cluster type and bootstrap status |
| `task argocd-ui` | Port-forward to ArgoCD UI |
| `task bootstrap:argocd-password` | Get ArgoCD admin password |

## GitOps Repository Structure

Your GitOps repository should be structured by cluster type:

```
gitops-manifests/
├── clusters/
│   ├── flux-system/              # Flux installation manifests (auto-generated)
│   │
│   ├── ephemeral/                # For Kind, K3d
│   │   ├── base/
│   │   │   ├── kustomization.yaml
│   │   │   ├── argocd.yaml       # ArgoCD HelmRelease (NodePort)
│   │   │   └── appset.yaml       # ApplicationSet for this cluster type
│   │   └── kind-dev/
│   │       └── kustomization.yaml
│   │
│   ├── on-prem/                  # For Harvester, K3s
│   │   ├── base/
│   │   │   ├── kustomization.yaml
│   │   │   ├── argocd.yaml       # ArgoCD HelmRelease (Tailscale ingress)
│   │   │   ├── metrics-server.yaml
│   │   │   ├── tailscale-operator.yaml
│   │   │   └── appset.yaml       # ApplicationSet for this cluster type
│   │   ├── harvester/
│   │   │   └── kustomization.yaml
│   │   └── k3s/
│   │       └── kustomization.yaml
│   │
│   └── cloud/                    # For EKS, GKE, AKS
│       ├── base/
│       │   ├── kustomization.yaml
│       │   ├── argocd.yaml       # ArgoCD HelmRelease (Cloud LB)
│       │   └── appset.yaml
│       ├── eks-prod/
│       └── gke-staging/
│
└── apps/                         # Application manifests (referenced by AppSets)
    ├── prometheus/
    │   ├── base/
    │   └── overlays/
    ├── grafana/
    └── ...
```

## Bootstrap Flow

### What Happens During Bootstrap

1. **Cluster labeled** with `cluster-type` and `cluster-name`
2. **Flux installed** via `flux bootstrap github`
   - Points to `clusters/{type}/{name}/` in GitOps repo
3. **Flux deploys ArgoCD** via HelmRelease in cluster-type base
4. **ArgoCD ApplicationSets activate** and deploy remaining apps

### Example: Ephemeral Cluster (Kind)

**clusters/ephemeral/base/kustomization.yaml**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - argocd.yaml          # Deploy ArgoCD
  - appset.yaml          # ApplicationSet for ephemeral clusters
```

**clusters/ephemeral/base/argocd.yaml** (Flux HelmRelease)
```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: argo
  namespace: flux-system
spec:
  interval: 1h
  url: https://argoproj.github.io/argo-helm

---
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: argocd
  namespace: argocd
spec:
  interval: 5m
  chart:
    spec:
      chart: argo-cd
      version: 8.6.0
      sourceRef:
        kind: HelmRepository
        name: argo
        namespace: flux-system
  install:
    createNamespace: true
  values:
    redis-ha:
      enabled: false
    controller:
      replicas: 1
    server:
      replicas: 1
      service:
        type: NodePort      # For local access
        nodePortHttp: 30080
        nodePortHttps: 30443
    repoServer:
      replicas: 1
    applicationSet:
      replicas: 1
```

**clusters/ephemeral/base/appset.yaml** (ArgoCD ApplicationSet)
```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: ephemeral-apps
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - name: prometheus
            namespace: monitoring
          - name: grafana
            namespace: monitoring
  template:
    metadata:
      name: '{{name}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/andrewrothstein/gitops-manifests
        targetRevision: HEAD
        path: 'apps/{{name}}/base'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

**clusters/ephemeral/kind-dev/kustomization.yaml**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../base

# Optional: cluster-specific overrides
```

### Example: On-Prem Cluster (Harvester)

**clusters/on-prem/base/argocd.yaml** (with Tailscale)
```yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: argocd
  namespace: argocd
spec:
  interval: 5m
  chart:
    spec:
      chart: argo-cd
      version: 8.6.0
      sourceRef:
        kind: HelmRepository
        name: argo
        namespace: flux-system
  values:
    redis-ha:
      enabled: false
    controller:
      replicas: 1
    server:
      replicas: 1
      ingress:
        enabled: true
        ingressClassName: tailscale    # Tailscale ingress
        hosts:
          - argocd.elephant-frog.ts.net
    repoServer:
      replicas: 1
    applicationSet:
      replicas: 1
```

**clusters/on-prem/base/kustomization.yaml**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - metrics-server.yaml       # Deploy metrics-server
  - tailscale-operator.yaml   # Deploy Tailscale operator
  - argocd.yaml
  - appset.yaml
```

**clusters/on-prem/base/appset.yaml**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: on-prem-apps
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - name: prometheus
            namespace: monitoring
            overlay: tailscale    # Use Tailscale overlay
          - name: grafana
            namespace: monitoring
            overlay: tailscale
  template:
    metadata:
      name: '{{name}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/andrewrothstein/gitops-manifests
        targetRevision: HEAD
        path: 'apps/{{name}}/overlays/{{overlay}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

## Application Structure

Applications in the `apps/` directory support multiple overlays:

```
apps/
├── prometheus/
│   ├── base/
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   └── helmrelease.yaml        # Base Prometheus config
│   └── overlays/
│       ├── tailscale/
│       │   ├── kustomization.yaml
│       │   └── ingress.yaml        # Tailscale ingress
│       └── cloud/
│           ├── kustomization.yaml
│           └── ingress.yaml        # Cloud LoadBalancer
```

## Workflows

### Create and Bootstrap New Kind Cluster

```bash
# 1. Create cluster
CLUSTER_TYPE=ephemeral CLUSTER_NAME=kind-dev task up

# 2. Bootstrap (Flux → ArgoCD)
task bootstrap

# 3. Wait a few moments, then check
task cluster-info

# 4. Access ArgoCD
task argocd-ui
# Get password: task bootstrap:argocd-password
```

### Bootstrap Existing Harvester Cluster

```bash
# 1. Switch to Harvester
task use-harvester

# 2. Bootstrap
CLUSTER_TYPE=on-prem CLUSTER_NAME=harvester task bootstrap

# 3. Monitor bootstrap
watch kubectl get helmreleases -A
watch kubectl get applications -n argocd
```

### Make Changes and Sync

```bash
# Edit manifests in GitOps repo, commit, push

# Trigger immediate sync
task sync

# Or wait for Flux's automatic reconciliation (default 1m)
```

### Troubleshooting

```bash
# Check cluster info
task cluster-info

# Check Flux status
flux check
flux get all

# Check Flux kustomizations
flux get kustomizations

# Check Flux helmreleases
flux get helmreleases -A

# Check ArgoCD apps
kubectl get applications -n argocd
argocd app list

# Force reconcile
flux reconcile source git flux-system
flux reconcile kustomization flux-system
```

## Environment Variables

Configure in `.env` or via Doppler:

```bash
# Cluster configuration
CLUSTER_TYPE=ephemeral          # ephemeral, on-prem, cloud
CLUSTER_NAME=kind-dev           # Unique cluster identifier

# GitOps repository
GITOPS_REPO=github.com/andrewrothstein/gitops-manifests
GITOPS_BRANCH=main

# Tailscale (for on-prem clusters)
TAILSCALE_OPERATOR_CLIENT_ID=...
TAILSCALE_OPERATOR_CLIENT_SECRET=...
```

## Migration from Old Pattern

If you were using the old CLUSTER_PROVIDER pattern:

### Before
```bash
CLUSTER_PROVIDER=kind+cilium task up
# Then manually deploy apps
task argocd:upgrade
task prometheus:upgrade
# etc...
```

### After
```bash
CLUSTER_TYPE=ephemeral CLUSTER_NAME=kind-dev task up
task bootstrap
# Everything else deployed automatically by ArgoCD ApplicationSets
```

## Benefits

1. **No complex Taskfile conditionals** - cluster type lives in GitOps repo structure
2. **GitOps benefits** - audit trail, rollback, declarative state
3. **Consistent deployments** - same process for all cluster types
4. **Easy to test** - just point to different cluster-type paths
5. **Separation of concerns** - Taskfiles just bootstrap, GitOps deploys apps

## Next Steps

1. Create your GitOps repository with the structure above
2. Define cluster-type base configurations (ephemeral/on-prem/cloud)
3. Create ArgoCD ApplicationSets for each cluster type
4. Bootstrap your clusters with `task bootstrap`
5. Let Flux and ArgoCD handle the rest!
