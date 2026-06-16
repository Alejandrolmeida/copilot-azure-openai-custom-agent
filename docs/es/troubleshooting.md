# Solución de problemas

🌐 Idioma: [English](../troubleshooting.md) | Español

## `ERROR: AZURE_OPENAI_BASE_URL is required`

Crea `.env` desde el ejemplo y rellénalo:

```bash
cp examples/.env.example .env
```

## `HTTP ERROR 401`

Causas probables:

- clave de API incorrecta
- la clave pertenece a otro recurso de Azure OpenAI
- espacios en blanco copiados alrededor de la clave
- uso de un token bearer donde se espera una clave de API

## `HTTP ERROR 404`

Causas probables:

- endpoint incorrecto
- nombre de implementación incorrecto
- la implementación del modelo sigue en aprovisionamiento
- uso de `/openai/v1` donde el cliente espera solo el host del recurso, o al
  revés

Para pruebas de humo directas, usa:

```text
https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/
```

Para `COPILOT_PROVIDER_BASE_URL` de Copilot CLI, usa:

```text
https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com
```

## El modelo responde sin contenido visible

Los modelos con razonamiento pueden gastar presupuesto de salida en tokens de
razonamiento interno. Aumenta:

```bash
AZURE_OPENAI_MAX_COMPLETION_TOKENS=16384
COPILOT_PROVIDER_MAX_OUTPUT_TOKENS=16384
```

## Los subagentes siguen mostrando modelos Claude predeterminados

Reinicia Copilot CLI después de ejecutar el wrapper:

```bash
./examples/copilot-azure-wrapper.sh
```

Después revisa:

```bash
jq '.subagents.agents' ~/.copilot/settings.json
```

Dentro de Copilot CLI, abre:

```text
/subagents
```

## VS Code no muestra mi modelo personalizado

La disponibilidad de modelos en VS Code depende de capacidades de GitHub
Copilot, configuración de la organización, versión de la extensión y registro de
modelos personalizados. La configuración de workspace solo selecciona un modelo
después de que esté disponible en VS Code.

## No se encuentra el comando Copilot CLI

Instala:

```bash
npm install -g @github/copilot
```

Después verifica:

```bash
copilot --version
```
