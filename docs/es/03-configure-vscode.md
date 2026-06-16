# 03. Configurar Visual Studio Code

🌐 Idioma: [English](../03-configure-vscode.md) | Español

Visual Studio Code y GitHub Copilot pueden seleccionar modelos expuestos por tu
plan de GitHub Copilot y por las políticas de tu organización. La disponibilidad
de modelos personalizados/BYOK en VS Code puede depender de características en
vista previa, políticas empresariales, la versión de la extensión y la forma en
que tu organización registra los modelos personalizados.

Este repositorio proporciona una plantilla segura para configuración de
workspace y variables de entorno de terminal.

## Ejemplo de configuración de workspace

Copia el archivo de ejemplo en tu proyecto o adáptalo manualmente:

```bash
cp examples/vscode-settings.example.jsonc .vscode/settings.json
```

Después sustituye:

```text
YOUR_MODEL_ID_OR_DEPLOYMENT_ALIAS
YOUR-AZURE-OPENAI-RESOURCE
YOUR_DEPLOYMENT_NAME
```

## Configuración de selección de modelo

Los ajustes relevantes de VS Code son:

```jsonc
{
  "github.copilot.selectedCompletionModel": "YOUR_MODEL_ID_OR_DEPLOYMENT_ALIAS",
  "github.copilot.chat.askAgent.model": "YOUR_MODEL_ID_OR_DEPLOYMENT_ALIAS",
  "github.copilot.chat.implementAgent.model": "YOUR_MODEL_ID_OR_DEPLOYMENT_ALIAS",
  "github.copilot.chat.exploreAgent.model": "YOUR_MODEL_ID_OR_DEPLOYMENT_ALIAS",
  "chat.agent.thinkingStyle": "inline"
}
```

## Variables de terminal

Estas variables son útiles para scripts abiertos dentro de terminales de VS Code:

```jsonc
{
  "terminal.integrated.env.linux": {
    "AZURE_OPENAI_BASE_URL": "https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/",
    "AZURE_OPENAI_MODEL": "YOUR_DEPLOYMENT_NAME",
    "AZURE_OPENAI_MAX_COMPLETION_TOKENS": "16384"
  }
}
```

No coloques claves de API en configuraciones de workspace confirmadas. Usa un
`.env` local, configuración de usuario, keychain, Azure Key Vault u otro gestor
de secretos.

## Verificar en VS Code

1. Recarga VS Code: **Developer: Reload Window**.
2. Abre GitHub Copilot Chat.
3. Revisa el selector de modelo o usa la interfaz de selección de modelo.
4. Haz una pregunta sencilla.
5. Si el modelo no aparece, revisa tu plan de Copilot, la política de la
  organización y la versión de la extensión.

## Diferencia importante respecto a Copilot CLI

Copilot CLI tiene variables de entorno BYOK explícitas como
`COPILOT_PROVIDER_BASE_URL`. En VS Code, el registro y la disponibilidad de
modelos pueden estar gestionados por configuración de GitHub Copilot, políticas
de organización o características de la extensión. La configuración de workspace
de este tutorial selecciona un modelo una vez que está disponible en VS Code; no
crea el proveedor de Azure por sí sola.
