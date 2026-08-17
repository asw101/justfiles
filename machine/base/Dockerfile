FROM ubuntu:latest

USER root

# Install dependencies for Homebrew and Tailscale.
#
# The bison/flex/libicu-dev/libreadline-dev group is for building PostgreSQL
# from source, which `cargo pgrx init` does (component-pg's e2e harness). PG 16+
# configures with ICU by default and aborts with "Package requirements (icu-uc
# icu-i18n) were not met" without the dev headers; readline is required next.
# That harness is explicitly designed to need no sudo and no apt at run time,
# so these have to be baked in here rather than installed on the fly.
#
# lld is required by component-pg's .cargo/config.toml, which pins
# -Clink-arg=-fuse-ld=lld on linux because ld.bfd OOMs in a 3 GiB container
# linking pgrx + wasmtime. Without it, cargo fails with the misleading
# "collect2: fatal error: cannot find 'ld'" even though GNU ld is present.
#
# clang/libclang-dev back pgrx-pg-sys, which runs bindgen against the PG
# server headers: without libclang.so it panics with "Unable to find
# libclang". The libxml2/libxslt/xsltproc group is the rest of pgrx's
# documented prerequisite set, added together to stop rediscovering them
# one failed build at a time.
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    file \
    git \
    procps \
    bison \
    ca-certificates \
    clang \
    flex \
    iptables \
    sudo \
    tmux \
    jq \
    libclang-dev \
    libicu-dev \
    libreadline-dev \
    libssl-dev \
    libxml2-dev \
    libxml2-utils \
    libxslt1-dev \
    lld \
    openssh-client \
    xsltproc \
    pkg-config \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Tailscale
RUN curl -fsSL https://tailscale.com/install.sh | sh

# Create a stable build user and tool home. The machine layer later assigns
# these installations to whichever user Apple creates for the host account.
RUN useradd -m -d /opt/cmbox -s /bin/bash cmbox && \
    echo "cmbox ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    mkdir -p /home/linuxbrew/.linuxbrew && \
    chown -R cmbox:cmbox /home/linuxbrew

# Install development tools under stable, username-independent paths.
USER cmbox
ENV HOME=/opt/cmbox
WORKDIR /opt/cmbox

RUN NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add brew to PATH
ENV PATH="/home/linuxbrew/.linuxbrew/bin:/opt/cmbox/.cargo/bin:/opt/cmbox/.local/bin:${PATH}"

# Set a short prompt, add brew to PATH for login shells (Tailscale SSH),
# and auto-attach to tmux on SSH login
RUN echo 'export PATH="/home/linuxbrew/.linuxbrew/bin:/opt/cmbox/.cargo/bin:/opt/cmbox/.local/bin:$PATH"' >> /opt/cmbox/.bashrc && \
    echo "PS1='\\W \$ '" >> /opt/cmbox/.bashrc && \
    echo 'if [ -n "$SSH_CONNECTION" ] && [ -z "$TMUX" ]; then tmux attach -t main 2>/dev/null || tmux new -s main; fi' >> /opt/cmbox/.bashrc && \
    echo '[ -f ~/.bashrc ] && . ~/.bashrc' > /opt/cmbox/.profile

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
    > /opt/cmbox/.tmux.conf

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

# Create wrapper scripts
USER root
COPY scripts/git-signing-setup /usr/local/bin/git-signing-setup
COPY scripts/sandbox-init /usr/local/bin/sandbox-init
RUN chmod +x /usr/local/bin/git-signing-setup /usr/local/bin/sandbox-init && \
    echo '#!/bin/bash\nexec claude --dangerously-skip-permissions "$@"' > /usr/local/bin/claude-auto && chmod +x /usr/local/bin/claude-auto && \
    echo '#!/bin/bash\nexec codex --full-auto "$@"' > /usr/local/bin/codex-auto && chmod +x /usr/local/bin/codex-auto && \
    echo '#!/bin/bash\nexec copilot --allow-all-tools --model gpt-5.6-sol --effort high "$@"' > /usr/local/bin/copilot-auto && chmod +x /usr/local/bin/copilot-auto && \
    for dir in \
      /home/linuxbrew/.linuxbrew/bin \
      /opt/cmbox/.cargo/bin \
      /opt/cmbox/.local/bin; do \
      for tool in "$dir"/*; do \
        ln -sf "$tool" "/usr/local/bin/${tool##*/}"; \
      done; \
    done && \
    for tool in /opt/cmbox/.cargo/bin/*; do \
      name="${tool##*/}"; \
      rm -f "/usr/local/bin/$name"; \
      printf '%s\n' \
        '#!/bin/sh' \
        'export CARGO_HOME=/opt/cmbox/.cargo' \
        'export RUSTUP_HOME=/opt/cmbox/.rustup' \
        "exec $tool \"\$@\"" \
        > "/usr/local/bin/$name"; \
      chmod 755 "/usr/local/bin/$name"; \
    done

USER cmbox

# Copilot CLI config: disable co-author attribution and pre-trust the workspace
RUN mkdir -p /opt/cmbox/.copilot && \
    echo '{"include_coauthor":false,"trustedFolders":["/home"],"remoteExport":false}' > /opt/cmbox/.copilot/config.json

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
    > /opt/cmbox/.copilot/lsp-config.json

# Claude Code config: disable co-author attribution
RUN mkdir -p /opt/cmbox/.claude && \
    echo '{"attribution":{"commit":"","pr":""}}' > /opt/cmbox/.claude/settings.json

USER root

# Apple creates the machine user at runtime with a host-derived UID. Keep the
# shared tool installations writable without depending on that UID, and seed
# user configuration through the standard account skeleton.
RUN install -d /etc/skel/.copilot /etc/skel/.claude && \
    cp /opt/cmbox/.copilot/config.json /opt/cmbox/.copilot/lsp-config.json \
      /etc/skel/.copilot/ && \
    cp /opt/cmbox/.claude/settings.json /etc/skel/.claude/ && \
    cp /opt/cmbox/.tmux.conf /etc/skel/.tmux.conf && \
    chmod -R a+rwX /opt/cmbox /home/linuxbrew

USER cmbox

ENTRYPOINT ["/usr/local/bin/sandbox-init"]
