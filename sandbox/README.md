# Sandbox

A Justfile for building and running sandboxed development containers on macOS using [Apple's `container` CLI](https://github.com/apple/container).

## Quick Start

```bash
brew install just

# Start the container system service
just system-start

# Build the sandbox image
just image-build

# Run with your project mounted
just run-project ~/myproject
```

## What's Inside

The Dockerfile builds an Ubuntu-based image with Homebrew, `gh`, `just`, Tailscale, and coding agents (Claude Code, GitHub Copilot CLI, OpenAI Codex CLI).

## Recipes

Run `just` to see all available recipes. Highlights:

| Recipe | Description |
|---|---|
| `image-build` | Build the sandbox image |
| `run [args]` | Interactive shell with current directory mounted |
| `run-project <project> [args]` | Run with SSH and a project directory mounted |
| `create-named <name> <project>` | Create a persistent named sandbox |
| `attach <name>` | Attach to a named sandbox |
| `image-release` | Build, tag, and push to GHCR |
| `run-tailscale` | Run with Tailscale networking |

## Passing Environment Variables

Pass extra env vars into the container with `--env`:

```bash
# Pass a variable with a value
just run --env FOO=bar

# Pass through a host variable
just run --env MY_SECRET
```

`GH_TOKEN` is passed through automatically when set.

## Run from Anywhere

Set up a shell alias so you can use `sandbox <recipe>` from any directory:

```bash
alias sandbox='just --justfile ~/path/to/Justfile'
```

See [docs/just-alias-setup.md](docs/just-alias-setup.md) for details.

## Docs

- [Apple Container Build Guide](docs/apple-container-build.md)
- [GitHub Container Registry](docs/apple-container-ghcr.md)
- [Just Alias Setup](docs/just-alias-setup.md)
- [Tmux](docs/tmux.md)
