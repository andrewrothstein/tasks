# vCluster ArgoCD Enroller

A Kubernetes operator with CLI that automatically enrolls vCluster instances in ArgoCD for GitOps management.

## Overview

This operator watches for vCluster StatefulSets and automatically:
1. Extracts the vCluster kubeconfig from its secret
2. Creates an ArgoCD cluster secret with proper authentication
3. Cleans up ArgoCD secrets when vClusters are deleted

## Setup

### Prerequisites

- Python 3.13+
- `uv` package manager
- Kubernetes cluster with ArgoCD installed
- vCluster CLI (optional, for testing)

### Installation

```bash
# Install dependencies
task install

# Install development dependencies
task install-dev
```

### CLI Usage

```bash
# Run the operator
vcluster-argocd-enroller

# Run in development mode with auto-reload
vcluster-argocd-enroller --dev --verbose

# Check vCluster enrollment status
vcluster-argocd-enroller check

# Manually enroll a vCluster
vcluster-argocd-enroller enroll my-vcluster --namespace vcluster-ns

# Remove a vCluster from ArgoCD
vcluster-argocd-enroller unenroll my-vcluster --confirm

# Run with specific namespace watching
vcluster-argocd-enroller --namespace my-namespace

# Get help
vcluster-argocd-enroller --help
```

### Quick Development

```bash
# Install and run in dev mode
task install
task dev
```

### Testing

```bash
# Quick test with a disposable vcluster
task --taskfile ../vcluster-cli.yml test-operator

# Run tests via CLI
vcluster-argocd-enroller test

# Check existing vClusters
vcluster-argocd-enroller check --show-secrets
```

### Building Docker Image

```bash
task build
```

## How It Works

The operator monitors StatefulSets with the label `app: vcluster` and:

1. **On Create/Resume**: 
   - Extracts kubeconfig from secret `vc-{vcluster-name}`
   - Creates ArgoCD cluster secret in `argocd` namespace
   - Secret contains cluster endpoint and TLS certificates

2. **On Delete**:
   - Removes the corresponding ArgoCD cluster secret
   - Cleans up gracefully even if secret doesn't exist

## Configuration

The operator expects:
- vCluster secrets named: `vc-{vcluster-name}`
- ArgoCD installed in namespace: `argocd`
- vCluster StatefulSets labeled with: `app=vcluster`

## Development

This project uses:
- `uv` for Python dependency management
- `kopf` as the Kubernetes operator framework
- `ruff` for linting and formatting

### Project Structure

```
vcluster-argocd-enroller/
├── operator.py          # Main operator logic
├── pyproject.toml       # Python project configuration
├── Taskfile.yml         # Task automation
├── Dockerfile           # Container image definition
└── README.md            # This file
```

### Migrating from Pipfile

This project has been migrated from Pipenv to uv. To clean up old files:

```bash
task clean
```