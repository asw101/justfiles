# Running the Sandbox Justfile from Anywhere

Use a shell alias so you can run `sandbox <recipe>` from any directory.

Since the Justfile uses `justfile_directory()` to resolve all paths (Dockerfile,
build context, clone target), you only need `--justfile` — no `--working-directory`
is required.

## Setup

Add the following to your `~/.zshrc` (or `~/.bashrc`):

```bash
alias sandbox='just --justfile ~/justfiles/sandbox/Justfile'
```

Then apply:

```bash
source ~/.zshrc
```

## Usage examples

```bash
# From anywhere — build the image
sandbox build

# Run with current directory mounted
sandbox run

# From your project directory — launch with SSH + mount
cd ~/my-cool-project
sandbox run-project .

# Create a persistent named sandbox from your project
cd ~/my-cool-project
sandbox create-named my-sandbox .
sandbox attach my-sandbox

# List containers
sandbox list

# System management
sandbox system-start
sandbox system-stop
```

## How it works

`just --justfile <path>` tells `just` to use a specific Justfile instead of
searching the current directory. The Justfile itself uses `justfile_directory()`
to resolve all paths relative to its own location, so recipes like `build` and
`clone` work correctly regardless of where you invoke them.
