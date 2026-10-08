# 11. Contrato de perfiles y modelos

[English](../11-multimodel-profiles.md) | Español

Las configuraciones son JSON, nunca scripts. Los validadores canónicos están
en `scripts/foundry.py`; rechazan campos desconocidos, identidades inválidas,
deployments duplicados y límites inconsistentes. Consulta los ejemplos
`examples/profile.example.json` y `examples/config.example.json`.

## Perfil local

Requiere `tenant_id`, `subscription_id`, `vault_name`. Opcionalmente:
`config_secret` y `key_secret`, distintos entre sí. No contiene claves.
Su nombre es un identificador seguro: letras minúsculas, números, guion y guion
bajo, empezando por letra. No está limitado a perfiles numerados.

## Configuración del vault

Requiere `schema_version`, `subscription_id`, `resource_group`, `account_name`,
`endpoint` y mapa `models`. El endpoint es el host HTTPS de la cuenta OpenAI
sin ruta de API. La identidad se contrasta con ARM.

Cada entrada v2 usa el nombre lógico como clave y declara:

| Campo | Significado |
|---|---|
| `deployment` | Nombre exacto enviado a Azure |
| `context_window` | Ventana total |
| `max_prompt_tokens`, `max_output_tokens` | Presupuestos positivos cuya suma no supera la ventana |
| `wire_api` | `responses` o `completions` para CLI |
| `tool_calling`, `vision` | Booleanos revisados por modelo |
| `role` | `primary` seleccionable, o `auxiliary` |
| `source`, `verified_at` | Ficha Microsoft HTTPS y fecha ISO de comprobación |

Un modelo principal necesita herramientas para este lanzador. La metadata no
concede cuota ni cambia las capacidades del servicio. Contrasta la ficha de
Microsoft y la versión/despliegue disponibles; no infieras límites por familia.
Los valores del ejemplo son una instantánea, no máximos universales.

Si se reserva la salida máxima, entrada = contexto menos salida. Cuando la ficha
no publica entrada independiente, nombra ese número **presupuesto derivado**.
TPM/RPM, concurrencia y gasto son restricciones separadas.

Se admite el contrato v1 existente para CLI (deployment y presupuestos de tokens).
El exportador VS Code requiere v2: no inventa capacidades ausentes.
Una actualización explícita del secreto de configuración migra los metadatos
sin cambiar la clave. [Procedimiento](07-portable-keyvault-bootstrap.md).
