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
# Install with uv
uv sync

# Or install as editable package
uv pip install -e .
```

### CLI Usage

```bash
# Run the operator
uv run vcluster-argocd-enroller

# Run in development mode with auto-reload
uv run vcluster-argocd-enroller --dev --verbose

# Check vCluster enrollment status
uv run vcluster-argocd-enroller check

# Manually enroll a vCluster
uv run vcluster-argocd-enroller enroll my-vcluster --namespace vcluster-ns

# Remove a vCluster from ArgoCD
uv run vcluster-argocd-enroller unenroll my-vcluster --confirm

# Run with specific namespace watching
uv run vcluster-argocd-enroller --namespace my-namespace

# Get help
uv run vcluster-argocd-enroller --help
```

### Quick Development

```bash
# Install dependencies and run in dev mode
uv sync
uv run vcluster-argocd-enroller --dev --verbose
```

### Testing

```bash
# Run unit tests
uv run pytest

# Run unit tests with coverage
uv run pytest --cov=vcluster_argocd_enroller

# Run e2e tests (requires real cluster)
uv run pytest -m e2e

# Check existing vClusters
uv run vcluster-argocd-enroller check --show-secrets
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
├── src/
│   └── vcluster_argocd_enroller/
│       ├── __init__.py       # Package initialization
│       ├── __main__.py       # Package entry point
│       ├── cli.py            # Cyclopts CLI implementation
│       └── operator.py       # Kopf operator logic
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_operator_integration.py  # Unit tests with mocked K8s
│   └── test_e2e.py          # End-to-end tests (requires cluster)
├── pyproject.toml            # Python project configuration (uv)
├── uv.lock                   # Locked dependencies
├── pytest.ini                # Pytest configuration
├── Taskfile.yml              # Task automation
├── Dockerfile                # Container image definition
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```
