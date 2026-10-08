# 05. Subagentes y modelos auxiliares

[English](../05-subagents.md) | Español

Son superficies diferentes:

- La sesión principal usa el perfil/modelo seleccionado.
- Los subagentes task/explore/research/review pueden heredar ese modelo BYOK.
- Las utilidades internas pueden solicitar otro deployment de la misma cuenta.

No reescribas `~/.copilot/settings.json` para forzar todos los subagentes a un
modelo caro, máximo razonamiento o máximo contexto. Este cliente no lo hace.
`/subagents` muestra preferencias, pero los eventos reales son la evidencia.
El lanzador fija un deployment real por proceso: no enruta distintos
subagentes a distintos deployments Azure. Evita overrides por agente que
pidan modelos no disponibles en el perfil elegido. Al configurar otro
equipo, revisa sus preferencias de subagentes de usuario/repositorio/locales
y compara los modelos en los eventos antes de darlo por equivalente.

Para heredar explicitamente el modelo de la sesion en los agentes integrados,
integra esto en `~/.copilot/settings.json` conservando las demas claves:

```json
{
  "subagents": {
    "agents": {
      "task": {"model": "inherit"},
      "explore": {"model": "inherit"},
      "research": {"model": "inherit"},
      "code-review": {"model": "inherit"},
      "general-purpose": {"model": "inherit"},
      "security-review": {"model": "inherit"}
    }
  }
}
```

Esto prevalece sobre modelos preferidos en definiciones de agente, pero no
sobre `modelPolicy: "required"` ni un modelo explicito al delegar. Los ajustes
de repositorio y locales en `.github/copilot/settings.json` y
`.github/copilot/settings.local.json` prevalecen sobre los del usuario.
Comprueba esos archivos, el `COPILOT_HOME` efectivo y los agentes
personalizados del segundo equipo antes de iniciar una sesion nueva. En el
equipo original se confirmo `task` con `gpt-6-sol` tras este ajuste; esa prueba
no confirma todos los agentes o perfiles.

## Verificar, no adivinar

Ejecuta una tarea pequeña de subagente, con aprobación. Inspecciona solo los
campos de modelo y resultado de sus eventos. No pegues logs completos ni
mensajes internos. Compara modelo solicitado, primero ejecutado y completado.
Un nombre de modelo en un YAML no demuestra que se haya llamado.

Una verificación anterior de CLI 1.0.91 observó herencia del principal en
`task`, `explore`, `research` y `code-review`, y compactación con el principal.
Otras versiones y preferencias requieren comprobación nueva.

## Ejemplo: clasificador interno

Se observó que CLI 1.0.91 llamaba a `gpt-5.4-nano` para clasificar frustración
de mensajes: API Responses, `conversation-background`, salida limitada a 2.048.
No era el subagente task. La ausencia del deployment provocaba 404 mientras
el chat normal funcionaba. Crear el deployment exacto corrigió esa llamada.

Es un ejemplo ligado a una versión, **no un requisito para todos los usuarios**.
No despliegues Nano, modelos Luna/Mini antiguos ni Claude solo porque aparezcan
en definiciones. Obtén evidencia del modelo, nombre enviado y ruta reales.
Conserva la puntuación en los nombres de deployment.

Aprovisiona solo una dependencia demostrada y aprobada mediante Bicep.
Declárala con `role: "auxiliary"` en v2; no aparecerá en el selector principal
ni en el export del editor. Los metadatos por sí solos no redirigen una llamada
codificada internamente en el CLI.

Comprueba RPM y TPM. Un deployment mínimo puede servir una clasificación pero
limitar sesiones o PCs simultáneos. Respeta las indicaciones de reintento de Azure;
no aumentes cuota ni cambies a procesamiento global silenciosamente.

Consulta [límites del contrato](11-multimodel-profiles.md) y
[aprovisionamiento opcional](02-create-azure-openai-deployment.md).
