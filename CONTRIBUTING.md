# Contributing / Contribuir

Use synthetic fixtures and keep changes scoped. Never include real cloud
identifiers, accounts, keys, `.env`, imports, databases, logs or all-ref Git bundles.
Usa fixtures sintéticos y cambios acotados. No incluyas identificadores reales,
cuentas, claves, imports, bases, logs ni bundles de todas las referencias Git.

```bash
python3 -m unittest discover -s tests -v
npm ci --ignore-scripts
npm test
npm run lint:docs
python3 scripts/check_docs.py
python3 scripts/check_public.py
gitleaks dir . --redact --no-banner
gitleaks git . --redact --no-banner
```

Build `infra/main.bicep` using the pinned Bicep version in CI. Unit/CI checks
must not require Azure credentials or perform inference. Live validation needs
a separately approved test subscription, costs and cleanup plan.
Compila Bicep con la versión fijada en CI. Las pruebas no deben requerir
credenciales Azure ni inferencia; pruebas reales necesitan aprobación separada.

Update English and Spanish guides together; executable code blocks must match.
Review the exact staged diff before committing. Public releases require a clean
approved commit and a second scan of the generated artifacts.
Actualiza ambas lenguas, revisa el diff preparado y escanea también los artefactos.

```bash
python3 scripts/build_release.py
```

For local validation only, `--allow-dirty` produces a non-publishable snapshot.
The client ZIP contains `BUILD_INFO.json` and `SHA256SUMS`; the separate VSIX
is an optional experimental importer. Neither includes Git history or runtime data.
`verify_release.py` runs tests from the archive: use it only on your reviewed
builds. Checksums detect corruption, not a malicious or untrusted publisher.
