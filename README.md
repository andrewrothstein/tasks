# Tasks

A comprehensive [Taskfile](https://taskfile.dev/) collection for Kubernetes development and operations.

## Overview

This repository provides a modular, composable set of task definitions for:
- **Ephemeral Cluster Management**: Kind, K3d, Talos
- **Application Deployment**: GitOps, observability, databases, service mesh
- **Infrastructure Automation**: Terraform, Ansible, Pulumi
- **Developer Productivity**: Standardized workflows across tools

## Quick Start

```bash
# Install prerequisites
brew install go-task kubectl helm

# Clone repository
git clone https://github.com/andrewrothstein/tasks.git
cd tasks

# Set up environment
cp .env.sample .env
# Edit .env with your settings

# (Optional) Set up pre-commit hooks
uvx pre-commit install  # Auto-run checks on git commit

# Option 1: Create default cluster (Kind + Cilium)
task up

# Option 2: Choose specific cluster type
CLUSTER_PROVIDER=k3d task up           # Use K3d
CLUSTER_PROVIDER=kind+calico task up   # Kind with Calico
CLUSTER_PROVIDER=byo-cluster task up   # Use existing cluster
```

## Cluster Selection

### Choosing Your Cluster Type

The repository supports multiple cluster types, each optimized for different use cases:

#### Via Environment Variable (Recommended)
```bash
# Default (Kind with Cilium CNI)
task up

# Specific cluster type
CLUSTER_PROVIDER=kind task up              # Basic Kind cluster
CLUSTER_PROVIDER=kind+cilium task up       # Kind with Cilium CNI (eBPF)
CLUSTER_PROVIDER=kind+calico task up       # Kind with Calico CNI
CLUSTER_PROVIDER=kind+antrea task up       # Kind with Antrea CNI
CLUSTER_PROVIDER=kind+registry task up     # Kind with local registry
CLUSTER_PROVIDER=kind+spegel task up       # Kind with P2P image cache
CLUSTER_PROVIDER=k3d task up               # K3d (lightweight, fast)
CLUSTER_PROVIDER=byo-cluster task up       # BYO external cluster
```

#### Direct Task Invocation
```bash
task kind:create           # Basic Kind cluster
task kind+cilium:create    # Kind with Cilium
task k3d:create            # K3d cluster
```

### Cluster Types Explained

| Cluster Type | Best For | Features |
|-------------|----------|----------|
| **kind** | Basic testing | Simple, standard CNI |
| **kind+cilium** | Advanced networking | eBPF, network policies, observability |
| **kind+calico** | Enterprise features | BGP, advanced policies |
| **kind+antrea** | VMware environments | Windows node support |
| **kind+registry** | Local development | Built-in container registry |
| **kind+spegel** | CI/CD pipelines | P2P image distribution |
| **k3d** | Quick iteration | Fast startup, lightweight |
| **byo-cluster** | Production-like | Use existing clusters (Harvester, EKS, etc.) |

## Core Commands

### Cluster Management
```bash
# Create clusters
task kind:create        # Create Kind cluster
task k3d:create         # Create K3d cluster
CLUSTER_PROVIDER=byo-cluster task up  # Use external cluster

# Delete clusters
task kind:delete        # Destroy Kind cluster
task k3d:delete         # Destroy K3d cluster

# Switch between multiple clusters
task k8s:switch cluster=harvester   # Switch to different cluster
task k8s:list-clusters              # List available configs
task k8s:current                    # Show current cluster
```

### Application Deployment
```bash
task argocd:apply       # Deploy ArgoCD
task prometheus:apply   # Deploy Prometheus
task istio:apply        # Deploy Istio service mesh
task cert-manager:apply # Deploy cert-manager
```

### Testing
```bash
task test               # Run all tests
task test:quick         # Quick tests (no cluster ops)
task test:ci            # CI-appropriate tests
```

## Environment Configuration

### Using Doppler (Recommended)
```bash
doppler run --mount .env -- task up
```

### Using .env File
```bash
cp .env.sample .env
# Edit .env with your configuration
task up
```

## Repository Structure

```
.
├── Taskfile.yml           # Main task orchestrator
├── kubectl.yml            # Kubernetes operations utilities
├── kind*.yml              # Kind cluster variants
├── k3d.yml                # K3d cluster configuration
├── k8s-*.yml              # Category aggregators
├── tests/                 # Test suites
│   ├── test-all.yml       # Test orchestrator
│   └── test-kubectl.yml   # kubectl.yml tests
└── chart-*/               # Custom Helm charts
```

## Advanced Usage

### Using External Clusters (BYO)

For production or externally-managed clusters (Harvester, Rancher, EKS, GKE, AKS):

```bash
# Import existing kubeconfig
task kubectl-config:import file=~/Downloads/kubeconfig.yaml cluster=harvester

# Switch to external cluster
task k8s:switch cluster=harvester

# Use with BYO mode (no-op create/delete)
CLUSTER_PROVIDER=byo-cluster task up

# Quick switches for common clusters
task k8s:use-harvester    # Switch to Harvester
task k8s:use-k3s          # Switch to K3s
task k8s:use-local        # Back to local Kind/K3d
```

### Managing Multiple Kubeconfigs

```bash
# List available configs
task kubectl-config:list

# Switch between configs
task kubectl-config:switch cluster=dev
task kubectl-config:switch cluster=staging
task kubectl-config:switch cluster=prod

# Merge multiple configs
task kubectl-config:merge clusters=dev,staging,prod output=all

# Backup current config
task kubectl-config:backup name=before-changes
```

### Dry-Run Mode
```bash
KUBECTL_DRY_RUN=true task argocd:apply
```

### Custom Timeouts
```bash
KUBECTL_TIMEOUT=600s task prometheus:apply
```

## Testing

The repository includes comprehensive test coverage:

```bash
# Run specific test suites
task --taskfile tests/test-kubectl.yml test-all

# Test individual components
task --taskfile tests/test-kubectl.yml test-namespace
task --taskfile tests/test-kubectl.yml test-apply-delete
```

## Contributing

### Development Setup

1. Install pre-commit hooks (optional but recommended):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

2. Or use uvx (no installation needed):
   ```bash
   uvx pre-commit run --all-files
   ```

### Before Committing

1. Run pre-commit checks:
   ```bash
   # Check all files
   uvx pre-commit run --all-files

   # Or if pre-commit is installed
   pre-commit run --all-files

   # Check only staged files (automatic if hooks installed)
   pre-commit run
   ```

2. Run tests:
   ```bash
   task test:quick
   ```

### Contribution Guidelines

1. Create tests for new functionality in `tests/`
2. Follow existing patterns for task organization
3. Update CLAUDE.md for AI-assisted development
4. Ensure all pre-commit checks pass
5. Run `task test` before submitting changes
6. Keep documentation (README.md and CLAUDE.md) in sync

## License

MIT

## Secrets Management

* For secrets I use doppler: `doppler run --mount .env -- task up`
* Feel free to manage your secrets as you see fit in `.env` per the `.env.sample`
