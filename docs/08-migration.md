# 08. Breaking migration from the Bash tutorial

English | [Español](es/08-migration.md)

Version 2.0 removes the old Bash wrapper, exporter, installer and `.env` workflow.
The older `copilot-azurebrains` entry point is not installed or maintained.
Existing local launchers are not deleted automatically: inspect them before removal.

1. Back up local configuration privately; record the old vault/account identity.
2. Read old configuration as data. **Do not source it.** Reject shell substitutions.
3. Create a private profile from `examples/profile.example.json`.
4. Map endpoint, logical model, deployment and budgets into the v2 example.
   Add reviewed API, capabilities, role, source and date.
5. Initialize distinct vault secrets, or explicitly update only metadata on
   the same account. [Procedure](07-portable-keyvault-bootstrap.md).
6. Install and run `doctor`, then an approved small smoke test.
7. Register editor providers separately; no secret database migration.

The old `copilot-azure-config` JSON is not the multimodel contract. Do not rename
it and assume compatibility. Custom secret names are supported in a profile,
but their contents must follow the new contract.

New client behavior: no global subscription changes, no automatic subagent
overrides, no `--allow-all` default, no forced maximum effort/context.
Existing v1 multimodel profiles remain valid for CLI; v2 is required for
automatic editor capability export. User settings are never reset silently.
