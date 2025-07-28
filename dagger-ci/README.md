# Dagger CI Module

This Dagger module provides CI/CD functionality for building and publishing Docker images for the tasks repository.

## Overview

The module builds Docker images for multiple operating systems and architectures with the benefits of Dagger's caching and parallelization.

## Functions

### build_and_push

Builds and pushes a single platform image.

```bash
dagger call build-and-push \
  --github-token=env:GITHUB_TOKEN \
  --github-actor="your-username" \
  --os="ubuntu" \
  --os-ver="jammy" \
  --platform="linux/amd64"
```

### build_only

Builds a single platform image without pushing (for PR validation).

```bash
dagger call build-only \
  --os="ubuntu" \
  --os-ver="jammy" \
  --platform="linux/amd64"
```

### build_single_matrix_entry

Builds and pushes all architectures for a single OS/version combination (used by GitHub Actions on develop branch).

```bash
dagger call build-single-matrix-entry \
  --github-token=env:GITHUB_TOKEN \
  --github-actor="your-username" \
  --os="ubuntu" \
  --os-ver="jammy"
```

### build_single_matrix_entry_pr

Builds all architectures for a single OS/version combination without pushing (used by GitHub Actions for PRs).

```bash
dagger call build-single-matrix-entry-pr \
  --os="ubuntu" \
  --os-ver="jammy"
```

### build_all

Builds and pushes all images defined in the platform matrix.

```bash
dagger call build-all \
  --github-token=env:GITHUB_TOKEN \
  --github-actor="your-username"
```

## Local Testing

To test the module locally:

1. Install Dagger:
   ```bash
   curl -fsSL https://dl.dagger.io/dagger/install.sh | sh
   ```

2. Set up GitHub token:
   ```bash
   export GITHUB_TOKEN="your-github-token"
   ```

3. Run a build:
   ```bash
   cd dagger-ci
   dagger call build-and-push \
     --github-token=env:GITHUB_TOKEN \
     --github-actor="your-username" \
     --os="alpine" \
     --os-ver="3.20"
   ```

## GitHub Actions Integration

The module is integrated with GitHub Actions through three workflows:

- `.github/workflows/build.yml` - Main workflow that builds and pushes images on push to develop branch and on schedule
- `.github/workflows/pr-validation.yml` - PR validation workflow that builds images without pushing
- `.github/workflows/build-dagger-all.yml` - Manual workflow to build and push all images at once

## Architecture Support

The module automatically determines which architectures to build based on the OS:

- Alpine, Debian, Ubuntu: `linux/amd64` and `linux/arm64`
- Other OS: `linux/amd64` only