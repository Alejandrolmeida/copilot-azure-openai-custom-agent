# 03. Configure Visual Studio Code

Visual Studio Code and GitHub Copilot can select models exposed by your GitHub Copilot plan and organization policies. Custom/BYOK model availability in VS Code may depend on preview features, enterprise policy, extension version, and how your organization registers custom models.

This repository provides a safe template for workspace settings and terminal environment variables.

## Example workspace settings

Copy the example file into your project or adapt it manually:

```bash
cp examples/vscode-settings.example.jsonc .vscode/settings.json
```

Then replace:

```text
YOUR_MODEL_ID_OR_DEPLOYMENT_ALIAS
YOUR-AZURE-OPENAI-RESOURCE
YOUR_DEPLOYMENT_NAME
```

## Model selection settings

The relevant VS Code settings are:

```jsonc
{
  "github.copilot.selectedCompletionModel": "YOUR_MODEL_ID_OR_DEPLOYMENT_ALIAS",
  "github.copilot.chat.askAgent.model": "YOUR_MODEL_ID_OR_DEPLOYMENT_ALIAS",
  "github.copilot.chat.implementAgent.model": "YOUR_MODEL_ID_OR_DEPLOYMENT_ALIAS",
  "github.copilot.chat.exploreAgent.model": "YOUR_MODEL_ID_OR_DEPLOYMENT_ALIAS",
  "chat.agent.thinkingStyle": "inline"
}
```

## Terminal variables

These variables are useful for scripts opened inside VS Code terminals:

```jsonc
{
  "terminal.integrated.env.linux": {
    "AZURE_OPENAI_BASE_URL": "https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/",
    "AZURE_OPENAI_MODEL": "YOUR_DEPLOYMENT_NAME",
    "AZURE_OPENAI_MAX_COMPLETION_TOKENS": "16384"
  }
}
```

Do not place API keys in committed workspace settings. Use a local `.env`, user settings, keychain, Azure Key Vault, or another secret manager.

## Verify in VS Code

1. Reload VS Code: **Developer: Reload Window**.
2. Open GitHub Copilot Chat.
3. Check the model picker or use the model selector UI.
4. Ask a simple prompt.
5. If the model does not appear, check your Copilot plan, organization policy, and extension version.

## Important difference from Copilot CLI

The Copilot CLI has explicit BYOK environment variables such as `COPILOT_PROVIDER_BASE_URL`. VS Code model registration and availability may be managed by GitHub Copilot settings, organization policies, or extension features. The workspace settings in this tutorial select a model once it is available to VS Code; they do not create the Azure provider by themselves.
