# Solución de problemas

[English](../troubleshooting.md) | Español

| Síntoma | Comprobación |
|---|---|
| No aparece el lanzador | Instala localmente y añade `~/.local/bin` al PATH del shell real |
| Error de modelo sin interacción | Pasa `--model`; el selector requiere terminal |
| Conflicto de perfil | Inspecciona/respalda archivo o symlink; no sobrescribas a ciegas |
| Login Azure o 403 | Login WSL, tenant, suscripción y permisos acotados correctos |
| 401 | Cuenta/clave y política de autenticación; nunca imprimas la clave |
| 404 | Deployment exacto, cuenta y API; revisa llamadas auxiliares aparte |
| 429 | RPM/TPM, PCs concurrentes y Retry-After; no aumentes cuota silenciosamente |
| Modelo ausente en editor | Registra un proveedor; variables de terminal no lo registran |
| BYOK desaparece en editor | Destino de sesión Local y rol Agent |
| Importador no disponible | Host/perfil y comando nativo correctos; usa el diálogo seguro |
| What-if rechaza cambios | La herramienta crea/reutiliza; modificar/borrar requiere otra operación revisada |
| Inicialización parcial del vault | Revisa qué secreto existe; no sobrescribas ni rotes automáticamente |
| Sesión antigua no disponible | El historial local/remoto difiere entre PCs; no copies cachés privados |

Usa `doctor` antes de inferencia. Conserva en privado `--print-config`, informes
ARM e imports. Comparte solo códigos y pasos saneados, nunca logs completos.
No resuelvas errores concediendo Owner, activando autenticación prohibida,
usando `--allow-all`, aumentando límites a ciegas o reescribiendo ajustes globales.

Al ejecutar un acceso `copilot-<perfil>`, el lanzador comprueba la identidad y el
acceso a ARM y Key Vault. Si falta la sesión o el token ha caducado o se ha
revocado (por ejemplo, `AADSTS50173`), abre un login por código de dispositivo
para el tenant del perfil y reintenta la validación una vez. Completa el login
y el MFA en el navegador. Los errores de permisos o red no inician un login.
Sin terminal interactiva, muestra el comando de login y termina; `doctor`
conserva su comportamiento de solo lectura. No hace falta ejecutar `az logout`.
