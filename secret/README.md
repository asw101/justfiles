# secret — Password/Secret Management Justfile

Recipes for storing and retrieving secrets via [1Password CLI](https://developer.1password.com/docs/cli/) or macOS Keychain.

## Environment Variables

| Variable        | Default                | Description                          |
|-----------------|------------------------|--------------------------------------|
| `SECRET_SOURCE` | `1password`            | Backend: `1password` or `keychain`   |
| `SECRET_NAME`   | `github/260200-token`  | Default secret name for get/set      |

## Recipes

| Recipe       | Description                                      |
|--------------|--------------------------------------------------|
| `get`        | Retrieve a secret by name (uses `SECRET_SOURCE`)    |
| `set`        | Store a secret by name (uses `SECRET_SOURCE`)       |

### 1Password CLI

| Recipe       | Description                                      |
|--------------|--------------------------------------------------|
| `op-install` | Install 1Password CLI via Homebrew               |
| `op-verify`  | Check the installed `op` version                 |
| `op-signin`  | Sign in to your 1Password account                |
| `op-test`    | List vaults to confirm everything works          |
| `op-update`  | Update 1Password CLI via Homebrew                |

## Setup

```bash
# Install
secret op-install

# Sign in (first time — will prompt to add account)
secret op-signin

# Verify
secret op-test
```

## Usage

```bash
# Get the default secret (github/260200-token) from 1Password
secret get

# Get a specific secret
secret get "github/260200-token-classic"

# Set the default secret
secret set "ghp_yourTokenHere"

# Set a specific secret
secret set "github/260200-token-classic" "ghp_yourTokenHere"

# Use macOS Keychain instead
SECRET_SOURCE=keychain secret get
SECRET_SOURCE=keychain secret set "ghp_yourTokenHere"
```

## Tips

- If you have the 1Password desktop app, enable CLI integration under
  **Settings → Developer → Integrate with 1Password CLI** for biometric unlock.
- Set `SECRET_SOURCE=keychain` in your shell profile to permanently switch to macOS Keychain.
- Override `SECRET_NAME` to change the default secret name without passing it each time.
