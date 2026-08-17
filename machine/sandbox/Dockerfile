FROM ubuntu:latest

USER root

# Install dependencies for Homebrew, Tailscale, and local PostgreSQL builds.
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

RUN curl -fsSL https://tailscale.com/install.sh | sh

# Use stable paths because Apple creates the machine user at runtime.
RUN useradd -m -d /opt/cmbox -s /bin/bash cmbox && \
    echo "cmbox ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    mkdir -p /home/linuxbrew/.linuxbrew && \
    chown -R cmbox:cmbox /home/linuxbrew

USER cmbox
ENV HOME=/opt/cmbox
WORKDIR /opt/cmbox

RUN NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

ENV PATH="/home/linuxbrew/.linuxbrew/bin:/opt/cmbox/.cargo/bin:/opt/cmbox/.local/bin:${PATH}"

RUN echo 'export PATH="/home/linuxbrew/.linuxbrew/bin:/opt/cmbox/.cargo/bin:/opt/cmbox/.local/bin:$PATH"' >> /opt/cmbox/.bashrc && \
    echo "PS1='\\W \$ '" >> /opt/cmbox/.bashrc && \
    echo 'if [ -n "$SSH_CONNECTION" ] && [ -z "$TMUX" ]; then tmux attach -t main 2>/dev/null || tmux new -s main; fi' >> /opt/cmbox/.bashrc && \
    echo '[ -f ~/.bashrc ] && . ~/.bashrc' > /opt/cmbox/.profile

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

RUN brew install gh just go gopls rust-analyzer codex

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | \
    sh -s -- -y --profile default && \
    rustup component add rust-src

RUN curl -fsSL https://claude.ai/install.sh | bash
RUN curl -fsSL https://gh.io/copilot-install | bash

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

RUN mkdir -p /opt/cmbox/.copilot && \
    echo '{"include_coauthor":false,"trustedFolders":["/home"],"remoteExport":false}' > /opt/cmbox/.copilot/config.json

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

RUN mkdir -p /opt/cmbox/.claude && \
    echo '{"attribution":{"commit":"","pr":""}}' > /opt/cmbox/.claude/settings.json

USER root

RUN install -d /etc/skel/.copilot /etc/skel/.claude && \
    cp /opt/cmbox/.copilot/config.json /opt/cmbox/.copilot/lsp-config.json \
      /etc/skel/.copilot/ && \
    cp /opt/cmbox/.claude/settings.json /etc/skel/.claude/ && \
    cp /opt/cmbox/.tmux.conf /etc/skel/.tmux.conf && \
    chmod -R a+rwX /opt/cmbox /home/linuxbrew

USER cmbox

ENTRYPOINT ["/usr/local/bin/sandbox-init"]
