# azr

Create an Azure service principal and stash the credentials JSON in macOS Keychain.

## Recipes

| Recipe | Description |
|---|---|
| `token-set` | Create a service principal and store the blob in the keychain |
| `token-get` | Retrieve the stored credentials from the keychain |

## Usage

```bash
just token-set
just token-get
```

## Configuration

| Env var | Default | Description |
|---|---|---|
| `AZR_TOKEN_NAME` | `260200-azr-token` | Keychain item name for the stored credentials |

Override the keychain item name:

```bash
AZR_TOKEN_NAME=my-custom-name just token-set
```
