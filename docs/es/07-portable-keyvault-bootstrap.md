# 07. Bootstrap portable con Azure Key Vault

🌐 Idioma: [English](../07-portable-keyvault-bootstrap.md) | Español

Usa este flujo cuando quieras mantener una configuración de modelo personalizado
alojado en Azure y reutilizarla desde cualquier máquina donde puedas clonar este
repositorio y ejecutar `az login`.

El patrón separa:

- un secreto de Key Vault que contiene la clave de API de Azure OpenAI
- un secreto JSON de Key Vault que contiene configuración de ejecución no
  secreta, como endpoint, nombre de implementación, presupuestos de tokens,
  identidad de modelo, nivel de contexto y nivel de esfuerzo
- un wrapper local generado llamado `copilot-azurebrains`

No se escribe ninguna clave de API en el repositorio ni en el archivo de
configuración local generado.

## 1. Preparar el acceso de Azure CLI

Instala Azure CLI y después autentícate:

```bash
az login
az account set --subscription YOUR_SUBSCRIPTION_ID
```

La cuenta autenticada necesita permisos para leer y escribir secretos en el Key
Vault de destino.

## 2. Exportar desde la máquina que ya funciona

En la máquina donde `.env` ya contiene la configuración funcional, añade los
metadatos de Key Vault:

```bash
AZURE_KEYVAULT_NAME=YOUR_KEY_VAULT_NAME
AZURE_KEYVAULT_CONFIG_SECRET_NAME=copilot-azure-config
AZURE_KEYVAULT_SECRET_NAME=azure-openai-api-key
AZURE_SUBSCRIPTION_ID=YOUR_SUBSCRIPTION_ID
```

Después ejecuta:

```bash
./scripts/export-current-config-to-keyvault.sh
```

El script almacena:

- `azure-openai-api-key`: la clave de API de `AZURE_OPENAI_API_KEY` o
  `COPILOT_PROVIDER_API_KEY`
- `copilot-azure-config`: configuración JSON consumida por el wrapper en tiempo
  de ejecución

La configuración JSON incluye valores como:

```json
{
  "AZURE_OPENAI_BASE_URL": "https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/",
  "AZURE_OPENAI_MODEL": "YOUR_DEPLOYMENT_NAME",
  "AZURE_OPENAI_MAX_COMPLETION_TOKENS": "16384",
  "AZURE_KEYVAULT_SECRET_NAME": "azure-openai-api-key",
  "COPILOT_PROVIDER_MODEL_ID": "gpt-5.5",
  "COPILOT_PROVIDER_WIRE_API": "responses",
  "COPILOT_PROVIDER_MAX_PROMPT_TOKENS": "1000000",
  "COPILOT_PROVIDER_MAX_OUTPUT_TOKENS": "16384",
  "COPILOT_CONTEXT_TIER": "long_context",
  "COPILOT_REASONING_EFFORT": "max"
}
```

## 3. Inicializar otra máquina

Clona este repositorio, autentícate y proporciona únicamente los valores
localizadores de Key Vault:

```bash
az login
export AZURE_KEYVAULT_NAME=YOUR_KEY_VAULT_NAME
export AZURE_KEYVAULT_CONFIG_SECRET_NAME=copilot-azure-config
export AZURE_SUBSCRIPTION_ID=YOUR_SUBSCRIPTION_ID
./scripts/install-from-keyvault.sh
```

Como alternativa, copia el archivo de ejemplo y rellena los mismos metadatos:

```bash
cp examples/.env.keyvault.example .env
./scripts/install-from-keyvault.sh
```

El instalador crea:

```text
~/.config/azurebrains/copilot-azurebrains.env
~/.local/bin/copilot-azurebrains
```

Ejecuta:

```bash
copilot-azurebrains --print-config
copilot-azurebrains
```

Si `~/.local/bin` no está en `PATH`, añádelo a tu perfil de shell.

## 4. Comportamiento en tiempo de ejecución

Cada vez que ejecutas `copilot-azurebrains`, el wrapper del repositorio:

1. lee `~/.config/azurebrains/copilot-azurebrains.env`
2. carga el secreto JSON de configuración desde Azure Key Vault
3. carga el secreto de la clave de API desde Azure Key Vault
4. exporta las variables `COPILOT_PROVIDER_*`
5. inicia GitHub Copilot CLI con el modelo, el nivel de contexto y el nivel de
   esfuerzo configurados

## 5. Rotar o actualizar valores

Después de rotar la clave de Azure OpenAI o cambiar la implementación, actualiza
el `.env` funcional y vuelve a ejecutar:

```bash
./scripts/export-current-config-to-keyvault.sh
```

Las máquinas que ya usan `copilot-azurebrains` recogerán los nuevos valores de
Key Vault la próxima vez que inicien el wrapper.

## 6. Notas de seguridad

- No confirmes `.env` ni archivos de configuración generados.
- Prefiere RBAC o directivas de acceso con privilegio mínimo en Key Vault.
- Concede `Key Vault Secrets User` a usuarios o grupos para uso en ejecución.
- Concede `Key Vault Secrets Officer` solo a usuarios o automatizaciones que
  deban actualizar la configuración exportada.
- El archivo local generado contiene endpoint y metadatos de Key Vault, pero no
  la clave de API.
