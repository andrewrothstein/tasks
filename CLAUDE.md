# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a DevOps/Infrastructure automation toolkit using [Taskfile](https://taskfile.dev/) as the primary build system. The repository contains three main categories of task definitions:

1. **Cluster Lifecycle Management**: Tasks for creating and managing ephemeral Kubernetes clusters (Kind, K3d, Talos)
2. **Application Deployment**: Tasks for deploying applications, operators, and services into any Kubernetes cluster
3. **External Cluster Support**: BYO (Bring Your Own) cluster integration for production environments (Harvester, EKS, GKE, etc.)

## Repository Organization

### Cluster Lifecycle Management (Ephemeral Clusters)
These tasks handle provisioning and teardown of local development clusters:

**Core Cluster Provisioning:**
- `kind.yml` - Basic Kind cluster setup
- `k3d.yml` - K3d cluster with extensive configuration options
- `talos.yml` - Talos Linux Kubernetes clusters
- `byo-cluster.yml` - External cluster support (no-op create/delete)

**Kind with CNI Variants:**
- `kind+antrea.yml` - Kind cluster with Antrea CNI
- `kind+calico.yml` - Kind cluster with Calico CNI
- `kind+cilium.yml` - Kind cluster with Cilium CNI (default)
- `kind+registry.yml` - Kind cluster with built-in container registry
- `kind+spegel.yml` - Kind cluster with P2P image distribution

**Cluster Configuration Management:**
- `kubectl-config.yml` - Kubeconfig switching and management
- `k8s.yml` - Main cluster orchestrator with provider selection

### Application Deployment (Cluster-Agnostic)
These tasks deploy applications into any Kubernetes cluster:

**Category Aggregators:**
- `k8s-database.yml` - Database operators and instances
- `k8s-observability.yml` - Monitoring and observability stack
- `k8s-storage.yml` - Storage solutions and CSI drivers
- `k8s-cicd.yml` - CI/CD and GitOps tools

**Core Infrastructure:**
- `gateway-api.yml` - Kubernetes Gateway API
- `cert-manager.yml` - Certificate management
- `metrics-server.yml` - Cluster metrics
- `metallb.yml` - Load balancer for bare metal

**Service Mesh & Networking:**
- `istio.yml` - Istio service mesh
- `tailscale.yml` - Tailscale VPN operator
- `nginx.yml` - NGINX ingress controller

**GitOps & CI/CD:**
- `argocd.yml` - ArgoCD GitOps
- `flux.yml` - Flux GitOps
- `tekton.yml` - Tekton pipelines
- `drone.yml` - Drone CI

## Essential Commands

### Cluster Selection & Creation
```bash
# Default cluster (Kind + Cilium)
task up

# Choose specific cluster type
CLUSTER_PROVIDER=kind task up              # Basic Kind
CLUSTER_PROVIDER=kind+cilium task up       # Kind with Cilium (default)
CLUSTER_PROVIDER=kind+calico task up       # Kind with Calico
CLUSTER_PROVIDER=k3d task up               # K3d cluster
CLUSTER_PROVIDER=byo-cluster task up       # Use external cluster

# Direct cluster creation
task kind:create        # Basic Kind cluster
task k3d:create         # K3d cluster
task kind+cilium:create # Kind with Cilium CNI

# Destroy clusters
task kind:delete
task k3d:delete
```

### Cluster Switching & Management
```bash
# Switch between clusters
task k8s:switch cluster=harvester
task k8s:switch cluster=k3s
task k8s:list-clusters
task k8s:current

# Quick switches
task k8s:use-harvester  # Switch to Harvester
task k8s:use-k3s        # Switch to K3s  
task k8s:use-local      # Back to local

# Kubeconfig management
task kubectl-config:list
task kubectl-config:switch cluster=dev
task kubectl-config:import file=~/config.yaml cluster=prod
task kubectl-config:merge clusters=dev,staging output=all
```

