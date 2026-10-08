# Troubleshooting

English | [Español](es/troubleshooting.md)

| Symptom | Check |
|---|---|
| Launcher not found | Install locally and add `~/.local/bin` to the actual shell's PATH |
| Noninteractive model error | Pass `--model`; the selector requires a terminal |
| Profile conflict | Inspect/backup the file or symlink; never overwrite blindly |
| Azure login or 403 | Correct WSL login, tenant, subscription and scoped permissions |
| 401 | Correct account/key and supported authentication policy; never print the key |
| 404 | Exact deployment name, account and API route; inspect auxiliary calls separately |
| 429 | RPM and TPM, concurrent PCs, Retry-After; no silent quota increase |
| Model absent in editor | Register a provider; terminal variables do not register it |
| BYOK disappears in editor | Select Local session target and Agent role |
| Importer unavailable | Correct host/profile and native command; use the secure dialog fallback |
| What-if refuses update | This tool creates/reuses; modifying/deleting resources requires a separate reviewed operation |
| Partial vault initialization | Inspect which secret exists; do not overwrite or rotate automatically |
| Old session unavailable | Remote/local history differs between PCs; do not copy private caches |

Use `doctor` before inference. Keep `--print-config`, ARM reports and imports
private. Share only sanitized error codes and steps, never complete logs.
Do not solve errors by granting Owner, enabling blocked authentication, using
`--allow-all`, increasing token limits blindly or rewriting global settings.

When running a `copilot-<profile>` shortcut, the launcher checks identity and
access to ARM and Key Vault. If the session is missing or the token has expired
or been revoked (for example, `AADSTS50173`), it starts device-code login for
the profile tenant and retries validation once. Complete login and MFA in the
browser. Permission and network errors do not start login. Without an
interactive terminal, it prints the login command and exits; `doctor` remains
read-only. Running `az logout` is not required.
