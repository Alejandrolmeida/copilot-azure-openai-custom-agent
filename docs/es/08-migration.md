# 08. Migración incompatible desde el tutorial Bash

[English](../08-migration.md) | Español

La versión 2.0 retira wrapper, exportador, instalador Bash y flujo `.env`.
Ya no se instala ni mantiene `copilot-azurebrains`. Los accesos locales
existentes no se borran automáticamente: inspecciónalos antes de retirarlos.

1. Respalda en privado la configuración y anota identidad de vault/cuenta.
2. Lee la configuración como datos. **No la ejecutes con source.** Rechaza sustituciones shell.
3. Crea un perfil privado desde `examples/profile.example.json`.
4. Traslada endpoint, modelo lógico, deployment y presupuestos al ejemplo v2;
   añade API, capacidades, rol, fuente y fecha revisados.
5. Inicializa secretos distintos o actualiza explícitamente solo metadatos
   de la misma cuenta. [Procedimiento](07-portable-keyvault-bootstrap.md).
6. Instala, ejecuta `doctor` y después una prueba breve aprobada.
7. Registra proveedores del editor aparte; no migres la base de secretos.

El antiguo JSON `copilot-azure-config` no es el contrato multimodelo.
Renombrarlo no lo convierte. El perfil permite nombres de secretos personalizados,
pero el contenido debe cumplir el nuevo contrato.

Nuevo comportamiento: sin cambio global de suscripción, overrides automáticos
de subagentes, `--allow-all` predeterminado ni esfuerzo/contexto máximos forzados.
Los perfiles multimodelo v1 siguen funcionando en CLI; se requiere v2 para
exportar capacidades del editor. No se reinician ajustes del usuario silenciosamente.
