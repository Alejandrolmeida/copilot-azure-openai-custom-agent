# 04. Configure GitHub Copilot CLI with Azure OpenAI BYOK

GitHub Copilot CLI supports custom model providers through environment variables. For Azure OpenAI / Azure AI Foundry, the important variables are:

```bash
COPILOT_PROVIDER_TYPE=azure
COPILOT_PROVIDER_BASE_URL=https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com
COPILOT_PROVIDER_WIRE_API=responses
COPILOT_PROVIDER_MODEL_ID=gpt-5.5
COPILOT_PROVIDER_WIRE_MODEL=YOUR_DEPLOYMENT_NAME
COPILOT_PROVIDER_MAX_PROMPT_TOKENS=1000000
COPILOT_PROVIDER_MAX_OUTPUT_TOKENS=16384
COPILOT_PROVIDER_API_KEY=YOUR_API_KEY
```

## Why two model names?

```text
COPILOT_PROVIDER_MODEL_ID
```

is the well-known model identity Copilot CLI uses for agent capabilities, prompting strategy, tool support, and token limits.

```text
COPILOT_PROVIDER_WIRE_MODEL
```

is the deployment name sent to Azure.

For example:

```bash
COPILOT_PROVIDER_MODEL_ID=gpt-5.5
COPILOT_PROVIDER_WIRE_MODEL=my-gpt-5-5-deployment
```

## Use the wrapper

Copy and edit `.env`:

```bash
cp examples/.env.example .env
```

Then run:

```bash
./examples/copilot-azure-wrapper.sh --print-config
```

Start an interactive session:

```bash
./examples/copilot-azure-wrapper.sh
```

Run a non-interactive prompt:

```bash
./examples/copilot-azure-wrapper.sh \
  -p "Inspect this repository and suggest three improvements" \
  --allow-all
```

## Endpoint shape

Azure OpenAI v1 endpoint for direct API calls:

```text
https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/
```

Copilot CLI Azure provider base URL:

```text
https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com
```

The wrapper strips `/openai/v1/` automatically.

## Recommended flags

The wrapper launches:

```bash
copilot --model "$COPILOT_MODEL" --context long_context --effort max
```

You can override:

```bash
COPILOT_CONTEXT_TIER=default ./examples/copilot-azure-wrapper.sh
COPILOT_REASONING_EFFORT=high ./examples/copilot-azure-wrapper.sh
```
