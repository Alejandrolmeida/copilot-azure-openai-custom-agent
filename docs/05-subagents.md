# 05. Subagents and auxiliary models

English | [Español](es/05-subagents.md)

These are different surfaces:

- The main session uses the selected profile/model.
- Task/explore/research/review subagents can inherit that BYOK model.
- Internal utilities can request a different deployment on the same account.

Do not rewrite `~/.copilot/settings.json` to force every subagent to a costly
model, maximum reasoning or maximum context. This client does not do that.
`/subagents` shows user preferences, but actual events are the evidence.
The launcher fixes one wire deployment per process; it does not route different
subagents to different Azure deployments. Avoid per-agent model overrides
that name deployments unavailable in the selected profile. When moving to a
second machine, check its user/repository/local subagent preferences and
compare the actual model events before relying on the setup.

To explicitly inherit the selected session model for the built-in agents,
merge this into the user's `~/.copilot/settings.json`, preserving other keys:

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

This overrides preferred models from agent definitions, not an agent's
`modelPolicy: "required"` or an explicit per-call model. Repository and local
settings in `.github/copilot/settings.json` and
`.github/copilot/settings.local.json` take precedence over user settings.
Check those files, the effective `COPILOT_HOME`, and any custom agents on the
second machine before starting a new session. The original machine confirmed
`task` using `gpt-6-sol` after this setting; do not infer that every agent or
profile has been tested from that one run.

## Verify instead of guessing

Run one small, approved subagent task. Inspect only model and outcome fields
in its session events. Do not paste full logs or internal messages.
Compare requested, first-dispatched and completed model identifiers.
The model named in a bundled YAML definition is not proof it was called.

A previous CLI 1.0.91 verification observed primary-model inheritance for
`task`, `explore`, `research` and `code-review`, and primary-model compaction.
New versions and user preferences need new checks.

## Example: an internal classifier

CLI 1.0.91 was observed calling `gpt-5.4-nano` for a message-frustration classifier:
Responses API, `conversation-background`, output budget 2,048.
This was not the task subagent. A missing deployment caused 404 while normal
chat still worked. Creating the exact matching deployment fixed the observed call.

This is a version-specific example, **not a required default for all users**.
Do not provision Nano, older Luna/Mini models or Claude just because they
appear in source definitions. Capture the actual model, wire name and route.
Preserve punctuation in wire deployment names.

Provision only a demonstrated dependency with approval using the Bicep path.
Declare it as `role: "auxiliary"` in v2 metadata; it stays out of the primary
selector and editor export. Metadata alone does not remap a hardcoded CLI call.

Check both RPM and TPM. A minimal deployment can serve one classifier call but
throttle simultaneous sessions or PCs. Retries should respect Azure guidance;
never increase capacity or move to global processing silently.

See [configuration limits](11-multimodel-profiles.md) and
[optional provisioning](02-create-azure-openai-deployment.md).