### Application Deployment Commands
```bash
# Deploy core infrastructure
task metrics-server:apply
task cert-manager:apply
task gateway-api:apply

# Deploy applications
task argocd:apply
task prometheus:apply
task grafana:apply

# Check deployments
task argocd:check
task istio:check
```

### Full Environment Setup
```bash
# Current approach (mixes concerns)
task up  # Creates cluster + deploys apps

# Recommended approach (clear separation)
task kind:create        # Step 1: Create cluster
task core:apply         # Step 2: Deploy core services
task apps:apply         # Step 3: Deploy applications
```

## Architecture & Structure

### Task Organization
- Each tool/service has its own task definition file
- Tasks are modular and composable via `includes`
- Clear separation between cluster provisioning and app deployment

### Key Directories
- `/chart-*/` - Custom Helm charts
- `/crossplane-*/` - Crossplane provider configurations  
- `/playbooks/` - Ansible playbooks
- `/pulumi/` - Pulumi infrastructure code
- `/tf-*/` - Terraform modules

### Environment Configuration
- Uses Doppler for secrets: `doppler run --mount .env -- task <command>`
- Alternative: Configure `.env` file based on `.env.sample`
- All tasks respect `.env` via `dotenv` directive

## Testing

### Running Tests
Tests are located in the `tests/` directory. The repository includes comprehensive test coverage.

```bash
# Main test commands
task test               # Run all tests
task test:quick         # Quick tests (no cluster ops)
task test:ci            # CI-appropriate tests

# Test specific modules
task --taskfile tests/test-kubectl.yml test-all
task --taskfile tests/test-kubectl-config.yml test-all

# Run individual test suites
task --taskfile tests/test-kubectl.yml test-namespace
task --taskfile tests/test-kubectl.yml test-apply-delete
task --taskfile tests/test-kubectl.yml test-dry-run
task --taskfile tests/test-kubectl.yml test-backward-compat

# Clean up test resources
task --taskfile tests/test-kubectl.yml cleanup
task --taskfile tests/test-all.yml cleanup
```

## Development Patterns

### Working with Ephemeral Clusters
1. Choose cluster type based on needs:
   - **Kind**: Best for testing, supports multiple CNIs
   - **K3d**: Lightweight, fast startup, good for CI
   - **Talos**: Production-like, immutable OS
   - **BYO**: Use existing external clusters

2. CNI selection for Kind:
   - **Default**: kind+cilium (eBPF-based, recommended)
   - **Calico**: Enterprise features, network policies
   - **Cilium**: eBPF-based, advanced observability
   - **Antrea**: VMware-backed, good Windows support
   - **Registry**: Includes local container registry
   - **Spegel**: P2P image distribution for CI/CD

### Working with External Clusters (BYO)
1. Import existing kubeconfig:
   ```bash
   task kubectl-config:import file=~/kubeconfig.yaml cluster=harvester
   ```

2. Switch to external cluster:
   ```bash
   task k8s:switch cluster=harvester
   ```

3. Use BYO mode (no-op create/delete):
   ```bash
   CLUSTER_PROVIDER=byo-cluster task up
   ```

### Deploying Applications
1. Check cluster readiness: `kubectl cluster-info`
2. Deploy core services first (metrics, ingress, cert-manager)
3. Deploy application-specific requirements
4. Use namespace isolation for multi-tenancy

### Task Dependencies
- Cluster tasks are independent of application tasks
- Application tasks may have inter-dependencies
- Use `deps` for parallel execution, `cmds` for sequential

### Important Notes
- Most application deployment tasks work on any K8s cluster
- Ephemeral cluster tasks are specifically for local development
- Production deployments should use appropriate cluster provisioning tools (not Kind/K3d)
- BYO clusters use no-op create/delete operations for safety
- Always ensure CLAUDE.md and README.md are consistent before committing changes
- Run `task test` before submitting any changes