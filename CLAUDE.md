# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a DevOps/Infrastructure automation toolkit using [Taskfile](https://taskfile.dev/) as the primary build system. The repository contains two main categories of task definitions:

1. **Cluster Lifecycle Management**: Tasks for creating and managing ephemeral Kubernetes clusters (Kind, K3d)
2. **Application Deployment**: Tasks for deploying applications, operators, and services into any Kubernetes cluster

## Documentation Structure

All documentation is organized in the `docs/` folder:
- `docs/gitops/` - GitOps patterns, ArgoCD guides, and secrets management
- `docs/migration/` - Migration guides for moving between different approaches

When creating new documentation, place it in the appropriate subfolder and link it from the main README.md

## Repository Organization

### Cluster Lifecycle Management (Ephemeral Clusters)
These tasks handle provisioning and teardown of local development clusters:

**Core Cluster Provisioning:**
- `kind.yml` - Basic Kind cluster setup
- `k3d.yml` - K3d cluster with extensive configuration options
- `talos.yml` - Talos Linux Kubernetes clusters

**Kind with CNI Variants:**
- `kind+antrea.yml` - Kind cluster with Antrea CNI
- `kind+calico.yml` - Kind cluster with Calico CNI
- `kind+cilium.yml` - Kind cluster with Cilium CNI
- `kind+registry.yml` - Kind cluster with built-in container registry
- `kind+spegel.yml` - Kind cluster with P2P image distribution

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

### Cluster Lifecycle Commands
```bash
# Create ephemeral clusters
task kind:create        # Basic Kind cluster
task k3d:create         # K3d cluster
task kind+cilium:create # Kind with Cilium CNI

# Destroy clusters
task kind:delete
task k3d:delete
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

## Development Patterns

### Working with Ephemeral Clusters
1. Choose cluster type based on needs:
   - Kind: Best for testing, supports multiple CNIs
   - K3d: Lightweight, fast startup, good for CI
   - Talos: Production-like, immutable OS

2. CNI selection for Kind:
   - Default: kindnet (simple, fast)
   - Calico: Enterprise features, network policies
   - Cilium: eBPF-based, advanced observability
   - Antrea: VMware-backed, good Windows support

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
- Prefer Taskfiles over bash scripts for cross-platform compatibility (Windows PowerShell support)