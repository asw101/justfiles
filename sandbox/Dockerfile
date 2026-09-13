FROM ubuntu:26.04

USER root

# Install dependencies for Homebrew and Tailscale
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    file \
    git \
    procps \
    ca-certificates \
    dtach \
    iptables \
    sudo \
    tmux \
    jq \
    libssl-dev \
    openssh-client \
    pkg-config \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Tailscale
RUN curl -fsSL https://tailscale.com/install.sh | sh

# Create agent user with sudo access and linuxbrew directory
RUN useradd -m -s /bin/bash agent && \
    echo "agent ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/agent && \
    chmod 0440 /etc/sudoers.d/agent && \
    mkdir -p /home/linuxbrew/.linuxbrew && \
    chown -R agent:agent /home/linuxbrew

# Install Homebrew as agent user
USER agent
ENV HOME=/home/agent
WORKDIR /home/agent

RUN NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add brew to PATH
ENV PATH="/home/agent/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/bin:/home/agent/.cargo/bin:/home/agent/.local/bin:${PATH}"

# Set a short prompt, add brew to PATH for login shells (Tailscale SSH),
# and auto-attach to tmux on SSH login
RUN echo 'export PATH="/home/agent/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/bin:/home/agent/.cargo/bin:/home/agent/.local/bin:$PATH"' >> /home/agent/.bashrc && \
    echo "PS1='\\W \$ '" >> /home/agent/.bashrc && \
    echo 'if [ -n "$SSH_CONNECTION" ] && [ -z "$TMUX" ]; then tmux attach -t main 2>/dev/null || tmux new -s main; fi' >> /home/agent/.bashrc && \
    echo '[ -f ~/.bashrc ] && . ~/.bashrc' > /home/agent/.profile

# Configure tmux: easy prefix (Ctrl+a), mouse mode, status bar hint
RUN printf '%s\n' \
    'set -g prefix C-a' \
    'unbind C-b' \
    'bind C-a send-prefix' \
    'set -g mouse on' \
    'set -g status-right " detach: C-a d | new window: C-a c "' \
    'set -g status-style "bg=blue,fg=white"' \
    'set -g base-index 1' \
    'set -g history-limit 50000' \
    > /home/agent/.tmux.conf

# Install development tools, language servers, and coding agents
RUN brew install gh just go gopls rust-analyzer codex

# Install the stable Rust toolchain with Cargo, Rustfmt, and Clippy
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | \
    sh -s -- -y --profile default && \
    rustup component add rust-src

# Install Claude Code (latest release, direct binary download)
RUN curl -fsSL https://claude.ai/install.sh | bash

# Install Copilot CLI (latest release, direct binary download)
RUN curl -fsSL https://gh.io/copilot-install | bash

# Install mint from a checksummed release artifact.
USER root
ARG MINT_VERSION=v0.8.0
RUN arch="$(dpkg --print-architecture)" && \
    case "$arch" in amd64|arm64) ;; *) echo "unsupported mint architecture: $arch" >&2; exit 1;; esac && \
    base="https://github.com/asw101/mint/releases/download/${MINT_VERSION}" && \
    curl -fsSLo "/tmp/mint_linux_${arch}" "$base/mint_linux_${arch}" && \
    curl -fsSLo /tmp/SHA256SUMS "$base/SHA256SUMS" && \
    grep " mint_linux_${arch}$" /tmp/SHA256SUMS | (cd /tmp && sha256sum -c -) && \
    install -m 0755 "/tmp/mint_linux_${arch}" /usr/local/bin/mint && \
    rm -f "/tmp/mint_linux_${arch}" /tmp/SHA256SUMS

# Create wrapper scripts
COPY scripts/git-signing-setup /usr/local/bin/git-signing-setup
COPY scripts/sandbox-init /usr/local/bin/sandbox-init
RUN chmod +x /usr/local/bin/git-signing-setup /usr/local/bin/sandbox-init && \
    echo '#!/bin/bash\nexec claude --dangerously-skip-permissions "$@"' > /usr/local/bin/claude-auto && chmod +x /usr/local/bin/claude-auto && \
    echo '#!/bin/bash\nexec codex --full-auto "$@"' > /usr/local/bin/codex-auto && chmod +x /usr/local/bin/codex-auto && \
    echo '#!/bin/bash\nexec copilot --allow-all-tools --model gpt-6-astra --effort high "$@"' > /usr/local/bin/copilot-auto && chmod +x /usr/local/bin/copilot-auto

USER agent

# Copilot CLI config: default to GPT-6 Astra, disable co-author attribution,
# and pre-trust the workspace
RUN mkdir -p /home/agent/.copilot && \
    echo '{"include_coauthor":false,"trustedFolders":["/home/agent/pwd"],"remoteExport":false}' > /home/agent/.copilot/config.json && \
    echo '{"model":"gpt-6-astra"}' > /home/agent/.copilot/settings.json

# Make Rust and Go code intelligence available to Copilot CLI
RUN printf '%s\n' \
    '{' \
    '  "lspServers": {' \
    '    "rust-analyzer": {' \
    '      "command": "rust-analyzer",' \
    '      "args": [],' \
    '      "fileExtensions": {".rs": "rust"},' \
    '      "requestTimeoutMs": 120000' \
    '    },' \
    '    "gopls": {' \
    '      "command": "gopls",' \
    '      "args": [],' \
    '      "fileExtensions": {".go": "go"},' \
    '      "requestTimeoutMs": 120000' \
    '    }' \
    '  }' \
    '}' \
    > /home/agent/.copilot/lsp-config.json

# Claude Code config: disable co-author attribution
RUN mkdir -p /home/agent/.claude && \
    echo '{"attribution":{"commit":"","pr":""}}' > /home/agent/.claude/settings.json

ENTRYPOINT ["/usr/local/bin/sandbox-init"]
CMD ["/bin/bash"]
