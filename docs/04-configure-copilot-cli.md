# 04. CLI profiles and sessions

English | [Español](es/04-configure-copilot-cli.md)

Start with a vault containing the [configuration and API key](07-portable-keyvault-bootstrap.md).
Keep the checkout in a permanent location: installed launchers point to its
script and the local Python interpreter, not to another machine's paths.

```bash
python3 scripts/foundry.py configure work
python3 scripts/foundry.py doctor work
export PATH="$HOME/.local/bin:$PATH"
copilot-foundry work
```

For unattended configuration provide `--subscription`, `--tenant` and `--vault`.
To use custom secret names, edit a private profile JSON and install it directly:

```bash
python3 scripts/foundry.py install "$HOME/.config/my-foundry-input/work.json"
```

The filename stem becomes the profile name. Installation creates
`~/.config/copilot-foundry/work.json`, `copilot-foundry`, `copilot-work` and
`Copilot-work` under `~/.local/bin`. Names such as `foundry1` remain supported.
Conflicting files or symlinks are refused; inspect rather than overwrite.
Persist PATH in the actual user's shell configuration without replacing it.

```bash
copilot-foundry work --model gpt-5-mini
copilot-foundry work --resume
copilot-foundry work --resume=YOUR_SESSION_ID
copilot-foundry work --model gpt-5-mini -- -p "Reply exactly OK."
```

Only configured primary models are selectable. Auxiliary models are not offered.
Without `--model`, a terminal selector asks for a number; `q`, EOF or Ctrl+C cancel.
Without a TTY, `--model` is mandatory. Extra Copilot options go after `--`;
provider/model/protection overrides are rejected there.

The launcher validates tenant, vault and resource, clears inherited alternative
provider credentials, reads the key into memory and protects it from child
tool environments with `--secret-env-vars`. Do not use shell tracing or dump
the environment. A process controlled by the same user/root remains a threat.

For v2 profiles, reasoning effort is not forced: CLI model behavior applies.
Legacy v1 profiles keep their previous default effort for compatibility.
No global subagent settings are modified.
Before starting Copilot, the launcher reads the selected deployment's live
60-second token rate limit from Azure. It reserves at most one quarter of that
TPM for a single request, with up to one quarter of that request budget for
output, and caps the advertised input/output limits accordingly. Missing,
inconsistent or insufficient quota fails before the API key is read.
`--print-config` shows both the configured model limits and the effective
runtime limits. The live cap does not guarantee no 429s: simultaneous
sessions, rapid tool turns, images and other consumers share the deployment.
Respect Retry-After; compact or start a fresh session if the history grows.
For a deliberately large **single** request after a quota increase, use
`copilot-foundry work --model MODEL --full-context`. It fails before reading
the key unless live TPM covers the configured input plus output limits with
at least 12.5% remaining (1,200,000 TPM for 922,000 + 128,000 tokens).
This opts out of the conservative per-request cap; parallel requests, rate
estimation and shared usage can still produce 429, and large contexts cost more.
The flag does not request quota or modify Azure deployments.

## Switching and diagnostics

The current singular-provider launcher fixes endpoint and wire deployment at
startup. `/model` is not a subscription switch. Exit and relaunch another
profile/model with `--resume`. Do not run two processes on the same session.
An ID from another PC is not guaranteed to be present locally.

`doctor` is the shareable high-level check. `--print-config` contains operational
identifiers: keep its output private. `--smoke-test` is explicitly billable and
expects `OK` and usage; it caps output at 1,024 tokens or the lower model limit.
The configured model must support the declared API; there is no automatic fallback.
