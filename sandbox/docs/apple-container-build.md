# Building & Running Sandbox Containers with Apple Containerization

Build and run the `sandbox` container image using Apple's native `container` CLI on macOS.

## Prerequisites

| Requirement | Details |
|---|---|
| **Hardware** | Apple Silicon Mac (M1/M2/M3/M4) |
| **OS** | macOS 26 (Tahoe) or later |
| **Tool** | Apple `container` CLI ([releases](https://github.com/apple/container/releases)) |
| **Homebrew** | Installed on the host (for `just` command runner) |

## 1. Install Apple `container` CLI

Download and install the latest `.pkg` from [GitHub Releases](https://github.com/apple/container/releases):

```bash
# Download (adjust version as needed)
curl -LO https://github.com/apple/container/releases/download/0.4.1/container-0.4.1-installer-signed.pkg

# Install
sudo installer -pkg container-0.4.1-installer-signed.pkg -target /

# Start the system service (installs a default Linux kernel on first run)
container system start
```

Verify it's running:

```bash
container list --all
```

## 2. Install `just` (command runner)

```bash
brew install just
```

## 3. Build the Sandbox Image

The `sandbox/Dockerfile` builds an Ubuntu-based image with Homebrew, `gh`, `just`, and three coding agents pre-installed:
- **Claude Code** (`claude` / `claude-auto`)
- **GitHub Copilot CLI** (`copilot` / `copilot-auto`)
- **OpenAI Codex CLI** (`codex` / `codex-auto`)

### Build with Apple `container` CLI

```bash
cd sandbox

# Build the image (equivalent to `just image-build`)
container build --tag sandbox --file Dockerfile .
```


> **Tip:** The Homebrew install inside the image is resource-intensive. Increase builder resources if it fails:

```bash
container builder stop && container builder delete
container builder start --cpus 8 --memory 8g
container build --tag sandbox --file Dockerfile .
```

### Verify the image was built

```bash
container image list
# Should show: sandbox  latest  <digest>
```

## 4. Run the Container Interactively

### Basic interactive shell

```bash
container run -it --rm sandbox /bin/bash
```

### Mount a project directory from your host

Use `--volume` to bind-mount a local project into the container:

```bash
container run -it --rm \
  --volume /path/to/your/project:/home/agent/project \
  sandbox /bin/bash
```

### Run with more resources (recommended for coding agents)

```bash
container run -it --rm \
  --cpus 8 \
  --memory 8g \
  --volume /path/to/your/project:/home/agent/project \
  sandbox /bin/bash
```

### Forward SSH keys into the container

To clone private repos or push to GitHub from inside the container:

```bash
container run -it --rm \
  --ssh \
  --volume /path/to/your/project:/home/agent/project \
  sandbox /bin/bash
```

## 5. Run a Coding Agent Inside the Container

Once inside the container shell, the agents are available via wrapper scripts:

### Claude Code
```bash
# Interactive mode
claude

# Auto mode (skips permission prompts)
claude-auto
```

### GitHub Copilot CLI
```bash
# Interactive mode
copilot

# Auto mode (allows all tools)
copilot-auto
```

### OpenAI Codex CLI
```bash
# Interactive mode
codex

# Full-auto mode
codex-auto
```

### Authentication

The agents need API keys / auth tokens. Pass them as environment variables:

```bash
container run -it --rm \
  --volume /path/to/your/project:/home/agent/project \
  --env GH_TOKEN=ghp_... \
  --env ANTHROPIC_API_KEY=sk-ant-... \
  --env OPENAI_API_KEY=sk-... \
  --ssh \
  sandbox /bin/bash
```

For GitHub Copilot CLI, authenticate with `gh` inside the container:

```bash
gh auth login
```

## 6. Named Containers (Persistent)

Instead of `--rm`, create a named container you can stop/restart:

```bash
# Create and start
container run -d --name my-sandbox \
  --cpus 8 --memory 8g \
  --volume ~/projects:/home/agent/projects \
  --ssh \
  sandbox /bin/bash -c "sleep infinity"

# Attach to it
container exec -it my-sandbox /bin/bash

# Stop when done
container stop my-sandbox

# Restart later
container start my-sandbox
container exec -it my-sandbox /bin/bash

# Delete when finished
container stop my-sandbox
container delete my-sandbox
```

## 7. Push / Pull from GitHub Container Registry

To publish your build:

```bash
container registry login ghcr.io
container image tag sandbox ghcr.io/YOUR_USERNAME/sandbox:latest
container image push ghcr.io/YOUR_USERNAME/sandbox:latest
```

To pull a pre-built image:

```bash
container image pull ghcr.io/YOUR_USERNAME/sandbox:latest

container run -it --rm \
  --volume ~/myproject:/home/agent/project \
  ghcr.io/YOUR_USERNAME/sandbox:latest /bin/bash
```

## Comparison: `docker` vs `container` Commands

| Task | Docker / `docker sandbox` | Apple `container` |
|---|---|---|
| Build image | `docker build -t sandbox .` | `container build --tag sandbox .` |
| Run interactive | `docker run -it --rm sandbox bash` | `container run -it --rm sandbox bash` |
| Mount volume | `docker run -v /host:/guest ...` | `container run --volume /host:/guest ...` |
| Run sandbox (Docker-specific) | `docker sandbox run -t sandbox:latest claude ~/project` | *(see interactive run above)* |
| List images | `docker images` | `container image list` |
| List containers | `docker ps -a` | `container list --all` |
| Exec into running | `docker exec -it name bash` | `container exec -it name bash` |
| Stop | `docker stop name` | `container stop name` |
| Remove | `docker rm name` | `container delete name` |
| System start/stop | *(Docker Desktop app)* | `container system start/stop` |

## Troubleshooting

### Build fails with OOM
Increase builder resources:
```bash
container builder stop && container builder delete
container builder start --cpus 8 --memory 16g
```

### Container won't start
Ensure the system service is running:
```bash
container system start
```

### Slow network inside container
Each container gets its own VM with a unique IP. Verify connectivity:
```bash
container exec my-sandbox ping -c1 8.8.8.8
```

### "Unsupported" errors
Confirm you're on macOS 26+ and Apple Silicon. The `container` CLI does not support Intel Macs or older macOS versions.
