# Security policy / Política de seguridad

Do not post keys, tokens, private configuration, subscription/tenant IDs,
endpoints, session logs or customer data in issues, pull requests or screenshots.
No publiques claves, tokens, configuración privada, IDs, endpoints, logs ni datos
de clientes en issues, PRs o capturas.

Use the repository's **Security → Report a vulnerability** private channel when
available. If unavailable, open an issue requesting a secure contact **without
technical details or sensitive data**. Never include a secret as evidence.
Utiliza el canal privado **Security → Report a vulnerability** si está habilitado.
Si no lo está, solicita un contacto seguro sin detalles técnicos ni datos privados.

If a credential was exposed, revoke/rotate it promptly and review access.
History cleanup needs owner approval and cannot erase copies already made.
Si se expone una credencial, revócala/rótala y revisa accesos. Limpiar historia
requiere aprobación y no elimina copias ya realizadas.

Security fixes target the current client revision. Internal VS Code commands
and CLI model behavior are version-dependent; unsupported versions must fail
explicitly rather than bypass credential protection.
