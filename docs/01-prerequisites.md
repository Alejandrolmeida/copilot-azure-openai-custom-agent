# 01. Prerequisites

You need:

- A GitHub account with GitHub Copilot access.
- Visual Studio Code with the GitHub Copilot Chat extension.
- GitHub Copilot CLI if you want terminal agent workflows.
- An Azure subscription with access to Azure OpenAI or Azure AI Foundry.
- A deployed chat model, for example GPT-5, GPT-4.1, GPT-4o, or another compatible model.
- Python 3.10+ for the optional smoke test.
- Azure CLI if you want to load secrets from Azure Key Vault.

## Install GitHub Copilot CLI

Recommended install options:

```bash
# npm
npm install -g @github/copilot

# or Homebrew
brew install copilot-cli
```

Verify:

```bash
copilot --version
copilot --help
```

## Login

For normal GitHub Copilot routing:

```bash
copilot login
```

When using a custom BYOK provider with `COPILOT_PROVIDER_BASE_URL`, GitHub auth may not be required for model access, but GitHub integration features still need authentication.

## Install Azure CLI

```bash
az version
az login
az account set --subscription YOUR_SUBSCRIPTION_ID
```

## Security baseline

Never commit:

- `.env`
- API keys
- Azure subscription IDs if you consider them sensitive
- tenant IDs
- personal access tokens
- private endpoints
- customer names or internal project names
