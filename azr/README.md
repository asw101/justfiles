# azr

Create an Azure service principal and store the credentials JSON via the `pw` Justfile (supports 1Password and macOS Keychain).

## Recipes

| Recipe       | Description                                              |
|--------------|----------------------------------------------------------|
| `secret-set` | Create a service principal and store the credentials     |
| `secret-get` | Retrieve the stored SP credentials                       |

## Environment Variables

| Variable          | Default              | Description                              |
|-------------------|----------------------|------------------------------------------|
| `AZR_SECRET_NAME` | `260200-azr-token`   | Secret name for the stored credentials   |
| `PW_SOURCE`       | `keychain`           | Backend: `keychain` or `1password`       |

## Usage

```bash
# Create a service principal and store credentials
azr secret-set

# Retrieve stored credentials
azr secret-get

# Use a custom secret name
azr secret-set "my-custom-name"
azr secret-get "my-custom-name"

# Override via env var
AZR_SECRET_NAME=my-custom-name azr secret-get

# Use 1Password instead of keychain
PW_SOURCE=1password azr secret-get
```
