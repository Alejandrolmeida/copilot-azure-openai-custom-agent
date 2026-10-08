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

## Foundry6: temporary public IP test

This opt-in test changes **Azure OpenAI account-wide** network ACLs, not Key
Vault or a single deployment. The operator must have Entra ID access to read
the vault and permission to update the OpenAI account. A valid Entra session
is checked before each update; Copilot still uses the vault's API key for
inference. Do not use this as proof of Entra-based inference authentication.

Prepare once from the repository checkout (requires an existing `Allow` ACL
without IP or virtual network rules):

```bash
python3 scripts/foundry.py access foundry6 prepare
Copilot-foundry6
python3 scripts/foundry.py access foundry6 close
```

`prepare` blocks all public IPs on the Foundry6 account until a temporary
session starts. The **Foundry6-only** shortcut must pass
`--temporary-ip-access` to `scripts/foundry.py run foundry6`. The launcher
prompts for the current **public IPv4 egress address**; check it independently
before entering it (VPNs/proxies may change egress). It validates the address
format but does not discover or transmit it to an IP-lookup service. It allows
that IP only while the Copilot child process runs, then removes the rule on
exit. For a billable inference check instead, run
`python3 scripts/foundry.py run foundry6 --temporary-ip-access --model MODEL --smoke-test`.
`close` restores `Allow` with zero rules **only after all sessions have ended**.

If a machine crashes or connectivity is lost, cleanup cannot be guaranteed:
there is no Azure-side expiry. From an authorized session, run
`python3 scripts/foundry.py access foundry6 revoke` to remove the single
temporary IP rule, confirm it has been removed, and then `close` when done.
Never run `revoke` while another Foundry6 session is using the rule; unexpected
ACLs or concurrent changes are refused, not overwritten. An IP allowlist is
not user authentication: anyone at the allowed egress with a valid API key
can reach this account. Validate denial from a separate egress network before
asserting that the network restriction works end-to-end.

## Switching and diagnostics

The current singular-provider launcher fixes endpoint and wire deployment at
startup. `/model` is not a subscription switch. Exit and relaunch another
profile/model with `--resume`. Do not run two processes on the same session.
An ID from another PC is not guaranteed to be present locally.

`doctor` is the shareable high-level check. `--print-config` contains operational
identifiers: keep its output private. `--smoke-test` is explicitly billable and
expects `OK` and usage; it caps output at 1,024 tokens or the lower model limit.
The configured model must support the declared API; there is no automatic fallback.
