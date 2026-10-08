# Copilot with your Azure OpenAI models

[Español](README.es.md) | English

A community client for **GitHub Copilot CLI and VS Code**, using your own
Azure OpenAI resources, multiple profiles and Key Vault credentials.
Use existing resources by default. Optional **Bicep** provisioning requires
a reviewed plan and explicit approval.

> This is the breaking 2.0 client revision. Read the [migration guide](docs/08-migration.md)
> before replacing the old Bash wrappers. Publication does not include any
> maintainer accounts, credentials, operational notes or session history.

## Choose your path

| You have… | Start here |
|---|---|
| A configured Azure OpenAI account and Key Vault | [Client quick start](#client-quick-start) |
| Azure OpenAI but no portable configuration | [Key Vault bootstrap](docs/07-portable-keyvault-bootstrap.md) |
| No resources yet | [Optional Bicep provisioning](docs/02-create-azure-openai-deployment.md) |
| Another Windows PC | [Second-PC guide](docs/09-second-pc.md) |

## Client quick start

Use a reviewed checkout of this version in a permanent directory.
Install Python 3.10+, Azure CLI and a compatible Copilot CLI in Linux/WSL.
Authenticate in that environment; GitHub and Azure logins are separate.

```bash
az login
python3 scripts/foundry.py configure work
python3 scripts/foundry.py doctor work
export PATH="$HOME/.local/bin:$PATH"
copilot-foundry work
```

`configure` lets you select an accessible subscription and vault that already
contains the [configuration contract](docs/11-multimodel-profiles.md).
It validates identity and endpoint without changing your default subscription.
The launcher asks for a model, then reads the API key into memory.

```bash
copilot-foundry work --model gpt-5-mini
copilot-foundry work --resume
```

The model must exist in **your** configuration. No models or subscriptions are
automatically provisioned. `doctor` does not read the API key or run inference.
For VS Code, follow the [provider registration guide](docs/03-configure-vscode.md);
terminal variables do not register editor models.

## Support boundary

- Linux and Windows with WSL; VS Code Linux or Windows connected to WSL.
- Azure public-cloud **OpenAI account endpoints**, validated against ARM.
- CLI Responses or Chat Completions as explicitly declared per model.
- Experimental editor automation: Responses, checked native command, explicit consent.
- No guarantee for native Windows CLI wrappers, Foundry project endpoints,
  other provider protocols or sovereign clouds in this revision.

Subagents may inherit the active BYOK model; auxiliary CLI functions can request
another deployment. [Diagnose actual calls](docs/05-subagents.md), not just agent YAML.
Context limits, TPM/RPM and money are separate. Budgets send alerts, not hard stops.

## Guides

1. [Prerequisites and permissions](docs/01-prerequisites.md)
2. [Optional infrastructure](docs/02-create-azure-openai-deployment.md)
3. [VS Code and encrypted credentials](docs/03-configure-vscode.md)
4. [CLI profiles and sessions](docs/04-configure-copilot-cli.md)
5. [Subagents and auxiliary models](docs/05-subagents.md)
6. [Security and publication](docs/06-security.md)
7. [Key Vault initialization](docs/07-portable-keyvault-bootstrap.md)
8. [Breaking migration](docs/08-migration.md)
9. [Second PC](docs/09-second-pc.md)
10. [Troubleshooting](docs/troubleshooting.md)
11. [Configuration contract](docs/11-multimodel-profiles.md)

## Development

```bash
python3 -m unittest discover -s tests -v
npm ci --ignore-scripts
npm test
npm run lint:docs
python3 scripts/check_docs.py
python3 scripts/check_public.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) and
[CHANGELOG.md](CHANGELOG.md). Public examples are synthetic. Never commit
real profiles, endpoints, tenant/subscription IDs, keys, logs or editor databases.

Licensed under [MIT](LICENSE).
