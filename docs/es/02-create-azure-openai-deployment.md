# 02. Crear una implementación de Azure OpenAI / Azure AI Foundry

🌐 Idioma: [English](../02-create-azure-openai-deployment.md) | Español

Esta guía usa marcadores de posición genéricos. Sustitúyelos por tus propios nombres.

## Opción A: portal de Azure AI Foundry

1. Abre Azure AI Foundry.
2. Crea o selecciona un proyecto.
3. Ve a **Models + endpoints**.
4. Implementa un modelo de chat.
5. Elige un nombre de implementación, por ejemplo:

   ```text
   my-gpt-deployment
   ```

6. Copia el endpoint. Para Azure OpenAI v1 normalmente tiene este aspecto:

   ```text
   https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/
   ```

7. Obtén una clave de API desde el recurso o configura autenticación con
   Microsoft Entra ID si tu cliente lo admite.

## Opción B: ejemplo con Azure CLI

Los comandos exactos de CLI dependen de la disponibilidad del modelo, la región,
la cuota y el tipo de implementación. Úsalo como punto de partida:

```bash
az cognitiveservices account create \
  --name YOUR_AZURE_OPENAI_RESOURCE \
  --resource-group YOUR_RESOURCE_GROUP \
  --location YOUR_REGION \
  --kind OpenAI \
  --sku S0 \
  --custom-domain YOUR_AZURE_OPENAI_RESOURCE
```

Después implementa el modelo desde el portal o con Azure CLI/API compatible para
la familia de tu modelo.

## Recopila estos valores

Necesitarás:

```text
AZURE_OPENAI_BASE_URL=https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/
AZURE_OPENAI_MODEL=YOUR_DEPLOYMENT_NAME
AZURE_OPENAI_API_KEY=YOUR_API_KEY
```

## Prueba de humo

Copia el archivo de entorno de ejemplo:

```bash
cp examples/.env.example .env
```

Edita `.env` y después ejecuta:

```bash
python examples/smoke-test-openai-v1.py
```

Resultado esperado:

```text
OK: request completed
reply: endpoint operational
```
