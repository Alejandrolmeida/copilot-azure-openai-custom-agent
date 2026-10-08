# 06. Seguridad y publicación

[English](../06-security.md) | Español

Guarda fuera del repositorio perfiles reales, IDs de tenant/suscripción, recursos,
endpoints, correos, logs, imports e informes. Los identificadores operativos no
siempre son credenciales, pero son privados según la política del proyecto.
Usa ejemplos sintéticos; no publiques una guía de tu instalación real.

La configuración es JSON validado, nunca `source` ni `eval`. Las claves viajan
en memoria por HTTPS, no en argumentos ni archivos compartidos. El filtrado del
entorno no aísla frente a root ni procesos controlados por el mismo usuario.
No actives trazas, vuelques cuerpos de petición ni subas historiales completos.

El consumidor necesita lectura. Los escritores y operadores de infraestructura
requieren permisos separados y acotados; ninguna herramienta concede Owner
para resolver errores. No debilites políticas del tenant o firewall para una prueba.

VS Code debe crear secretos cifrados propios en cada equipo. No edites ni copies
`state.vscdb`, inventes referencias o sustituyas el servicio core por el
namespace de secretos de una extensión cualquiera.

## Posición de seguridad del acceso público

Esta es una **evaluación del repositorio, no una certificación de Azure**.
Compara el cliente Python y las plantillas Bicep actuales con las guías locales
*Guia_acceso_publico_Copilot_Azure_OpenAI* (acceso público, P01-P16) e
*Informe_seguridad_Copilot_Azure_OpenAI* (hallazgos históricos H01-H08,
alternativa de red privada, T01-T16). Los Word contienen metadatos y elementos
multimedia y se excluyen expresamente de la publicación. El informe histórico
evaluaba `445a8ca`; esta comparación usa `33d2421`. No se ha auditado una
suscripción real, firewall, sesión de Copilot ni instalación de VS Code.
"Implementado" significa propiedad del código, **no** configuración desplegada
ni ruta de datos acreditada de extremo a extremo.

El diseño público ofrece dos opciones diferenciadas:

| Perfil de red | Azure OpenAI **y** Key Vault | Exposición residual |
|---|---|---|
| `public_selected_ips` (preferido con salida estable) | Endpoints públicos, denegación predeterminada y rangos IPv4 públicos de salida aprobados en cada recurso | Una clave robada aún puede usarse desde una IP permitida; el firewall del vault no restringe el uso de una clave de inferencia ya copiada. |
| `public_any_ip` (solo con aceptación documentada del riesgo) | Endpoints públicos accesibles desde cualquier IP; ambos servicios siguen exigiendo autenticación | Una clave robada puede usarse desde cualquier IP hasta su revocación; priorizar revocación rápida, recursos dedicados y monitorización. |

La plantilla expresa estos perfiles con `allowPublicAccess: false` y
`allowedIPs` no vacío, o con `allowPublicAccess: true`, respectivamente.
Son opciones de red, no de autenticación. El cliente actual usa **identidad
Entra para leer Key Vault** y después una **clave API de Azure OpenAI para
inferencia**. Esta ruta basada en clave requiere `disableLocalAuth: false`.
No atribuye individualmente a Entra las peticiones de inferencia posteriores;
no se debe afirmar que la inferencia ya usa Entra ni desactivar la autenticación
local sin migración probada del cliente. Private Endpoints, DNS privado y
conexión desde red privada constituyen una **arquitectura alternativa** más
restrictiva, no un requisito ni una función de la plantilla Bicep actual.

