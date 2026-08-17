# Claude Remote Control Service

`claude-rc.service` keeps Claude Code Remote Control running inside the machine
across reboots. The image installs the unit but deliberately leaves it disabled:
a new machine has neither credentials nor a trusted workspace.

## Enable the Service

Run these steps inside the machine:

```bash
# Authenticate with a full-scope login
claude auth login

# Create and trust the workspace
mkdir -p ~/tmp
cd ~/tmp
claude

# Start Remote Control now and on future boots
sudo systemctl enable --now claude-rc

# Follow the service log and find the session URL
journalctl -u claude-rc -f
```

Claude must be run interactively in `/home/user/tmp` once to accept the trust
prompt. Without that step, the service restarts repeatedly with `Workspace not
trusted`.

## Existing Machines

Rebuilding the image does not update an existing machine disk. Copy and install
the unit explicitly:

```bash
machine cp machine/init/claude-rc.service machine:/tmp/claude-rc.service
machine sh '
  sudo install -m 0644 /tmp/claude-rc.service /etc/systemd/system/claude-rc.service &&
  sudo systemctl daemon-reload'
```

Then authenticate, trust the workspace, and enable the service as shown above.

## Operations

```bash
sudo systemctl status claude-rc
sudo systemctl restart claude-rc
journalctl -u claude-rc --since -1h
sudo systemctl disable --now claude-rc
```

The unit intentionally omits systemd sandboxing directives. Remote sessions
need the same permissions as an interactive shell, including passwordless
`sudo`. Logs go to journald rather than an unbounded file.
