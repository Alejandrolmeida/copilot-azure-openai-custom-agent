# 06. Security recommendations

🌐 Language: English | [Español](es/06-security.md)

## Never commit secrets

Do not commit:

- API keys
- `.env`
- personal access tokens
- tenant IDs if sensitive in your organization
- private endpoints
- customer names
- internal project names

The `.gitignore` in this repository excludes `.env` and `.env.*`.

## Prefer secret managers

For local development, you can use:

- Azure Key Vault
- GitHub Codespaces secrets
- OS keychain
- password managers
- environment variables injected by your shell profile

## Azure Key Vault pattern

Store your Azure OpenAI key:

```bash
az keyvault secret set \
  --vault-name YOUR_KEY_VAULT_NAME \
  --name azure-openai-api-key \
  --value YOUR_API_KEY
```

Then configure `.env` without the key:

```bash
AZURE_KEYVAULT_NAME=YOUR_KEY_VAULT_NAME
AZURE_KEYVAULT_SECRET_NAME=azure-openai-api-key
AZURE_SUBSCRIPTION_ID=YOUR_SUBSCRIPTION_ID
```

The wrapper can load the secret at runtime.

For a fully portable setup where endpoint, deployment name, model identity,
token budgets, and the key secret name are all loaded from Key Vault after
`az login`, see
[07. Portable bootstrap with Azure Key Vault](07-portable-keyvault-bootstrap.md).

## Least privilege

- Use separate resources for experimentation.
- Rotate keys regularly.
- Restrict network access when possible.
- Use managed identity or Microsoft Entra ID where your client and service
  support it.
- Monitor token usage and costs.

## Public tutorial checklist

Before publishing a repo:

```bash
grep -R --line-number \
  -E 'sk-|api[_-]?key|secret|tenant|subscription|openai.azure.com' . \
  --exclude-dir=.git \
  --exclude=.env.example
```

Review every match. Placeholder endpoints are fine; real values are not.
