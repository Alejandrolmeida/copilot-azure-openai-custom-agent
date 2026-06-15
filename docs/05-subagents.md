# 05. Configure GitHub Copilot CLI subagents

GitHub Copilot CLI can use subagents such as:

```text
explore
task
general-purpose
code-review
research
```

Projects can also define agents in:

```text
.github/agents/*.agent.md
```

## Why configure subagents separately?

The main Copilot CLI session can use your Azure model while subagents still use their default models. To avoid that, you need subagent overrides.

Copilot CLI stores persistent settings in:

```text
~/.copilot/settings.json
```

The wrapper in this repository automatically updates that file before launching Copilot CLI.

## Example subagent config

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

## What the wrapper does

`examples/copilot-azure-wrapper.sh` configures:

- built-in subagents: `explore`, `task`, `general-purpose`, `code-review`, `research`
- project agents found in `.github/agents/*.agent.md`

with:

```jsonc
{
  "model": "gpt-5.5",
  "effortLevel": "max",
  "contextTier": "long_context"
}
```

## Verify

Run:

```bash
jq -r '
  .subagents.agents
  | to_entries[]
  | [.key, .value.model, .value.effortLevel, .value.contextTier]
  | @tsv
' ~/.copilot/settings.json | column -t
```

Inside Copilot CLI, use:

```text
/subagents
```

You should see the subagents as overridden and using your selected model ID.

## Disable automatic subagent configuration

```bash
COPILOT_CONFIGURE_SUBAGENTS=false ./examples/copilot-azure-wrapper.sh
```
