FROM ubuntu:latest

USER root

# Install dependencies for Homebrew and Tailscale
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    file \
    git \
    procps \
    ca-certificates \
    iptables \
    sudo \
    tmux \
    jq \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Tailscale
RUN curl -fsSL https://tailscale.com/install.sh | sh

# Create agent user with sudo access and linuxbrew directory
RUN useradd -m -s /bin/bash agent && \
    echo "agent ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    mkdir -p /home/linuxbrew/.linuxbrew && \
    chown -R agent:agent /home/linuxbrew

# Install Homebrew as agent user
USER agent
ENV HOME=/home/agent
WORKDIR /home/agent

RUN NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add brew to PATH
ENV PATH="/home/agent/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/bin:${PATH}"

# Set a short prompt, add brew to PATH for login shells (Tailscale SSH),
# and auto-attach to tmux on SSH login
RUN echo 'export PATH="/home/agent/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/bin:$PATH"' >> /home/agent/.bashrc && \
    echo "PS1='\\W\\$ '" >> /home/agent/.bashrc && \
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

# Install gh, just, copilot-cli (prerelease), codex, and claude-code
RUN brew install gh just copilot-cli@prerelease codex && \
    brew install --cask claude-code

# Create wrapper scripts
USER root
RUN echo '#!/bin/bash\nexec claude --dangerously-skip-permissions "$@"' > /usr/local/bin/claude-auto && chmod +x /usr/local/bin/claude-auto && \
    echo '#!/bin/bash\nexec codex --full-auto "$@"' > /usr/local/bin/codex-auto && chmod +x /usr/local/bin/codex-auto && \
    echo '#!/bin/bash\nexec copilot --allow-all-tools "$@"' > /usr/local/bin/copilot-auto && chmod +x /usr/local/bin/copilot-auto

USER agent
