# 07. Key Vault initialization and metadata updates

English | [Español](es/07-portable-keyvault-bootstrap.md)

Copy the synthetic profile/config examples into a private directory outside
the repository. Replace identities and validate every model's published limits
and actual deployment. Never add a key to either JSON.

```bash
mkdir -p "$HOME/.config/my-foundry-input"
chmod 700 "$HOME/.config/my-foundry-input"
cp examples/profile.example.json "$HOME/.config/my-foundry-input/work.json"
cp examples/config.example.json "$HOME/.config/my-foundry-input/config.json"
```

Edit the copies. The vault and account must exist. Provisioning permissions do
not automatically grant data-plane secret writes. Have the owner approve the
minimal required role; this tool does not grant or remove roles.

```bash
python3 scripts/seed_vault.py "$HOME/.config/my-foundry-input/work.json" "$HOME/.config/my-foundry-input/config.json" --confirm-write
python3 scripts/foundry.py install "$HOME/.config/my-foundry-input/work.json"
python3 scripts/foundry.py doctor work
```

Initialization refuses existing target secrets. It reads the account key into
memory and writes via HTTPS to Key Vault, never in process arguments. There is
no rotation. If writing the second secret fails, inspect the partial state:
do not blindly overwrite or delete the key. Key Vault versions provide recovery.

For a reviewed **metadata-only** update on the same account:

```bash
python3 scripts/seed_vault.py "$HOME/.config/my-foundry-input/work.json" "$HOME/.config/my-foundry-input/config.json" --update-config-only --confirm-write
```

This preserves the key and refuses redirecting its configuration to another
account. Review the JSON diff before confirming. Remove temporary write access
after the operation; normal clients only need secret read and metadata access.

A second PC logs in independently and installs only the non-secret profile.
Secrets are fetched at startup. Do not copy Azure token caches or VS Code's
credential database. Secret names default to `copilot-foundry-config` and
`azure-openai-api-key`; profiles may override them with distinct names.
