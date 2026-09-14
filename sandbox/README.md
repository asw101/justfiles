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
`just`, [`mint`](https://github.com/asw101/mint), Tailscale, and coding agents
(Claude Code, GitHub Copilot CLI, OpenAI Codex CLI). Copilot CLI is
preconfigured with `rust-analyzer` and `gopls` for Rust and Go code
intelligence, and defaults to GPT-6 Astra both directly and through
`copilot-auto`. Sandbox launch recipes forward the host SSH agent by default for
Git authentication and SSH commit signing.

## Recipes

Run `just` to see all available recipes. Highlights:

| Recipe | Description |
|---|---|
| `image-build` | Build the sandbox image |
| `run [args]` | Interactive shell with current directory mounted |
| `run-copilot [args]` | Pull `COPILOT_GITHUB_TOKEN` from [`secret`](../secret/), optionally forward host `GH_TOKEN`, update Copilot CLI, launch in YOLO mode |
| `run-copilot-persistent [args]` | Open a shell in a persistent named container with Copilot authentication |
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

`run-copilot` automates a common workflow: it pulls `COPILOT_GITHUB_TOKEN` from the
sibling [`secret`](../secret/) Justfile, runs `copilot update` inside the
container, then launches `copilot --allow-all-tools` (YOLO mode).

The secret is only used for Copilot authentication; it is not assigned to
`GH_TOKEN`. If `GH_TOKEN` is set on the host, it is also passed through unchanged
for `gh` and Git HTTPS authentication. Copilot prefers `COPILOT_GITHUB_TOKEN`
over `GH_TOKEN`, so both credentials can coexist without sharing permissions.

```bash
# Uses github/260500-token-copilot
sandbox run-copilot

# Override the secret name or backend
COPILOT_SECRET_NAME=github/my-token sandbox run-copilot
SECRET_SOURCE=keychain sandbox run-copilot

# Pass extra container flags after the recipe name
sandbox run-copilot --env FOO=bar
```

## Persistent Copilot Sandbox

`run-copilot-persistent` provides the same token setup as `run-copilot`, but
opens a normal shell in a named container that remains available after the
shell exits. Inside it, `copilot-dtach` creates or reattaches to a Copilot
process that survives terminal disconnections.

```bash
# Rebuild once after installing this recipe
sandbox image-build

# Create or start the persistent container and open its shell
sandbox run-copilot-persistent

# Inside the container, create or reattach to Copilot
copilot-dtach

# Detach from Copilot without stopping it: press Ctrl-\
# You are now back at the container shell; leave it normally
exit

# Later, return to the container shell
sandbox run-copilot-persistent

# Reattach to the same Copilot process
copilot-dtach

# Stop it without deleting its filesystem
sandbox stop copilot-sandbox

# Restart it and enter its shell
sandbox run-copilot-persistent

# Delete it when it is no longer needed
sandbox delete copilot-sandbox
```

The same container includes equivalent helpers for Claude Code and Codex. Each
uses its own `dtach` session, so the agents can run independently:

```bash
claude-dtach
codex-dtach
copilot-dtach
```

Press `Ctrl-\` to detach from any helper, then run the same helper again to
reattach. The helpers restore normal terminal and mouse modes after detaching.
On reattach, they send a terminal resize signal so full-screen agent interfaces
redraw the complete window.
Override their socket paths with `CLAUDE_DTACH_SOCKET`, `CODEX_DTACH_SOCKET`,
or `COPILOT_DTACH_SOCKET`.

For persistent scrollback, reliable full-screen redraws, and multiple windows,
use the equivalent tmux helpers:

```bash
claude-tmux
codex-tmux
copilot-tmux
```

Each command creates its agent's tmux session or attaches to it when it already
exists. Detach with `Ctrl-a d`, then run the same command to reattach. Override
the tmux session names with `CLAUDE_TMUX_SESSION`, `CODEX_TMUX_SESSION`, or
`COPILOT_TMUX_SESSION`. For example:

```bash
COPILOT_TMUX_SESSION=feature \
COPILOT_SESSION_NAME=feature \
COPILOT_REMOTE=1 \
copilot-tmux
```

Startup arguments and environment settings apply only when a helper creates its
tmux session. When that tmux session already exists, the helper reattaches and
ignores new startup arguments.

Name a new Copilot session and enable remote control with environment variables:

```bash
COPILOT_SESSION_NAME=my-project COPILOT_REMOTE=1 copilot-dtach
```

This starts Copilot as `copilot --name my-project --remote`. The values apply
only when `dtach` creates a new Copilot process; when the socket already has a
running process, `copilot-dtach` reattaches to it instead. You can also pass the
native flags directly:

```bash
copilot-dtach --name my-project --remote
```

If `copilot-sandbox` was created from an older image, delete it once with
`sandbox delete copilot-sandbox` before the first run so the recipe creates it
from the rebuilt image.

Override the default container name or Copilot secret with
`COPILOT_SANDBOX_NAME` or `COPILOT_SECRET_NAME`:

```bash
COPILOT_SANDBOX_NAME=my-project \
COPILOT_SECRET_NAME=github/my-token \
sandbox run-copilot-persistent
```

Container flags passed after the recipe name apply only when the container is
first created. The project directory mounted on that first run remains the
workspace on subsequent starts. Closing the host terminal leaves the container
and its `dtach`-managed Copilot process running. Stopping the container
terminates Copilot and `dtach`; after restarting, run `copilot-dtach` to create
a new Copilot process in the preserved container.

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
