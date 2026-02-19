# Using tmux to Keep Sessions Alive over Tailscale SSH

When you SSH into the container via Tailscale, your coding agent session will die if the SSH connection drops. This container is pre-configured to make tmux effortless.

## What's Built In

- **Auto-attach on SSH** — tmux starts automatically when you SSH in. If a session already exists, it reattaches. No commands to remember.
- **Easy prefix** — `Ctrl+a` instead of the default `Ctrl+b` (easier to reach)
- **Mouse mode** — click to select panes, scroll with trackpad
- **Status bar hints** — shows keybindings right in the status bar
- **50k line scrollback** — never lose output

## Just SSH In

```bash
tailscale ssh agent@<container-hostname>
```

That's it. You're in tmux automatically.

## Detach (Keep Everything Running)

Press `Ctrl+a` then `d`.

Close your laptop, switch networks, whatever — your agent keeps running.

## Reattach

SSH back in. It reattaches automatically.

```bash
tailscale ssh agent@<container-hostname>
# You're right back where you left off
```

## Cheat Sheet

All commands use `Ctrl+a` as the prefix (shown as `C-a`):

| Action | Keys |
|---|---|
| **Detach** | `C-a d` |
| **New window** | `C-a c` |
| **Next window** | `C-a n` |
| **Previous window** | `C-a p` |
| **Split horizontal** | `C-a "` |
| **Split vertical** | `C-a %` |
| **Switch pane** | `C-a` + arrow key |
| **Scroll up** | trackpad or `C-a [` then arrows |
| **Exit scroll** | `q` |

## Example Workflow

```bash
# SSH in — you're in tmux automatically
tailscale ssh agent@my-sandbox

# You're in window 1. Start Claude:
claude

# Open a second window for a shell: C-a c
# Now you have window 1 (claude) and window 2 (shell)

# Switch between them: C-a n / C-a p

# Done for now? Detach: C-a d
# Agent keeps running. Come back anytime.
```

## Why This Matters

Without tmux, if your SSH drops:
- ❌ Coding agent dies mid-task
- ❌ You lose all output and context
- ❌ Agent has to start over

With tmux:
- ✅ Agent keeps running through disconnects
- ✅ Reattach instantly, pick up where you left off
- ✅ Run multiple agents side by side in different windows
