# Doppler + ArgoCD Secrets Management

This setup provides GitOps-compliant secrets management using Doppler + External Secrets Operator + ArgoCD.

## Architecture

```
Doppler (Source of Truth)
    ↓
External Secrets Operator
    ↓
Kubernetes Secrets
    ↓
ArgoCD Applications
```

## One-Time Setup

1. **Get Doppler Service Token**
   ```bash
   # From Doppler dashboard: Projects > YOUR_PROJECT > YOUR_CONFIG > Access > Service Tokens
   export DOPPLER_SERVICE_TOKEN="dp.st.YOUR_TOKEN"
   ```

2. **Run Bootstrap Task**
   ```bash
   # With Doppler CLI
   doppler run -- task doppler-bootstrap

   # Or with environment variable
   DOPPLER_SERVICE_TOKEN="dp.st.YOUR_TOKEN" task doppler-bootstrap
   ```

## How It Works

1. **ClusterSecretStore**: Provides cluster-wide access to Doppler
2. **ExternalSecrets**: Sync specific secrets from Doppler to K8s namespaces
3. **ArgoCD ApplicationSet**: Manages ExternalSecret resources via GitOps

## Usage in Applications

Instead of environment variables, apps now reference Kubernetes secrets:

```yaml
# Old way (environment variable)
adminPassword: ${ARGOCD_ENV_GRAFANA_ADMIN_PASSWORD}

# New way (Kubernetes secret)
adminPassword:
  valueFrom:
    secretKeyRef:
      name: doppler-secrets
      key: GRAFANA_ADMIN_PASSWORD
```

## Secret Patterns

1. **All Secrets**: Syncs entire Doppler config to a namespace
2. **Namespace-Specific**: Syncs only needed secrets per namespace
3. **App-Specific**: Fine-grained control with specific secret selection

## Benefits

- ✅ True GitOps - all config in Git
- ✅ Automatic secret rotation
- ✅ No secrets in ArgoCD environment
- ✅ Centralized management via Doppler
- ✅ Kubernetes-native secret access