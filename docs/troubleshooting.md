# Troubleshooting

## `ERROR: AZURE_OPENAI_BASE_URL is required`

Create `.env` from the example and fill it:

```bash
cp examples/.env.example .env
```

## `HTTP ERROR 401`

Likely causes:

- wrong API key
- key belongs to another Azure OpenAI resource
- copied whitespace around the key
- using a bearer token where an API key is expected

## `HTTP ERROR 404`

Likely causes:

- wrong endpoint
- wrong deployment name
- model deployment is still provisioning
- using `/openai/v1` where the client expects only the resource host, or vice versa

For direct smoke tests, use:

```text
https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/
```

For Copilot CLI `COPILOT_PROVIDER_BASE_URL`, use:

```text
https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com
```

## Model replies with no visible content

Reasoning-capable models may spend output budget on internal reasoning tokens. Increase:

```bash
AZURE_OPENAI_MAX_COMPLETION_TOKENS=16384
COPILOT_PROVIDER_MAX_OUTPUT_TOKENS=16384
```

## Subagents still show default Claude models

Restart Copilot CLI after running the wrapper:

```bash
./examples/copilot-azure-wrapper.sh
```

Then check:

```bash
jq '.subagents.agents' ~/.copilot/settings.json
```

Inside Copilot CLI, open:

```text
/subagents
```

## VS Code does not show my custom model

Model availability in VS Code depends on GitHub Copilot capabilities, organization settings, extension version, and custom model registration. The workspace settings select a model only after it is available to VS Code.

## Copilot CLI command not found

Install:

```bash
npm install -g @github/copilot
```

Then verify:

```bash
copilot --version
```
