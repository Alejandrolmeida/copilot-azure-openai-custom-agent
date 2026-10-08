# 03. Register VS Code providers securely

English | [Español](es/03-configure-vscode.md)

Terminal environment variables and model-selection workspace settings do not
register editor providers. Use Custom Endpoint groups and the editor's native
credential service. Never put API keys in JSON or copy another PC's SQLite.

Use v2 profiles with reviewed capabilities. Generate a **private, key-free** request:

```bash
python3 scripts/vscode_config.py work --output "$HOME/foundry-editor-import.json"
```

Multiple profile names are accepted. Primary models only are exported.
Each model uses its deployment ID, full Responses URL, declared tool/vision
capabilities and individual input/context/output limits. Automated import is
verified for Responses only; use the editor's secure dialog for other APIs.

## Stable fallback: secure dialog

Create one Custom Endpoint group per account through the editor. Use its
credential field, not chat or a terminal echo, to supply the account key.
Use the generated group's models as metadata; do not copy an `apiKey`
reference from another machine. Preserve unrelated providers.

## Optional experimental importer

The source under `tools/vscode-import/` implements an explicit command, not an
auto-running workspace hook. It checks workspace trust, Linux/WSL host, Azure
identity, vault, endpoint and model metadata before reading a key.

Use the VSIX from a reviewed release. Developers can build a non-publishable
test VSIX with `python3 scripts/build_release.py --allow-dirty`.
Install it in the intended Linux/WSL extension host using **Install from VSIX**.
Run **Foundry: Import Reviewed Profiles (Experimental)** from the command palette.

Choose the generated request and the active profile's `chatLanguageModels.json`.
For Windows stable/default profile it is under `%APPDATA%\Code\User`; from WSL
select its `/mnt/c/...` path. Named profiles, Insiders and portable installs
can differ. Create/open the file through the editor first if it does not exist.

Review the modal confirmation. The importer backs up the JSON privately,
imports groups sequentially and verifies persistence and preservation.
An identical existing group is skipped; a conflicting group stops the import.
After partial failure, inspect the active profile before retrying. No automatic
secret deletion or broad rollback occurs.

It uses `lm.addLanguageModelsProviderGroup`, an **internal, version-dependent**
command. If unavailable, use the secure dialog. `context.secrets.store()` in
an arbitrary extension has a different namespace; it cannot manufacture core
`${input:chat.lm.secret...}` references. Negative IDs are valid.

Uninstall the temporary extension after verification. Its private JSON backup
lives under `~/.local/state/copilot-foundry/vscode/`. Never publish that directory.

## Real validation

Choose session target **Local** and role **Agent**, then the profile-labelled
model. These are separate controls; Agent Host/Copilot sessions may expose a
different model list. Test creation and reading of a **new** file with approved
small inference. Record actual combinations tested; JSON registration alone
is not a successful chat/tool test.
