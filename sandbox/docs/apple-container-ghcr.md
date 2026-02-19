# Publishing to GitHub Container Registry

Push and pull sandbox images via GitHub Container Registry (ghcr.io) using Apple's `container` CLI.

## Prerequisites

| Requirement | Details |
|---|---|
| **Hardware** | Apple Silicon Mac (M1/M2/M3/M4) |
| **OS** | macOS 26 (Tahoe) or later |
| **Tool** | Apple `container` CLI ([releases](https://github.com/apple/container/releases)) |
| **Auth** | `GHCR_NAME` and `GHCR_TOKEN` environment variables (see [Creating a PAT](#create-a-fine-grained-personal-access-token)) |

## Setup

Set your GitHub username and a personal access token with `write:packages` scope:

```bash
export GHCR_NAME="your-github-username"
export GHCR_TOKEN="ghp_..."
```

## Usage

```bash
# Login to ghcr.io (requires GHCR_NAME and GHCR_TOKEN)
just image-login

# Build, tag, and push in one step
just image-release
```

Or run individual steps:

```bash
just image-build   # Build the image locally
just image-tag     # Tag for GHCR
just image-push    # Push to ghcr.io
```

## Running from the Registry

Pull and run a pre-built image:

```bash
# Pull
just image-pull

# Run
just run-ghcr
```

Or using the `container` CLI directly:

```bash
container image pull ghcr.io/YOUR_USERNAME/sandbox:latest

container run -it --rm \
  --cpus 8 \
  --memory 8g \
  --volume ~/myproject:/home/agent/project \
  ghcr.io/YOUR_USERNAME/sandbox:latest /bin/bash
```

## Configuration

The GHCR image path is configured via the `GHCR_NAME` environment variable, which the Justfile uses to construct the image reference:

```just
ghcr_image := env("GHCR_IMAGE", if ghcr_name != "" { "ghcr.io/" + ghcr_name + "/" + name } else { "" })
```

Set `GHCR_NAME` to your GitHub username or organization name.

## Minimal Scope Authentication

To avoid adding scopes to your main `gh` auth, create a fine-grained PAT with minimal permissions:

### Create a Fine-grained Personal Access Token

1. Go to https://github.com/settings/personal-access-tokens/new
2. Configure:
   - **Token name:** `ghcr-sandbox`
   - **Expiration:** your preference
   - **Repository access:** "Public repositories only" (or select specific repos)
   - **Permissions → Packages:** "Read and write"
3. Click "Generate token" and copy it

### Option A: Export directly in your shell

```bash
export GHCR_NAME="your-github-username"
export GHCR_TOKEN="YOUR_TOKEN"
```

Then use `just image-login` as normal.

### Option B: Store the token in macOS Keychain

```bash
security add-generic-password -a "$GHCR_NAME" -s "ghcr-token" -w "YOUR_TOKEN_HERE"
```

Then retrieve it at login time:

```bash
export GHCR_NAME="your-github-username"
export GHCR_TOKEN=$(security find-generic-password -s "ghcr-token" -w)
just image-login
```
