# Machine-specific layer over either machine's own base image or the sibling
# sandbox image.
ARG BASE_IMAGE=cmbox-sandbox:latest
FROM ${BASE_IMAGE}

USER root

ENV container=container

# `container machine` execs /sbin/init. The selected sandbox base supplies the
# development toolchain; cmbox adds only what is needed to boot as a VM.
RUN apt-get update && \
    apt-get install -y \
      dbus \
      iproute2 \
      iputils-ping \
      net-tools \
      openssh-server \
      systemd \
      systemd-sysv \
      vim-tiny \
      wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN (command -v unminimize >/dev/null && yes | unminimize) || true

RUN mkdir -p /var/lib/dbus && \
    : > /etc/machine-id && \
    : > /var/lib/dbus/machine-id && \
    systemctl set-default multi-user.target && \
    systemctl mask \
      dev-hugepages.mount \
      sys-fs-fuse-connections.mount \
      systemd-update-utmp.service \
      systemd-tmpfiles-setup.service \
      console-getty.service && \
    systemctl disable networkd-dispatcher.service || true

RUN sed -i -e 's/^AcceptEnv LANG LC_\*$/#AcceptEnv LANG LC_*/' /etc/ssh/sshd_config

# The build runtime mounts /etc/resolv.conf read-only, and container machine
# rewrites it during boot. Install and maintain the desired guest resolver.
RUN install -d /usr/local/lib/cmbox && \
    printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\n' \
      > /usr/local/lib/cmbox/resolv.conf && \
    printf '%s\n' \
      '#!/bin/sh' \
      'cmp -s /usr/local/lib/cmbox/resolv.conf /etc/resolv.conf ||' \
      '  cp /usr/local/lib/cmbox/resolv.conf /etc/resolv.conf' \
      > /usr/local/sbin/cmbox-resolv-conf && \
    chmod 755 /usr/local/sbin/cmbox-resolv-conf && \
    printf '%s\n' \
      '[Unit]' \
      'Description=Install cmbox resolver configuration' \
      'After=systemd-resolved.service' \
      '' \
      '[Service]' \
      'Type=oneshot' \
      'ExecStart=/usr/local/sbin/cmbox-resolv-conf' \
      '' \
      '[Install]' \
      'WantedBy=multi-user.target' \
      > /etc/systemd/system/cmbox-resolv-conf.service && \
    printf '%s\n' \
      '[Unit]' \
      'Description=Watch the cmbox resolver configuration' \
      '' \
      '[Path]' \
      'PathChanged=/etc/resolv.conf' \
      'Unit=cmbox-resolv-conf.service' \
      '' \
      '[Install]' \
      'WantedBy=multi-user.target' \
      > /etc/systemd/system/cmbox-resolv-conf.path && \
    printf '%s\n' \
      '[Unit]' \
      'Description=Reapply the cmbox resolver after machine initialization' \
      '' \
      '[Timer]' \
      'OnBootSec=5s' \
      'Unit=cmbox-resolv-conf.service' \
      '' \
      '[Install]' \
      'WantedBy=timers.target' \
      > /etc/systemd/system/cmbox-resolv-conf.timer && \
    systemctl enable \
      cmbox-resolv-conf.service \
      cmbox-resolv-conf.path \
      cmbox-resolv-conf.timer

# Claude Code Remote Control is shipped disabled because a fresh machine has
# neither credentials nor a trusted workspace. See init/README.md.
COPY init/claude-rc.service /etc/systemd/system/claude-rc.service
RUN install -d /usr/lib/systemd/system-preset && \
    printf 'disable claude-rc.service\n' \
      > /usr/lib/systemd/system-preset/50-claude-rc.preset && \
    ! systemctl is-enabled claude-rc.service >/dev/null 2>&1

# Plain sandbox containers use sandbox-init; a machine boots systemd directly.
ENTRYPOINT []
CMD ["/sbin/init"]
