# Tasks - Kubernetes Development Toolkit

A comprehensive collection of [Taskfile](https://taskfile.dev/) definitions for Kubernetes development, GitOps workflows, and infrastructure automation.

## 🚀 Quick Start

```bash
# Install Task (https://taskfile.dev/installation/)
brew install go-task

# Clone and setup
git clone https://github.com/andrewrothstein/tasks
cd tasks

# Setup secrets (choose one)
doppler run --mount .env -- task up    # Using Doppler
cp .env.sample .env && task up          # Using .env file
```

## 📚 Documentation

- [**CLAUDE.md**](CLAUDE.md) - AI assistant instructions and codebase overview
- [**GitOps & ArgoCD**](docs/gitops/)
  - [ArgoCD Migration Guide](docs/gitops/argocd-migration.md) - Migrating from Task to ArgoCD
  - [Doppler Secrets Management](docs/gitops/doppler-secrets-management.md) - GitOps-compliant secrets with Doppler
- [**Migration Guides**](docs/migration/)
  - [.env to GitOps Migration](docs/migration/env-to-gitops.md) - Migrate from .env files to Kubernetes secrets

## 🎯 Key Features

### Cluster Management
- **Kind** - Local Kubernetes clusters with various CNI options
- **K3d** - Lightweight Kubernetes for development
- **Talos** - Production-like immutable Kubernetes

### Application Deployment
- **GitOps** - ArgoCD, Flux, and Tekton pipelines
- **Observability** - Prometheus, Grafana, Jaeger, and OpenTelemetry
- **Service Mesh** - Istio with ambient mode support
- **Storage** - Rook/Ceph, OpenEBS, Longhorn, and more

### Developer Tools
- **Secret Management** - Doppler integration, Sealed Secrets, External Secrets
- **CI/CD** - Drone, Tekton, GitHub Actions runners
- **Databases** - PostgreSQL, MySQL, Redis, MongoDB operators

## 🔧 Common Tasks

```bash
# List all available tasks
task --list-all

# Cluster operations
task kind:create          # Create Kind cluster
task k3d:create           # Create K3d cluster
task kind+cilium:create   # Kind with Cilium CNI

# Deploy applications
task argocd:apply         # Deploy ArgoCD
task prometheus:apply     # Deploy Prometheus
task grafana:apply        # Deploy Grafana

# GitOps bootstrap
task doppler-bootstrap    # Setup Doppler + External Secrets + ArgoCD
```

## 🔐 Secret Management

### Using Doppler (Recommended)
```bash
# Set up Doppler CLI
doppler login
doppler setup

# Run tasks with Doppler
doppler run --mount .env -- task <taskname>
```

### Using .env File
```bash
# Copy and edit the sample
cp .env.sample .env
# Edit .env with your values
task <taskname>
```

### Migrating to GitOps
See [.env to GitOps Migration Guide](docs/migration/env-to-gitops.md) for transitioning from .env files to Kubernetes-native secret management.

## 📁 Repository Structure

```
.
├── Taskfile.yml           # Main task definitions
├── CLAUDE.md              # AI assistant instructions
├── docs/                  # Documentation
│   ├── gitops/           # GitOps guides
│   └── migration/        # Migration guides
├── argocd/               # ArgoCD applications and configs
├── chart-*/              # Custom Helm charts
├── k8s-*.yml            # Kubernetes app deployments
├── kind*.yml            # Kind cluster variants
└── *.yml                # Individual tool tasks
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow existing patterns for new task files
4. Submit a pull request

## 📜 License

MIT License - see LICENSE file for details