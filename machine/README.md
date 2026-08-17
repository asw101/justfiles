# Machine

A Justfile for building and running an isolated Ubuntu development machine on
macOS using [Apple's `container` CLI](https://github.com/apple/container).
The machine deliberately does not mount the host home directory.

## Quick Start

```bash
brew install just

# Build the standalone sandbox base and machine image
machine base-build
machine build

# Create and boot the machine
machine up

# Open an interactive shell
machine run
```

## What's Inside

The machine image layers systemd, SSH, and persistent machine support over the
sandbox development toolchain. It includes Homebrew, Rust, Go, `gh`, `just`,
Tailscale, and coding agents (Claude Code, GitHub Copilot CLI, OpenAI Codex
CLI). Claude Remote Control can run either as a host-launched process or as a
systemd service inside the machine.

## Recipes

Run `machine` to see all available recipes. Highlights:

| Recipe | Description |
|---|---|
| `base-build [args]` | Build the vendored standalone sandbox base |
| `sandbox-build [args]` | Build the sibling [`sandbox`](../sandbox/) image |
| `build [args]` | Build the machine image from the vendored base |
| `build-from-sandbox [args]` | Build the machine image from `sandbox:latest` |
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

The standalone path uses the vendored `machine/sandbox/` build context:

```bash
machine base-build
machine build
```

The in-repository path builds the sibling [`sandbox`](../sandbox/) image first:

```bash
machine sandbox-build
machine build-from-sandbox
```

The steps are intentionally separate so the base image can be reused. Use
`machine sandbox-diff` to inspect changes between the vendored baseline and the
sibling sandbox, then `machine sandbox-merge` to refresh the baseline.

## Running Commands

```bash
# Interactive shell
machine run

# Argument-safe command execution
machine run printf 'value: %s\n' "hello world"

# Pipelines and shell syntax
machine sh 'printf "%s\n" alpha beta | sort -r'

# Copy into and out of the machine
machine cp ./input.txt machine:/home/user/tmp/input.txt
machine cp machine:/home/user/tmp/output.txt ./output.txt
```

Command arguments are encoded before crossing `container machine run`, which
otherwise joins and reparses them. This preserves quotes, pipelines, variables,
and metacharacters.

## Claude Remote Control

`machine rc` starts Claude Remote Control under `nohup` and survives the host
command exiting. For a service that also survives machine reboots, follow
[`init/README.md`](init/README.md). Authenticate with `claude auth login` inside
the machine before starting Remote Control.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CMBOX_MACHINE` | `cmbox` | Machine name |
| `CMBOX_IMAGE` | `local/ubuntu-machine:26.04` | Machine image |
| `CMBOX_BASE_IMAGE` | `cmbox-sandbox:latest` | Standalone base image |
| `CMBOX_CPUS` | `4` | vCPUs assigned at creation |
| `CMBOX_MEMORY` | `8G` | Memory assigned at creation |
| `CMBOX_HOME_MOUNT` | `none` | Host home mount mode: `none`, `ro`, or `rw` |

CPU and memory settings apply when the machine is created. To resize an
existing machine, use `container machine set`, then restart it.

## Run from Anywhere

Run `just alias` from the repository root and add the emitted `machine` alias to
your shell configuration.
