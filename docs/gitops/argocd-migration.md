# GitOps Migration Guide

This guide explains the migration from Helm CLI-based deployments to ArgoCD GitOps patterns.

## Architecture Overview

### Services Remaining with Helm CLI (Left of ArgoCD)
These services are part of cluster bootstrapping and remain with direct Helm deployments:
- CNI providers (Cilium, Calico, Antrea)
- Core infrastructure (cert-manager, metrics-server)
- Storage providers (Longhorn, OpenEBS, Rook)
- Ingress controllers (NGINX, Gateway API)
- ArgoCD itself

### Services Migrated to ArgoCD (Right of ArgoCD)
All application-layer services are deployed via ArgoCD:
- Observability stack (Prometheus, Grafana, Jaeger, Kiali)
- Database operators (CloudNative-PG, Redis, MongoDB, MySQL, Cassandra)
- CI/CD tools (Flux, Tekton, Drone)
- Security tools (Vault, External Secrets)
- Application platforms (Knative, KubeFlow)

## Directory Structure
```
argocd/
├── applications/        # Individual ArgoCD Application manifests
│   ├── app-of-apps.yaml
│   ├── cloudnative-pg.yaml
│   ├── jaeger.yaml
│   ├── kube-prometheus-stack.yaml
│   └── redis-operator.yaml
└── appsets/            # ArgoCD ApplicationSet manifests
    ├── database-operators.yaml
    └── observability-stack.yaml
```

## Usage

### Quick Start
```bash
# Bootstrap ArgoCD with GitOps applications
task argocd-bootstrap:bootstrap

# Deploy all applications
task argocd-apps:apply-all

# Check application status
task argocd-apps:status
```

### Individual Operations
```bash
# Apply specific application
kubectl apply -f argocd/applications/kube-prometheus-stack.yaml

# Apply ApplicationSet
kubectl apply -f argocd/appsets/database-operators.yaml

# Sync applications
task argocd-apps:sync-all

# Delete applications
task argocd-apps:delete-all
```

## Migration Workflow

1. **Bootstrap Cluster** (Helm CLI)
   ```bash
   task kind:create         # or k3d:create
   task cert-manager:apply
   task metrics-server:apply
   task gateway-api:apply
   ```

2. **Deploy ArgoCD** (Helm CLI)
   ```bash
   task argocd:upgrade
   task argocd:login
   ```

3. **Deploy Applications** (GitOps)
   ```bash
   task argocd-apps:apply-all
   ```

## ApplicationSet Benefits

ApplicationSets reduce boilerplate by generating multiple applications from a single template:
- Database operators: One ApplicationSet manages all database operators
- Observability stack: Unified deployment of monitoring tools
- Consistent configuration across similar applications

## Environment Variables

ArgoCD applications can use environment variables via the `${ARGOCD_ENV_*}` pattern:
```yaml
grafana:
  adminPassword: ${ARGOCD_ENV_GRAFANA_ADMIN_PASSWORD}
```

## Best Practices

1. **Separation of Concerns**: Keep cluster bootstrapping separate from application deployments
2. **Use ApplicationSets**: For similar applications to reduce duplication
3. **Automated Sync**: Enable for non-critical environments
4. **Manual Sync**: Use for production environments
5. **Resource Cleanup**: Always include finalizers for proper cleanup