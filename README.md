# GitHub Copilot with Azure OpenAI / Azure AI Foundry custom models

Step-by-step community tutorial for using an Azure OpenAI or Azure AI Foundry
model as a custom provider with GitHub Copilot workflows in:

- Visual Studio Code
- GitHub Copilot CLI

The examples use placeholders only. Do **not** commit real endpoints, API keys,
tenant IDs, subscription IDs, or personal data.

## What you will build

You will configure a custom Azure-hosted model deployment, then use it from
GitHub Copilot tooling for agentic coding workflows.

```text
Developer machine
├── VS Code + GitHub Copilot Chat
└── GitHub Copilot CLI
        │
        ▼
Azure OpenAI / Azure AI Foundry deployment
        │
        ▼
Model deployment, for example: gpt-5, gpt-4.1, gpt-4o, etc.
```

## Repository contents

```text
.
├── README.md
├── docs/
│   ├── 01-prerequisites.md
│   ├── 02-create-azure-openai-deployment.md
│   ├── 03-configure-vscode.md
│   ├── 04-configure-copilot-cli.md
│   ├── 05-subagents.md
│   ├── 06-security.md
│   ├── 07-portable-keyvault-bootstrap.md
│   └── troubleshooting.md
├── examples/
│   ├── .env.example
│   ├── .env.keyvault.example
│   ├── copilot-azure-wrapper.sh
│   ├── vscode-settings.example.jsonc
│   └── smoke-test-openai-v1.py
├── scripts/
│   ├── export-current-config-to-keyvault.sh
│   └── install-from-keyvault.sh
├── .gitignore
└── LICENSE
```

## Quick start

1. Create or identify an Azure OpenAI / Azure AI Foundry deployment.
2. Copy the example environment file:

   ```bash
   cp examples/.env.example .env
   ```

3. Fill `.env` locally with your own values. Never commit `.env`.
4. Test the endpoint:

   ```bash
   python examples/smoke-test-openai-v1.py
   ```

5. Use the GitHub Copilot CLI wrapper:

   ```bash
   ./examples/copilot-azure-wrapper.sh --print-config
   ./examples/copilot-azure-wrapper.sh
   ```

## Documentation path

Start here:

1. [Prerequisites](docs/01-prerequisites.md)
2. [Create an Azure OpenAI deployment](docs/02-create-azure-openai-deployment.md)
3. [Configure Visual Studio Code](docs/03-configure-vscode.md)
4. [Configure GitHub Copilot CLI](docs/04-configure-copilot-cli.md)
5. [Configure Copilot CLI subagents](docs/05-subagents.md)
6. [Security recommendations](docs/06-security.md)
7. [Portable Azure Key Vault bootstrap](docs/07-portable-keyvault-bootstrap.md)
8. [Troubleshooting](docs/troubleshooting.md)

## Important security notice

This repository intentionally contains no real credentials. The example files
use placeholder values such as:

```text
https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/
YOUR_DEPLOYMENT_NAME
YOUR_API_KEY
```

Use environment variables, `.env` files ignored by Git, Azure Key Vault,
GitHub Codespaces secrets, or your platform secret manager.

## License

MIT
