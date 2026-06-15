# 02. Create an Azure OpenAI / Azure AI Foundry deployment

This guide uses generic placeholders. Replace them with your own names.

## Option A: Azure AI Foundry portal

1. Open Azure AI Foundry.
2. Create or select a project.
3. Go to **Models + endpoints**.
4. Deploy a chat model.
5. Choose a deployment name, for example:

   ```text
   my-gpt-deployment
   ```

6. Copy the endpoint. For Azure OpenAI v1 it usually looks like:

   ```text
   https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/
   ```

7. Get an API key from the resource or configure Microsoft Entra ID authentication if supported by your client.

## Option B: Azure CLI example

The exact CLI commands depend on model availability, region, quota, and deployment type. Treat this as a starting point:

```bash
az cognitiveservices account create \
  --name YOUR_AZURE_OPENAI_RESOURCE \
  --resource-group YOUR_RESOURCE_GROUP \
  --location YOUR_REGION \
  --kind OpenAI \
  --sku S0 \
  --custom-domain YOUR_AZURE_OPENAI_RESOURCE
```

Then deploy your model from the portal or with the supported Azure CLI/API for your model family.

## Collect these values

You will need:

```text
AZURE_OPENAI_BASE_URL=https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/
AZURE_OPENAI_MODEL=YOUR_DEPLOYMENT_NAME
AZURE_OPENAI_API_KEY=YOUR_API_KEY
```

## Smoke test

Copy the example env file:

```bash
cp examples/.env.example .env
```

Edit `.env`, then run:

```bash
python examples/smoke-test-openai-v1.py
```

Expected result:

```text
OK: request completed
reply: endpoint operational
```
