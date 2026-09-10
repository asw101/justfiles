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

The Dockerfile builds an Ubuntu-based image with Homebrew, Rust, Go, `gh`,
`just`, Tailscale, and coding agents (Claude Code, GitHub Copilot CLI, OpenAI
Codex CLI). Copilot CLI is preconfigured with `rust-analyzer` and `gopls` for
Rust and Go code intelligence. Sandbox launch recipes forward the host SSH
agent by default for Git authentication and SSH commit signing.

## Recipes

Run `just` to see all available recipes. Highlights:

| Recipe | Description |
|---|---|
| `image-build` | Build the sandbox image |
| `run [args]` | Interactive shell with current directory mounted |
| `run-copilot [args]` | Pull `GH_TOKEN` from [`secret`](../secret/), update Copilot CLI, launch in YOLO mode |
| `run-tmux [args]` | Detached sandbox with persistent tmux session — resumable across terminal disconnects (does not auto-launch Copilot) |
| `attach-tmux [name]` | Re-attach to the tmux session of a `run-tmux` sandbox |
| `stop-tmux [name]` | Stop the `run-tmux` sandbox container |
| `run-project <project> [args]` | Run with SSH and a project directory mounted |
| `create-named <name> <project>` | Create a persistent named sandbox |
| `attach <name>` | Attach to a named sandbox |
| `image-release` | Build, tag, and push to GHCR |
| `run-tailscale` | Run with Tailscale networking |

## SSH Agent and Commit Signing

Run recipes pass Apple Container's `--ssh` option by default. This exposes the
macOS SSH agent inside the container without copying private keys. Set
`SANDBOX_SSH=0` to disable forwarding.

Create or load a key on the host and register its public key as a GitHub
signing key. For 1Password, enable **Settings → Developer → Use the SSH
agent**, create an Ed25519 SSH key, and add its public key at
<https://github.com/settings/ssh/new> with **Key type: Signing Key**.

```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
gh ssh-key add ~/.ssh/id_ed25519.pub --type signing --title "Apple Container signing"
```

At startup, the sandbox makes Apple Container's forwarded socket accessible to
the `agent` user, matches the forwarded keys against the current GitHub
account's signing keys, enables SSH commit and tag signing, and configures
GitHub CLI credentials for HTTPS pushes. This is automatic when `GH_TOKEN` is
available.

To configure signing manually or override an ambiguous match:

```bash
# With one forwarded key
git-signing-setup

# With multiple keys, select one by fingerprint or unique comment
git-signing-setup SHA256:...
git-signing-setup apple-container-signing
```

The helper stores only the selected public key in the container. Confirm that
the agent is available at any time with `ssh-add -L`.

## Passing Environment Variables

Pass extra env vars into the container with `--env`:

```bash
# Pass a variable with a value
just run --env FOO=bar

# Pass through a host variable
just run --env MY_SECRET
```

`GH_TOKEN` is passed through automatically when set.

## YOLO Copilot Run

`run-copilot` automates a common workflow: it pulls `GH_TOKEN` from the
sibling [`secret`](../secret/) Justfile, runs `copilot update` inside the
container, then launches `copilot --allow-all-tools` (YOLO mode).

```bash
# Uses SECRET_NAME (default: github/260200-token) from the secret Justfile
sandbox run-copilot

# Override the secret name or backend
SECRET_NAME=github/my-token sandbox run-copilot
SECRET_SOURCE=keychain sandbox run-copilot

# Pass extra container flags after the recipe name
sandbox run-copilot --env FOO=bar
```

## Resumable Tmux Sandbox

`run-tmux` is an alternative to `run-copilot` for workflows where you want the
container to survive closing the terminal that started it.

```bash
# Start a detached sandbox with the current directory mounted; lands you in tmux
sandbox run-tmux

# Inside the tmux session, launch Copilot yourself (or anything else)
copilot-auto

# Detach with: C-a d  (container keeps running)

# From any terminal, rejoin:
sandbox attach-tmux

# When you're done:
sandbox stop-tmux
```

Differences vs. `run-copilot`:

- Container runs **detached** (`-d`) with a fixed `--name`, so closing the host
  terminal does not kill it. Override the name with `TMUX_SANDBOX_NAME=...`.
- A tmux session named `main` inside the container is the keep-alive — when it
  ends (e.g. you exit the last shell in it), the container exits and `--rm`
  cleans it up.
- It does **not** run `copilot update` or auto-start Copilot — you do that
  yourself once you're inside the tmux session.
- Nothing is persisted to the host beyond the mounted working directory, so
  Copilot sessions live only for the lifetime of the container.

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
