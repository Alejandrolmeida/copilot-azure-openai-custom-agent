# 11. Profile and model contract

English | [Español](es/11-multimodel-profiles.md)

Configuration is JSON, never executable shell. Canonical validators in
`scripts/foundry.py` reject unknown fields, invalid identities, duplicate
deployments and inconsistent limits. See `examples/profile.example.json`
and `examples/config.example.json`.

## Local profile

Required: `tenant_id`, `subscription_id`, `vault_name`. Optional:
`config_secret` and `key_secret`, which must be distinct. No key values.
The profile name is a safe identifier: lowercase letters, digits, hyphen and
underscore, starting with a letter. Numbered profiles are not required.

## Vault configuration

Required: `schema_version`, `subscription_id`, `resource_group`, `account_name`,
`endpoint` and a `models` map. The endpoint is the account's HTTPS OpenAI host,
without an API path. Identity is checked against ARM.

Each v2 entry is keyed by logical model name and declares:

| Field | Meaning |
|---|---|
| `deployment` | Exact name sent to Azure |
| `context_window` | Total window |
| `max_prompt_tokens`, `max_output_tokens` | Positive budgets whose sum fits the window |
| `wire_api` | CLI `responses` or `completions` |
| `tool_calling`, `vision` | Individually reviewed booleans |
| `role` | Selectable `primary`, or `auxiliary` |
| `source`, `verified_at` | Microsoft HTTPS model card and ISO verification date |

A primary model needs tool calling for this launcher. Metadata does not grant
quota or change service capabilities. Check Microsoft's card and the available
version/deployment; never extrapolate limits from another family member.
Example values are a dated snapshot, not universal maximums.

When reserving maximum output, input = context minus output. If the card does
not publish a separate input maximum, call this a **derived budget**.
TPM/RPM, concurrency and cost remain separate constraints.

The existing v1 contract remains accepted by CLI (deployment and token budgets).
VS Code export requires v2; it does not invent missing capabilities.
An explicit config-secret update migrates metadata without changing the key.
[Procedure](07-portable-keyvault-bootstrap.md).