| Área y hallazgo de la guía | Estado y evidencia | Brecha / cierre |
|---|---|---|
| H01 aprobación de herramientas | **Implementado en documentación/cliente:** no hay `--allow-all` predeterminado; rigen las aprobaciones habituales de Copilot. | **Pendiente:** probar aislamiento del workspace y salida para archivos, shell, MCP y extensiones. El firewall de Azure no gobierna estos flujos. |
| H02 endpoint | **Implementado en código:** `scripts/foundry.py` exige host HTTPS de Azure OpenAI y lo contrasta con el recurso ARM aprobado. | **Sin verificar de extremo a extremo:** probar TLS, redirecciones y destino real de cada función; coincidir con ARM no equivale a política de salida. |
| H03-H05 JSONC, `source`, fallo del vault | **Implementado en código:** el lanzador Python lee JSON, no ejecuta `.env`, no reescribe JSONC de Copilot y se detiene ante configuración inválida o errores/secreto vacío del vault. | **Pendiente:** pruebas negativas de integración con versiones compatibles; las reproducciones del antiguo Bash no prueban una vulnerabilidad actual. |
| H06 precedencia/vida de la clave | **Implementación parcial:** se eliminan determinadas variables heredadas del proveedor, se recupera la clave en cada arranque y no se guarda en argumentos ni archivos compartidos. | **Residual:** Copilot recibe la clave en su entorno. Comprobar ajustes heredados y procesos hijos, rotar el secreto del vault **y** la clave subyacente de Azure OpenAI y probar revocación durante una sesión. |
| H07 proveedor efectivo | **No verificado:** `doctor` valida identidad, endpoint ARM y deployments, pero no lee la clave ni infiere; `--smoke-test` envía una petición pequeña directamente, no a través de Copilot. | **Bloqueante:** comprobar rutas reales de CLI, subagentes, modelos auxiliares y VS Code por versión/perfil, incluso `providers.json` conflictivo, con datos sintéticos. |
| H08 red/observabilidad | **Declarado, no verificado en Azure:** `infra/resources.bicep` declara acceso público con denegación predeterminada y reglas IP para nuevos recursos, RBAC/protección de purga/retención de 90 días en Key Vault; el aprovisionamiento revisa what-if. | **Pendiente:** la plantilla no impone reglas de red/RBAC a recursos reutilizados. Comprobar ambos firewalls y roles reales. No se despliegan diagnósticos ni alertas de seguridad; designar responsable, configurarlos y probarlos. |
| Excepción del vault | **Declarada, no verificada:** los vaults nuevos usan `networkAcls.bypass: 'AzureServices'`. | **Pendiente:** justificar cada excepción de servicios de confianza o reducirla; no permite todos los servicios Azure. Comprobar aparte las reglas de vaults existentes. |
| Datos y puesto | **No evaluable aquí:** no se revisaron tenant, dispositivos, residencia/retención ni inventario de salida. | **Bloqueante:** clasificar datos permitidos, aprobar geografía de procesamiento del deployment/SKU, verificar cifrado/actualización del equipo e inventariar GitHub, extensiones, MCP y herramientas. `.gitignore` no impide leer un archivo local al agente. |
| Límites y respuesta | **Parcial:** se comprueba TPM del deployment al iniciar; los presupuestos opcionales avisan, no bloquean gastos. | **Pendiente:** definir responsable de incidentes, tiempo de revocación, cuotas, entrega de alertas y procedimiento de parada probado antes del uso sostenido. |

**Pruebas de aceptación (perfil público).** Infraestructura registra P01
(el plan no introduce red privada) y la configuración real de *ambos*
servicios; P05 prueba IP denegadas **solo** en `public_selected_ips`,
mientras P06/P07 prueban acceso con clave válida y rechazo sin clave desde
otra IP para `public_any_ip`. El responsable del cliente ejecuta P02
(streaming, herramientas y subagentes), P03 (clave ausente/inválida) y P04
(identidad Entra sin acceso al vault: no obtiene la clave ni infiere; una clave
ya copiada funciona hasta su rotación), P08-P10 (destino/TLS, fallo del vault y configuración
inválida/conflictiva), P12-P13 (regeneración de clave y JSONC intacto) y
P15 (clave señuelo ausente de logs). P11 (renovación de token) corresponde
a un **futuro cliente de inferencia mediante Entra**, no a la ruta actual
basada en clave API. Seguridad/operaciones ejecuta P14 (aislamiento de
archivos y salida de red) y P16 (límite medible/alerta recibida por el
responsable designado). Mantener abiertas además T07 (conflicto de proveedor),
T12 (destino de salida) y T16 (integridad de configuración concurrente) del
informe histórico. Los mocks prueban fallos del código, **no** cloud,
selección del proveedor, streaming, persistencia del editor o revocación.
Usar datos sintéticos; conservar versiones, resultados e identificadores
operativos en un almacén privado de evidencias. No introducir datos internos
o de clientes hasta superar las pruebas aplicables y aceptar el riesgo residual
del perfil público elegido.

Fuentes Microsoft: [reglas de red de Foundry Tools](https://learn.microsoft.com/azure/ai-services/cognitive-services-virtual-networks),
[red de Key Vault](https://learn.microsoft.com/azure/key-vault/general/network-security),
[prácticas de Key Vault](https://learn.microsoft.com/azure/key-vault/general/secure-key-vault#network-security).
La [línea base de Azure OpenAI](https://learn.microsoft.com/security/benchmark/azure/baselines/azure-openai-security-baseline)
también recomienda restricciones de red, mínimo privilegio y logs de recursos,
pero advierte que su versión del benchmark puede contener consejos obsoletos.

## Antes de publicar

```bash
python3 scripts/check_public.py
gitleaks dir . --redact --no-banner
gitleaks git . --redact --no-banner
```

El comprobador de privacidad detecta ciertos patrones operativos; Gitleaks,
patrones de credenciales. Ninguno garantiza ausencia absoluta de secretos.
Revisa el diff preparado y el contenido de la release. No uses `git add .`
sin revisión, exportes todas las referencias locales ni uses `git push --mirror`.
Puede haber checkpoints privados aunque sus archivos no tengan seguimiento.

Mantén secret scanning y push protection. CI no debe recibir secretos Azure
ni aprovisionar desde PRs. Si se publica un secreto, revoca/rota primero;
acuerda cualquier reescritura de historia aparte. Borrarlo del último commit
no lo elimina de forks, cachés o commits anteriores.

Consulta [SECURITY.md](../../SECURITY.md) para informar confidencialmente.
