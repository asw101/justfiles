# pw — 1Password CLI Justfile

Recipes for installing, configuring, and using the [1Password CLI](https://developer.1password.com/docs/cli/) (`op`).

## Recipes

| Recipe    | Description                                      |
|-----------|--------------------------------------------------|
| `install` | Install 1Password CLI via Homebrew               |
| `verify`  | Check the installed `op` version                 |
| `signin`  | Sign in to your 1Password account                |
| `test`    | List vaults to confirm everything works          |
| `update`  | Update 1Password CLI via Homebrew                |
| `token`   | Retrieve the `github/260200-token` from 1Password |
| `token-classic` | Retrieve the `github/260200-token-classic` from 1Password |
| `kc-token` | Retrieve the `github/260200-token` from macOS Keychain |
| `kc-token-set` | Store the `github/260200-token` in macOS Keychain |
| `kc-token-classic` | Retrieve the `github/260200-token-classic` from macOS Keychain |
| `kc-token-classic-set` | Store the `github/260200-token-classic` in macOS Keychain |

## Setup

```bash
# Install
pw install

# Sign in (first time — will prompt to add account)
pw signin

# Verify
pw test
```

## Tips

- If you have the 1Password desktop app, enable CLI integration under
  **Settings → Developer → Integrate with 1Password CLI** for biometric unlock.
- Run `pw token` to fetch a GitHub token stored in your Private vault.

## macOS Keychain

As an alternative to 1Password, you can store and retrieve tokens using the macOS Keychain:

```bash
# Store a token (will create or update)
pw kc-token-set ghp_yourTokenHere

# Retrieve it
pw kc-token
```
