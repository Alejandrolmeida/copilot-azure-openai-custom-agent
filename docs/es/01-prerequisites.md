# 01. Requisitos

[English](../01-prerequisites.md) | Español

Utiliza Linux o Ubuntu/WSL con Python 3.10+, Azure CLI y Copilot CLI.
La instalación npm de Copilot requiere Node.js 22+. VS Code se ejecuta en
Linux o en Windows conectado al mismo entorno WSL.

```bash
python3 --version
az version
node --version
copilot --version
copilot help providers
copilot --help
```

Si falta una dependencia, utiliza su instalador oficial y solicita aprobación
para operaciones administrativas. No uses `sudo npm` para evitar un problema
del prefijo de usuario. Copilot se instala con `npm install -g @github/copilot`.
Usa `/login` dentro de Copilot para GitHub y `az login` dentro de WSL para Azure.
Nunca pidas contraseñas o tokens en el chat.

```bash
az login --tenant YOUR_TENANT_ID
az account show --query id -o tsv
```

Anota y conserva la suscripción predeterminada. Los scripts pasan
`--subscription` explícitamente y no ejecutan `az account set`.

## Permisos

| Operación | Acceso necesario |
|---|---|
| Ejecutar un perfil | Lectura de metadatos y Key Vault Secrets User |
| Inicializar/actualizar configuración | Listar claves de cuenta al inicializar; escritura de secretos del vault |
| Crear infraestructura | Permisos de despliegue en los ámbitos aprobados |
| Crear asignación de lector | Permiso de asignación de roles además del de despliegue |
| Crear alertas de presupuesto | Escritura de presupuestos Consumption |

Contributor no concede por sí solo asignación arbitraria de roles. No concedas
Owner como solución rápida. La asignación Bicep de lector es opcional y no
otorga escritura. Los permisos temporales de escritura requieren aprobación
separada y retirada por su propietario.

## Compatibilidad

La instalación de origen utilizó Copilot CLI 1.0.91 y VS Code 1.140.0.
Es evidencia, no una garantía universal de versiones. `doctor` comprueba flags
del CLI, identidad de cuenta/deployment y disponibilidad, no todas las funciones.
El importador del editor verifica el comando interno antes de usarlo.

Está implementada autenticación por API key desde Key Vault. Si el tenant
deshabilita claves locales, detente: no las habilites para eludir esa política.
Esta revisión no implementa un cliente exclusivamente Entra.

Fuentes: [instalación CLI](https://docs.github.com/en/copilot/get-started/cli-quickstart),
[Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli-linux),
[WSL](https://learn.microsoft.com/windows/wsl/install).
