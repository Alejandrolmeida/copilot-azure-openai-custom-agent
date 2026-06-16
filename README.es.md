# GitHub Copilot con modelos personalizados de Azure OpenAI / Azure AI Foundry

🌐 Idioma: [English](README.md) | Español

Tutorial comunitario paso a paso para usar un modelo de Azure OpenAI o
Azure AI Foundry como proveedor personalizado en flujos de trabajo de
GitHub Copilot en:

- Visual Studio Code
- GitHub Copilot CLI

Los ejemplos usan únicamente marcadores de posición. **No** confirmes endpoints
reales, claves de API, identificadores de tenant, identificadores de
suscripción ni datos personales.

## Qué vas a construir

Configurarás una implementación de modelo personalizada alojada en Azure y
después la usarás desde herramientas de GitHub Copilot para flujos de
codificación agénticos.

```text
Máquina de desarrollo
├── VS Code + GitHub Copilot Chat
└── GitHub Copilot CLI
        │
        ▼
Implementación de Azure OpenAI / Azure AI Foundry
        │
        ▼
Implementación de modelo, por ejemplo: gpt-5, gpt-4.1, gpt-4o, etc.
```

## Contenido del repositorio

```text
.
├── README.md
├── README.es.md
├── docs/
│   ├── 01-prerequisites.md
│   ├── 02-create-azure-openai-deployment.md
│   ├── 03-configure-vscode.md
│   ├── 04-configure-copilot-cli.md
│   ├── 05-subagents.md
│   ├── 06-security.md
│   ├── 07-portable-keyvault-bootstrap.md
│   ├── troubleshooting.md
│   └── es/
│       ├── 01-prerequisites.md
│       ├── 02-create-azure-openai-deployment.md
│       ├── 03-configure-vscode.md
│       ├── 04-configure-copilot-cli.md
│       ├── 05-subagents.md
│       ├── 06-security.md
│       ├── 07-portable-keyvault-bootstrap.md
│       └── troubleshooting.md
├── examples/
│   ├── .env.example
│   ├── .env.keyvault.example
│   ├── copilot-azure-wrapper.sh
│   ├── vscode-settings.example.jsonc
│   └── smoke-test-openai-v1.py
├── scripts/
│   ├── export-current-config-to-keyvault.sh
│   └── install-from-keyvault.sh
├── .gitignore
└── LICENSE
```

## Inicio rápido

1. Crea o identifica una implementación de Azure OpenAI / Azure AI Foundry.
2. Copia el archivo de entorno de ejemplo:

   ```bash
   cp examples/.env.example .env
   ```

3. Rellena `.env` localmente con tus propios valores. Nunca confirmes `.env`.
4. Prueba el endpoint:

   ```bash
   python examples/smoke-test-openai-v1.py
   ```

5. Usa el wrapper de GitHub Copilot CLI:

   ```bash
   ./examples/copilot-azure-wrapper.sh --print-config
   ./examples/copilot-azure-wrapper.sh
   ```

## Ruta de documentación

Empieza aquí:

1. [Requisitos previos](docs/es/01-prerequisites.md)
2. [Crear una implementación de Azure OpenAI](docs/es/02-create-azure-openai-deployment.md)
3. [Configurar Visual Studio Code](docs/es/03-configure-vscode.md)
4. [Configurar GitHub Copilot CLI](docs/es/04-configure-copilot-cli.md)
5. [Configurar subagentes de Copilot CLI](docs/es/05-subagents.md)
6. [Recomendaciones de seguridad](docs/es/06-security.md)
7. [Bootstrap portable con Azure Key Vault](docs/es/07-portable-keyvault-bootstrap.md)
8. [Solución de problemas](docs/es/troubleshooting.md)

## Aviso importante de seguridad

Este repositorio no contiene credenciales reales de forma intencionada. Los
archivos de ejemplo usan valores de marcador de posición como:

```text
https://YOUR-AZURE-OPENAI-RESOURCE.openai.azure.com/openai/v1/
YOUR_DEPLOYMENT_NAME
YOUR_API_KEY
```

Usa variables de entorno, archivos `.env` ignorados por Git, Azure Key Vault,
secretos de GitHub Codespaces o el gestor de secretos de tu plataforma.

## Licencia

MIT
