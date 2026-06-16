# 04. Configurar GitHub Copilot CLI con Azure OpenAI BYOK

🌐 Idioma: [English](../04-configure-copilot-cli.md) | Español

GitHub Copilot CLI admite proveedores de modelos personalizados mediante variables
de entorno. Para Azure OpenAI / Azure AI Foundry, las variables importantes son:

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

## ¿Por qué dos nombres de modelo?

```text
COPILOT_PROVIDER_MODEL_ID
```

es la identidad de modelo conocida que Copilot CLI usa para capacidades de
agente, estrategia de prompts, compatibilidad con herramientas y límites de
tokens.

```text
COPILOT_PROVIDER_WIRE_MODEL
```

es el nombre de implementación que se envía a Azure.

Por ejemplo:

```bash
COPILOT_PROVIDER_MODEL_ID=gpt-5.5
COPILOT_PROVIDER_WIRE_MODEL=my-gpt-5-5-deployment
```

## Usar el wrapper

Copia y edita `.env`:

```bash
cp examples/.env.example .env
```

Después ejecuta:

```bash
./examples/copilot-azure-wrapper.sh --print-config
```

Inicia una sesión interactiva:

```bash
./examples/copilot-azure-wrapper.sh
```

Si quieres usar la misma configuración de modelo en varias máquinas después de
`az login`, usa el flujo portable con Key Vault en
[07. Bootstrap portable con Azure Key Vault](07-portable-keyvault-bootstrap.md).

Ejecuta un prompt no interactivo:

```bash
./examples/copilot-azure-wrapper.sh \
  -p "Inspect this repository and suggest three improvements" \
  --allow-all
```

## Forma del endpoint

Endpoint de Azure OpenAI v1 para llamadas directas a la API:

```text
https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/
```

URL base del proveedor Azure para Copilot CLI:

```text
https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com
```

El wrapper elimina `/openai/v1/` automáticamente.

## Flags recomendados

El wrapper lanza:

```bash
copilot --model "$COPILOT_MODEL" --context long_context --effort max
```

Puedes sobrescribirlo:

```bash
COPILOT_CONTEXT_TIER=default ./examples/copilot-azure-wrapper.sh
COPILOT_REASONING_EFFORT=high ./examples/copilot-azure-wrapper.sh
```
