# Kubernetes Bootstrap Tool

A Python-based tool for managing independent Kubernetes cluster bootstrap profiles. This replaces the complex Task-based composition with explicit, declarative profiles.

## Philosophy

Bootstrap scenarios are **1:1 configurations**, not compositions. Each profile is completely independent and describes:
- Which cluster provider to use
- Whether to create the cluster
- Which components to install (and in what order)

This approach avoids the "forced composition" problem of Task's includes/deps system.

## Installation

The bootstrap tool is managed with [uv](https://docs.astral.sh/uv/):

```bash
# Install dependencies and create venv
uv sync

# Run the tool
uv run bootstrap --help

# Or activate venv and use directly
source .venv/bin/activate
bootstrap --help
```

## Quick Start

```bash
# Initialize example profiles
uv run bootstrap init

# List available profiles
uv run bootstrap list

# Show profile details
uv run bootstrap show kind-minimal

# Apply a profile (dry-run)
uv run bootstrap apply kind-minimal --dry-run

# Apply a profile for real
uv run bootstrap apply kind-minimal

# Use existing cluster (skip creation)
uv run bootstrap apply byo-observability --skip-cluster

# Destroy a cluster
uv run bootstrap destroy kind+cilium
```

## Profile Structure

Profiles are simple YAML files in the `profiles/` directory:

```yaml
name: kind-minimal
description: Minimal Kind cluster with Cilium and basic monitoring

cluster:
  provider: kind+cilium  # Any cluster provider supported by tasks
  create: true           # Whether to create the cluster

# Components installed sequentially (order matters)
components:
  - metrics-server:upgrade
  - cert-manager:upgrade

# Components installed in parallel (order doesn't matter)
parallel_components:
  - kube-prometheus-stack:upgrade
  - grafana:upgrade
```

## Example Profiles

### kind-minimal.yml
Basic Kind cluster with Cilium, metrics, and cert-manager:
```bash
uv run bootstrap apply kind-minimal
```

### kind-full.yml
Full-featured development environment with ArgoCD, monitoring, and networking:
```bash
uv run bootstrap apply kind-full
```

### k3d-dev.yml
Lightweight K3d cluster for fast iteration:
```bash
uv run bootstrap apply k3d-dev
```

### byo-observability.yml
Install observability stack on existing cluster:
```bash
# First, switch to your cluster
task k8s:switch cluster=harvester

# Then apply profile (skip cluster creation)
uv run bootstrap apply byo-observability
```

## Creating Custom Profiles

1. Create a new YAML file in `profiles/`:

```yaml
name: my-custom
description: My custom bootstrap configuration

cluster:
  provider: k3d
  create: true

components:
  - metrics-server:upgrade
  - argocd:upgrade
  - istio:upgrade

parallel_components:
  - kube-prometheus-stack:upgrade
  - loki:upgrade
```

2. Apply your profile:

```bash
uv run bootstrap apply my-custom
```

## CLI Commands

### `bootstrap list`
List all available profiles with their configurations.

### `bootstrap show <profile>`
Display detailed information about a specific profile.

### `bootstrap apply <profile>`
Apply a bootstrap profile to create and configure a cluster.

Options:
- `--dry-run`: Show what would be executed without running commands
- `--skip-cluster`: Skip cluster creation (use existing cluster)
- `--profiles-dir PATH`: Use custom profiles directory

### `bootstrap destroy <provider>`
Destroy a cluster by provider name (e.g., `kind`, `k3d`, `kind+cilium`).

Options:
- `--dry-run`: Show what would be executed

### `bootstrap init`
Initialize the `profiles/` directory with example profiles.

## Advantages Over Task Composition

**Task-based approach:**
- Complex includes/deps chains
- Artificial groupings (post-mesh-1, post-mesh-2, etc.)
- Hard to reason about execution order
- Forced composition through file includes

**Profile-based approach:**
- Each profile is independent and explicit
- Clear execution order (sequential → parallel)
- Easy to understand and modify
- Python control flow instead of Task DSL
- Better error handling and logging
- Can run components in parallel when safe

## Integration with Existing Tasks

The bootstrap tool executes existing Task commands, so all your current task definitions continue to work:

```yaml
components:
  - metrics-server:upgrade    # Runs: task metrics-server:upgrade
  - argocd:upgrade           # Runs: task argocd:upgrade
```

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Type checking
uv run mypy src/bootstrap

# Linting
uv run ruff check src/bootstrap

# Format code
uv run ruff format src/bootstrap
```

## Architecture

```
src/bootstrap/
  __init__.py          # Package init
  profile.py           # Profile models (Pydantic)
  executor.py          # Command execution logic
  cli.py               # Click-based CLI

profiles/                # Profile definitions
  kind-minimal.yml
  kind-full.yml
  k3d-dev.yml
  byo-observability.yml

pyproject.toml           # uv project configuration
```

## Migration from Task-based Approach

Instead of:
```bash
task up  # Creates cluster + deploys everything
```

Use:
```bash
uv run bootstrap apply kind-full
```

Benefits:
- Explicit about what's being installed
- Can create multiple independent profiles
- Clear separation of concerns
- Better suited for 1:1 bootstrap scenarios
