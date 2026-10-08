# Copilot con tus modelos de Azure OpenAI

Español | [English](README.md)

Cliente comunitario para **GitHub Copilot CLI y VS Code**, con recursos Azure
OpenAI propios, varios perfiles y credenciales en Key Vault.
Reutiliza recursos por defecto. El aprovisionamiento opcional con **Bicep**
requiere un plan revisado y aprobación explícita.

> Esta es la revisión incompatible 2.0 del cliente. Lee la [migración](docs/es/08-migration.md)
> antes de sustituir los wrappers Bash antiguos. La publicación no incluye
> cuentas del mantenedor, credenciales, notas operativas ni historiales.

## Elige tu camino

| Ya tienes… | Empieza aquí |
|---|---|
| Cuenta Azure OpenAI y Key Vault configurados | [Inicio rápido](#inicio-rápido) |
| Azure OpenAI pero no configuración portable | [Bootstrap Key Vault](docs/es/07-portable-keyvault-bootstrap.md) |
| Ningún recurso | [Aprovisionamiento Bicep opcional](docs/es/02-create-azure-openai-deployment.md) |
| Otro PC Windows | [Guía del segundo PC](docs/es/09-second-pc.md) |

## Inicio rápido

Utiliza una copia revisada de esta versión en una ubicación permanente.
Instala Python 3.10+, Azure CLI y Copilot CLI compatible en Linux/WSL.
Autentícate en ese entorno; los inicios de sesión GitHub y Azure son distintos.

```bash
az login
python3 scripts/foundry.py configure work
python3 scripts/foundry.py doctor work
export PATH="$HOME/.local/bin:$PATH"
copilot-foundry work
```

`configure` permite elegir una suscripción y un vault accesibles que ya contenga
el [contrato de configuración](docs/es/11-multimodel-profiles.md).
Valida identidad y endpoint sin cambiar tu suscripción predeterminada.
El lanzador pide el modelo y después lee la API key en memoria.

```bash
copilot-foundry work --model gpt-5-mini
copilot-foundry work --resume
```

El modelo debe existir en **tu** configuración. No se aprovisionan modelos ni
suscripciones automáticamente. `doctor` no lee la API key ni ejecuta inferencia.
Para VS Code sigue la [guía de registro](docs/es/03-configure-vscode.md);
las variables de terminal no registran modelos en el editor.

## Alcance compatible

- Linux y Windows con WSL; VS Code Linux o Windows conectado a WSL.
- Endpoints de **cuentas OpenAI** de Azure público, validados contra ARM.
- CLI Responses o Chat Completions, declarado explícitamente por modelo.
- Automatización experimental del editor: Responses, comando nativo verificado y consentimiento.
- Sin garantía para wrappers Windows nativos, endpoints de proyectos Foundry,
  otros protocolos/proveedores o nubes soberanas en esta revisión.

Los subagentes pueden heredar el modelo BYOK activo; las utilidades internas
pueden solicitar otro deployment. [Diagnostica las llamadas reales](docs/es/05-subagents.md),
no solo el YAML del agente. Contexto, TPM/RPM y dinero son límites distintos.
Los presupuestos envían alertas, no detienen el gasto.

## Guías

1. [Requisitos y permisos](docs/es/01-prerequisites.md)
2. [Infraestructura opcional](docs/es/02-create-azure-openai-deployment.md)
3. [VS Code y credenciales cifradas](docs/es/03-configure-vscode.md)
4. [Perfiles CLI y sesiones](docs/es/04-configure-copilot-cli.md)
5. [Subagentes y modelos auxiliares](docs/es/05-subagents.md)
6. [Seguridad y publicación](docs/es/06-security.md)
7. [Inicialización Key Vault](docs/es/07-portable-keyvault-bootstrap.md)
8. [Migración incompatible](docs/es/08-migration.md)
9. [Segundo PC](docs/es/09-second-pc.md)
10. [Solución de problemas](docs/es/troubleshooting.md)
11. [Contrato de configuración](docs/es/11-multimodel-profiles.md)

El [documento de arquitectura del proyecto (Word)](docs/arquitectura-copilot-azure-openai.docx)
contiene diagramas, decisiones, líneas base y brechas pendientes. Describe el
repositorio y las plantillas, no acredita un entorno Azure real. Las guías Word
externas usadas para el contraste no se publican.

## Desarrollo

```bash
python3 -m unittest discover -s tests -v
npm ci --ignore-scripts
npm test
npm run lint:docs
python3 scripts/check_docs.py
python3 scripts/check_public.py
```

Para regenerar el Word, instala `python-docx` y `Pillow` en un entorno local y
ejecuta `python scripts/generate_architecture_doc.py`. Revisa texto, diagramas,
metadatos y relaciones internas antes de publicarlo.

Consulta [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) y
[CHANGELOG.md](CHANGELOG.md). Los ejemplos son sintéticos. No publiques perfiles
reales, endpoints, IDs de tenant/suscripción, claves, logs ni bases de datos del editor.

Licencia [MIT](LICENSE).
