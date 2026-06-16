# 01. Requisitos previos

🌐 Idioma: [English](../01-prerequisites.md) | Español

Necesitas:

- Una cuenta de GitHub con acceso a GitHub Copilot.
- Visual Studio Code con la extensión GitHub Copilot Chat.
- GitHub Copilot CLI si quieres flujos de agentes en terminal.
- Una suscripción de Azure con acceso a Azure OpenAI o Azure AI Foundry.
- Un modelo de chat implementado, por ejemplo GPT-5, GPT-4.1, GPT-4o u otro
  modelo compatible.
- Python 3.10+ para la prueba de humo opcional.
- Azure CLI si quieres cargar secretos desde Azure Key Vault.

## Instalar GitHub Copilot CLI

Opciones de instalación recomendadas:

```bash
# npm
npm install -g @github/copilot

# o Homebrew
brew install copilot-cli
```

Verifica:

```bash
copilot --version
copilot --help
```

## Iniciar sesión

Para el enrutamiento normal de GitHub Copilot:

```bash
copilot login
```

Cuando se usa un proveedor BYOK personalizado con `COPILOT_PROVIDER_BASE_URL`,
es posible que la autenticación de GitHub no sea necesaria para acceder al
modelo, pero las características de integración con GitHub siguen requiriendo
autenticación.

## Instalar Azure CLI

```bash
az version
az login
az account set --subscription YOUR_SUBSCRIPTION_ID
```

## Línea base de seguridad

Nunca confirmes:

- `.env`
- Claves de API
- Identificadores de suscripción de Azure si los consideras sensibles
- Identificadores de tenant
- Tokens de acceso personal
- Endpoints privados
- Nombres de clientes o nombres internos de proyectos
