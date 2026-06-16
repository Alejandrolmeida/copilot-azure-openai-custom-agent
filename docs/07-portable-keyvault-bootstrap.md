# 07. Portable bootstrap with Azure Key Vault

Use this flow when you want to keep one Azure-hosted custom model
configuration and reuse it from any machine where you can clone this repository
and run `az login`.

The pattern separates:

- a Key Vault secret containing the Azure OpenAI API key
- a Key Vault JSON secret containing non-secret runtime configuration such as
  endpoint, deployment name, token budgets, model identity, context tier, and
  effort level
- a local generated wrapper named `copilot-azurebrains`

No API key is written to the repository or to the generated local config file.

## 1. Prepare Azure CLI access

Install Azure CLI, then authenticate:

```bash
az login
az account set --subscription YOUR_SUBSCRIPTION_ID
```

The signed-in account needs permission to read and write secrets in the target
Key Vault.

## 2. Export from the machine that already works

On the machine where `.env` already contains the working configuration, add the
Key Vault metadata:

```bash
AZURE_KEYVAULT_NAME=YOUR_KEY_VAULT_NAME
AZURE_KEYVAULT_CONFIG_SECRET_NAME=copilot-azure-config
AZURE_KEYVAULT_SECRET_NAME=azure-openai-api-key
AZURE_SUBSCRIPTION_ID=YOUR_SUBSCRIPTION_ID
```

Then run:

```bash
./scripts/export-current-config-to-keyvault.sh
```

The script stores:

- `azure-openai-api-key`: the API key from `AZURE_OPENAI_API_KEY` or
  `COPILOT_PROVIDER_API_KEY`
- `copilot-azure-config`: JSON settings consumed by the wrapper at runtime

The JSON config includes values such as:

```json
{
  "AZURE_OPENAI_BASE_URL": "https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/",
  "AZURE_OPENAI_MODEL": "YOUR_DEPLOYMENT_NAME",
  "AZURE_OPENAI_MAX_COMPLETION_TOKENS": "16384",
  "AZURE_KEYVAULT_SECRET_NAME": "azure-openai-api-key",
  "COPILOT_PROVIDER_MODEL_ID": "gpt-5.5",
  "COPILOT_PROVIDER_WIRE_API": "responses",
  "COPILOT_PROVIDER_MAX_PROMPT_TOKENS": "1000000",
  "COPILOT_PROVIDER_MAX_OUTPUT_TOKENS": "16384",
  "COPILOT_CONTEXT_TIER": "long_context",
  "COPILOT_REASONING_EFFORT": "max"
}
```

## 3. Bootstrap another machine

Clone this repository, authenticate, then provide only the Key Vault locator values:

```bash
az login
export AZURE_KEYVAULT_NAME=YOUR_KEY_VAULT_NAME
export AZURE_KEYVAULT_CONFIG_SECRET_NAME=copilot-azure-config
export AZURE_SUBSCRIPTION_ID=YOUR_SUBSCRIPTION_ID
./scripts/install-from-keyvault.sh
```

Alternatively, copy the example file and fill the same metadata:

```bash
cp examples/.env.keyvault.example .env
./scripts/install-from-keyvault.sh
```

The installer creates:

```text
~/.config/azurebrains/copilot-azurebrains.env
~/.local/bin/copilot-azurebrains
```

Run:

```bash
copilot-azurebrains --print-config
copilot-azurebrains
```

If `~/.local/bin` is not in `PATH`, add it to your shell profile.

## 4. Runtime behavior

Every time you run `copilot-azurebrains`, the repository wrapper:

1. reads `~/.config/azurebrains/copilot-azurebrains.env`
2. loads the JSON config secret from Azure Key Vault
3. loads the API key secret from Azure Key Vault
4. exports the `COPILOT_PROVIDER_*` variables
5. starts GitHub Copilot CLI with the configured model, context tier, and
  effort level

## 5. Rotate or update values

After rotating the Azure OpenAI key or changing the deployment, update the
working `.env` and rerun:

```bash
./scripts/export-current-config-to-keyvault.sh
```

Machines already using `copilot-azurebrains` will pick up the new Key Vault
values the next time they start the wrapper.

## 6. Security notes

- Do not commit `.env` or generated config files.
- Prefer RBAC or access policies with least privilege on the Key Vault.
- Grant users or groups `Key Vault Secrets User` for runtime use.
- Grant `Key Vault Secrets Officer` only to users or automation that must update
  the exported configuration.
- The generated local file contains endpoint and Key Vault metadata, but not the
  API key.
