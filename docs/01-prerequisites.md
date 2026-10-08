# 01. Prerequisites

English | [Español](es/01-prerequisites.md)

Use Linux or Ubuntu/WSL with Python 3.10+, Azure CLI and Copilot CLI.
The npm installation of Copilot needs Node.js 22+. VS Code runs on Linux or
on Windows connected to the same WSL environment.

```bash
python3 --version
az version
node --version
copilot --version
copilot help providers
copilot --help
```

If a dependency is missing, use its official installer, requesting approval for
administrator operations. Do not use `sudo npm` to bypass a user-prefix problem.
Copilot can be installed with `npm install -g @github/copilot`.
Use `/login` inside Copilot for GitHub features; use `az login` inside WSL for Azure.
Never ask a user to paste passwords or tokens into chat.

```bash
az login --tenant YOUR_TENANT_ID
az account show --query id -o tsv
```

Record and preserve the default subscription. The scripts pass `--subscription`
explicitly; they do not call `az account set`.

## Permissions

| Operation | Needed access |
|---|---|
| Run a profile | Subscription/resource metadata read and Key Vault Secrets User |
| Initialize/update vault configuration | Account key listing when initializing; vault data-plane secret write |
| Create infrastructure | Appropriate resource deployment permissions at approved scopes |
| Create a reader role assignment | Role-assignment permission in addition to resource deployment |
| Create budget alerts | Consumption budget write permission |

Contributor alone does not grant arbitrary role assignment. Do not grant Owner
as a workaround. The Bicep reader assignment is optional and grants no write role.
Temporary write permissions require separate approval and removal by their owner.

## Compatibility

The source installation exercised Copilot CLI 1.0.91 and VS Code 1.140.0.
This is evidence, not a universal version guarantee. `doctor` checks required CLI
flags, account/deployment identity and readiness; it does not certify every feature.
The editor importer checks its internal command before use.

Azure API-key authentication via Key Vault is implemented. If tenant policy
disables local keys, stop: do not enable keys to circumvent policy. Entra-only
client support is not implemented in this revision.

Sources: [CLI installation](https://docs.github.com/en/copilot/get-started/cli-quickstart),
[Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli-linux),
[WSL](https://learn.microsoft.com/windows/wsl/install).
