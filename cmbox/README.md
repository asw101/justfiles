# Cmbox

A Justfile command named `cmbox` for building and running an isolated Ubuntu
development machine on macOS using
[Apple's `container` CLI](https://github.com/apple/container). Cmbox
deliberately does not mount the host home directory.

## Quick Start

```bash
brew install just

# Build the base and cmbox images
cmbox base-build
cmbox build

# Create and boot the machine
cmbox up

# Open an interactive shell
cmbox run
```

## What's Inside

The cmbox image layers systemd, SSH, and persistent machine support over the
sandbox development toolchain. It includes Homebrew, Rust, Go, `gh`, `just`,
[`mint`](https://github.com/asw101/mint), Tailscale, and coding agents (Claude
Code, GitHub Copilot CLI, OpenAI Codex CLI). `copilot-auto` defaults to GPT-6
Astra. Claude Remote Control can run either as a host-launched process or as a
systemd service inside the machine.

Bubblewrap (`bwrap`) is included for Codex's Linux sandbox.
Codex is installed with the [official standalone installer](https://chatgpt.com/codex/install.sh),
not Homebrew, so `codex remote-control` can find its managed app-server package.
The standalone base seeds a `~/.codex/packages/standalone` link to the shared
installation under `/opt/cmbox`; each machine user's credentials and configuration
remain in their own `~/.codex`.
Existing machine users should run the installer in their own shell; rebuilding
an image does not update their home directories.

## Recipes

Run `cmbox` to see all available recipes. Highlights:

| Recipe | Description |
|---|---|
| `base-build [args]` | Build the base image from `cmbox/base/` |
| `build [args]` | Build the cmbox image from the base image |
| `build-from-sandbox [args]` | Build the cmbox image from `sandbox:latest` |
| `up` | Create and boot the machine |
| `run [command]` | Open a shell or run a command inside the machine |
| `sh <script>` | Run a shell script while preserving shell syntax |
| `cp <src> <dst>` | Copy files to or from the machine |
| `rc [dir]` | Start or restart Claude Remote Control |
| `rc-stop` | Stop Claude Remote Control |
| `status` | Show machine state |
| `stop` | Stop the machine |
| `delete --yes` | Delete the machine and its disk |
| `logs` | Show machine boot logs |

## Image Build Paths

The default path builds cmbox's own base from the `cmbox/base/` build
context:

```bash
cmbox base-build
cmbox build
```

`cmbox/base/` is cmbox's own build context, not a copy of the sibling
[`sandbox`](../sandbox/) command. The two images diverged deliberately: cmbox
builds its tooling under a stable `cmbox` user at `/opt/cmbox` because Apple
creates the machine user at runtime, seeds configuration through `/etc/skel`,
and adds an entrypoint. There is no baseline to reconcile against.

Alternatively, build on top of `sandbox:latest`, which the sibling `sandbox`
command produces:

```bash
sandbox image-build
cmbox build-from-sandbox
```

The steps are intentionally separate so the base image can be reused.

## SSH Logins

Interactive Bash logins over SSH open a plain shell, without automatically
starting an agent or attaching to tmux or shpool. Start your chosen agent or
session manager explicitly after changing to the desired workspace. Tmux
remains installed; the standalone cmbox base does not include shpool helpers.

The standalone base seeds this shell configuration through `/etc/skel` for
new machine users. Existing machines and home directories are not updated by
an image rebuild. To update an existing user, remove the line containing
`SSH_CONNECTION` and `tmux attach -t main` from their `~/.bashrc`; remove it
from `/etc/skel/.bashrc` as well if present, so future users inherit the same
behavior.

## Running Commands

```bash
# Interactive shell
cmbox run

# Argument-safe command execution
cmbox run printf 'value: %s\n' "hello world"

# Pipelines and shell syntax
cmbox sh 'printf "%s\n" alpha beta | sort -r'

# Copy into and out of the machine
cmbox cp ./input.txt cmbox:/home/user/tmp/input.txt
cmbox cp cmbox:/home/user/tmp/output.txt ./output.txt
```

Command arguments are encoded before crossing `container machine run`, which
otherwise joins and reparses them. This preserves quotes, pipelines, variables,
and metacharacters.

## Claude Remote Control

`cmbox rc` starts Claude Remote Control under `nohup` and survives the host
command exiting. For a service that also survives machine reboots, follow
[`init/README.md`](init/README.md). Authenticate with `claude auth login` inside
the machine before starting Remote Control.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CMBOX_MACHINE` | `cmbox` | Machine name |
| `CMBOX_IMAGE` | `local/cmbox:26.04` | Cmbox image |
| `CMBOX_BASE_IMAGE` | `cmbox-sandbox:latest` | Standalone base image |
| `CMBOX_CPUS` | `4` | vCPUs assigned at creation |
| `CMBOX_MEMORY` | `8G` | Memory assigned at creation |
| `CMBOX_DISK` | unset | Disk size at creation, for example `120G`. **No `container` CLI version through 1.3.0 supports this**; the script discovers the flag from `machine create --help` and errors if absent, so it starts working the day one is added |
| `CMBOX_HOME_MOUNT` | `none` | Host home mount mode: `none`, `ro`, or `rw` |

CPU and memory settings apply when the machine is created. To resize an
existing machine, use `container machine set`, then restart it.

## Run from Anywhere

Run `just alias` from the repository root and add the emitted `cmbox` alias to
your shell configuration.
