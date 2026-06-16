# 05. Configurar subagentes de GitHub Copilot CLI

🌐 Idioma: [English](../05-subagents.md) | Español

GitHub Copilot CLI puede usar subagentes como:

```text
explore
task
general-purpose
code-review
research
```

Los proyectos también pueden definir agentes en:

```text
.github/agents/*.agent.md
```

## ¿Por qué configurar los subagentes por separado?

La sesión principal de Copilot CLI puede usar tu modelo de Azure mientras los
subagentes siguen usando sus modelos predeterminados. Para evitarlo, necesitas
sobrescrituras de subagentes.

Copilot CLI almacena la configuración persistente en:

```text
~/.copilot/settings.json
```

El wrapper de este repositorio actualiza automáticamente ese archivo antes de
lanzar Copilot CLI.

## Ejemplo de configuración de subagentes

```jsonc
{
  "subagents": {
    "agents": {
      "explore": {
        "model": "gpt-5.5",
        "effortLevel": "max",
        "contextTier": "long_context"
      },
      "code-review": {
        "model": "gpt-5.5",
        "effortLevel": "max",
        "contextTier": "long_context"
      }
    }
  }
}
```

## Qué hace el wrapper

`examples/copilot-azure-wrapper.sh` configura:

- subagentes integrados: `explore`, `task`, `general-purpose`, `code-review`,
  `research`
- agentes de proyecto encontrados en `.github/agents/*.agent.md`

con:

```jsonc
{
  "model": "gpt-5.5",
  "effortLevel": "max",
  "contextTier": "long_context"
}
```

## Verificar

Ejecuta:

```bash
jq -r '
  .subagents.agents
  | to_entries[]
  | [.key, .value.model, .value.effortLevel, .value.contextTier]
  | @tsv
' ~/.copilot/settings.json | column -t
```

Dentro de Copilot CLI, usa:

```text
/subagents
```

Deberías ver los subagentes sobrescritos y usando tu identificador de modelo
seleccionado.

## Desactivar la configuración automática de subagentes

```bash
COPILOT_CONFIGURE_SUBAGENTS=false ./examples/copilot-azure-wrapper.sh
```
