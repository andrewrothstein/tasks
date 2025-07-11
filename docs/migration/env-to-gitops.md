# Migration Guide: .env Files to GitOps

This guide helps migrate from `.env` file-based secret management to GitOps-compliant approaches.

## Migration Paths

### Option 1: Direct Kubernetes Secrets (Quick Start)
Best for: Getting started quickly, non-production environments

```bash
# Create secret from .env file
task env-to-k8s-secrets

# Create in specific namespace
task env-to-k8s-secrets namespace=monitoring secret_name=app-secrets

# Create in multiple namespaces
task env-to-k8s-secrets:bulk-namespace namespaces=default,argocd,monitoring
```

**Pros:** Simple, immediate
**Cons:** Secrets in Git (base64 encoded), no rotation

### Option 2: Sealed Secrets (GitOps Safe)
Best for: Teams wanting GitOps without external dependencies

```bash
# Install Sealed Secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.5/controller.yaml

# Create sealed secret from .env
task env-to-k8s-secrets:create-sealed

# Commit the sealed secret to Git
git add argocd/sealed-secrets/env-secrets-sealed.yaml
git commit -m "Add sealed secrets"
```

**Pros:** Safe in Git, encryption at rest
**Cons:** Manual rotation, certificate management

### Option 3: External Secrets with Manual Backend
Best for: Teams not ready for external secret stores

```bash
# Generate template
task env-to-k8s-secrets:create-external-secret

# Edit the generated file and add your secrets
vim argocd/external-secrets/env-secrets-external.yaml

# Apply to cluster
kubectl apply -f argocd/external-secrets/env-secrets-external.yaml
```

**Pros:** Separation of concerns, upgrade path to external stores
**Cons:** Still manual, secrets in cluster

### Option 4: Migrate to External Secret Store
Best for: Production environments, teams ready for centralized secrets

1. **Choose a backend:**
   - Doppler (easiest)
   - HashiCorp Vault
   - AWS Secrets Manager
   - Azure Key Vault
   - Google Secret Manager

2. **Import existing secrets:**
   ```bash
   # Example: Import to Doppler
   doppler secrets upload .env
   
   # Or manually via UI
   ```

3. **Use External Secrets Operator:**
   ```bash
   task doppler-bootstrap
   ```

## Application Changes

### Before (Task/Helm with .env)
```yaml
# values.yaml
database:
  url: ${DATABASE_URL}
  password: ${DB_PASSWORD}
```

### After (GitOps with K8s Secrets)
```yaml
# values.yaml
database:
  url:
    valueFrom:
      secretKeyRef:
        name: env-secrets
        key: DATABASE_URL
  password:
    valueFrom:
      secretKeyRef:
        name: env-secrets
        key: DB_PASSWORD
```

## Step-by-Step Migration

1. **Audit Current Secrets**
   ```bash
   task env-to-k8s-secrets:list
   ```

2. **Choose Migration Path**
   - Quick start: Option 1
   - GitOps ready: Option 2 or 3
   - Production: Option 4

3. **Create Secrets**
   ```bash
   # For GitOps
   task env-to-k8s-secrets:create-sealed
   ```

4. **Update Application Manifests**
   - Change from env vars to secretKeyRef
   - Update Helm values files

5. **Test Deployment**
   ```bash
   # Deploy with ArgoCD
   kubectl apply -f application.yaml
   ```

6. **Clean Up**
   - Remove .env references from Task files
   - Archive .env file securely

## Common Patterns

### Multi-Environment Secrets
```bash
# Dev environment
task env-to-k8s-secrets:create-sealed namespace=dev secret_name=app-secrets-dev

# Staging environment  
task env-to-k8s-secrets:create-sealed namespace=staging secret_name=app-secrets-staging

# Production environment
task env-to-k8s-secrets:create-sealed namespace=prod secret_name=app-secrets-prod
```

### Namespace-scoped Secrets
```yaml
# Each app gets its own secret
monitoring/grafana-secrets
monitoring/prometheus-secrets
argocd/argocd-secrets
```

## Tips

1. **Start Small**: Migrate one non-critical app first
2. **Use Namespaces**: Isolate secrets by namespace
3. **Plan Rotation**: Have a strategy for updating secrets
4. **Backup First**: Keep .env files backed up during migration
5. **Document**: Update runbooks with new secret management process