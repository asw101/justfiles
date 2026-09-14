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
| `up [name] [args]` | Create or start a persistent sandbox and open a shell with Copilot authentication (default name: `sandbox`) |
| `down [name]` | Stop a persistent sandbox without deleting it (default name: `sandbox`) |
| `run-tmux [args]` | Detached sandbox with persistent tmux session — resumable across terminal disconnects (does not auto-launch Copilot) |
| `attach-tmux [name]` | Re-attach to the tmux session of a `run-tmux` sandbox |
| `stop-tmux [name]` | Stop the `run-tmux` sandbox container |
| `run-project <project> [args]` | Run with SSH and a project directory mounted |
| `create-named <name> <project>` | Create a persistent named sandbox |
| `attach <name>` | Attach to a named sandbox |
| `delete <name>` | Stop and permanently delete a container; an explicit name is required |
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

## Persistent Sandbox

`up` provides the same token setup as `run-copilot`, but
opens a normal shell in a named container that remains available after the
shell exits. It does not automatically launch an agent. Inside it,
`copilot-shpool` creates or reattaches to a Copilot process that survives
terminal disconnections.

The default container is `sandbox`. Pass a name to use a different one:
`sandbox up dev` creates or opens `dev`, and `sandbox down dev` stops it without
deleting its filesystem. Copilot authentication is configured on creation;
reopening an existing container does not refresh or add its token.

```bash
# Rebuild once after installing this recipe
sandbox image-build

# Create or start the persistent container and open its shell
sandbox up

# Inside the container, create or reattach to Copilot
copilot-shpool

# Detach without stopping Copilot: press Ctrl-Space, release, then Ctrl-q
# You are now back at the container shell; leave it normally
exit

# Later, return to the container shell
sandbox up

# Reattach to the same Copilot process
copilot-shpool

# Stop it without deleting its filesystem
sandbox down

# Restart it and enter its shell
sandbox up

# Delete it when it is no longer needed
sandbox delete sandbox
```

### SSH logins

Interactive SSH logins, including Tailscale SSH, open a plain Bash shell.
Login does not automatically start an agent or attach to tmux or shpool.
Change to your project directory, then run `claude-shpool`, `codex-shpool`,
or `copilot-shpool` to start or reattach to an agent. Detaching returns to the
SSH shell; `exit` then closes the connection. Tmux remains available explicitly.

Existing containers retain their shell configuration. To adopt this behavior
without recreating the container, remove the line containing
`SSH_CONNECTION` and `tmux attach -t main` from `~/.bashrc`.

### Shpool agent sessions

[Shpool](https://github.com/shell-pool/shpool) keeps native terminal scrollback
and copy/paste, and restores the screen on reattach, including output produced
while disconnected. It does not provide tmux-style panes or windows.

Each agent has an independent named session:

```bash
claude-shpool
codex-shpool
copilot-shpool
```

These use the same `*-auto` commands and permission settings as the existing
dtach/tmux helpers. Copilot is updated only when a new session starts.

`codex-auto` uses `--yolo`, disabling approval prompts and Codex's internal
sandbox. It relies on the container for isolation; host-mounted files and
credentials remain accessible. If an existing container reports
`unexpected argument '--full-auto'`, use this command until you
[recreate it from the updated image](#updating-an-existing-sandbox):

```bash
shpool-session "${CODEX_SHPOOL_SESSION:-codex}" codex --yolo
```

Detach with **Ctrl-Space, then Ctrl-q** and run the same helper to reattach.
Shpool starts its daemon automatically; no systemd service is needed.
The helpers restore terminal settings and disable mouse reporting on detach or
exit, so scrolling or clicking at the shell prompt does not require a `reset`.
This cleanup preserves scrollback and does not stop a detached agent session.

```bash
shpool list

# Free a session if an old terminal is still attached, then reconnect
shpool detach copilot
copilot-shpool

# Terminate the agent and remove its session
shpool kill copilot
```

Only one terminal can be attached to a shpool session at a time. The helpers
do not forcibly disconnect another terminal.

Override the names with `CLAUDE_SHPOOL_SESSION`, `CODEX_SHPOOL_SESSION`, or
`COPILOT_SHPOOL_SESSION`. For example:

```bash
COPILOT_SHPOOL_SESSION=feature \
COPILOT_SESSION_NAME=feature \
COPILOT_REMOTE=1 \
copilot-shpool

claude-shpool --resume
codex-shpool resume --last
```

Session names must not contain whitespace, slashes, or braces, and cannot be
`.` or `..`. Arguments are forwarded to the agent, not to shpool. The current
directory, startup arguments, and environment settings apply only when creating
a session; reattaching preserves the existing process and its original directory
and settings. `COPILOT_SESSION_NAME` and `COPILOT_REMOTE` work just like in the
dtach/tmux helpers.

The image installs shpool with Homebrew and configures screen restoration and
environment forwarding in `/etc/shpool/config.toml`. This includes PATH, GitHub
tokens, Claude/OpenAI API credentials and base URLs, and agent config-directory
overrides. Loading `/etc/environment` is disabled so Ubuntu's default PATH
does not overwrite the forwarded Homebrew PATH. SSH-agent forwarding is handled
by shpool itself. To customize shpool, use `~/.config/shpool/config.toml`;
if you set `forward_env`, include
the existing entries from `/etc/shpool/config.toml` because the list is replaced,
not extended. Other exported variables are not automatically forwarded.

### Existing dtach and tmux helpers

The dtach helpers remain available:

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

### Updating an existing sandbox

Rebuilding the image does not update existing containers. To try shpool without
deleting your existing sandbox, build the image and create a differently named
container from your project directory on the host:

```bash
sandbox image-build
sandbox up shpool-dev
```

Alternatively, back up any container-only files and configuration before
deleting the old container with `sandbox delete <name>`; `sandbox up <name>`
will create it from the rebuilt image. Deletion loses the container filesystem,
but not host-mounted project files.

Existing containers are not renamed or deleted when you switch to this
interface. To reopen the old default container, run `sandbox up copilot-sandbox`.
`COPILOT_SANDBOX_NAME` is no longer used; pass the container name directly.

Choose a container name and optionally override the Copilot secret with
`COPILOT_SECRET_NAME`:

```bash
COPILOT_SECRET_NAME=github/my-token sandbox up my-project

# Extra container flags go after the name, even when using the default name
sandbox up sandbox --env FOO=bar
```

Container flags passed after the container name apply only when the container is
first created. The project directory mounted on that first run remains the
workspace on subsequent starts. Closing the host terminal leaves the container
and its shpool-, dtach-, or tmux-managed agent processes running. Stopping the
container terminates those processes and their session managers; after
restarting, run the relevant helper to create a new agent process in the
preserved container. Shpool does not preserve live processes across container
stops or restarts.

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
