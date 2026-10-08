# Changelog

## Unreleased — 2.0.0 breaking revision

- Generic validated profiles and model capabilities; retain multimodel v1 CLI compatibility.
- Explicit Bicep planning and creation/reuse; no default subscription changes.
- Secure vault initialization and metadata-only updates without keys in argv.
- Private editor request generation and optional native-secret importer.
- Remove Bash/`.env` bootstrap and automatic global subagent mutation.
- English/Spanish migration, second-PC and operational guidance.
- Offline tests, publication checks, redacted secret scans and reproducible artifacts.

La revisión 2.0 retira el flujo Bash antiguo. Consulta la
[migración](docs/es/08-migration.md). No se migran ni borran automáticamente
configuraciones locales o recursos Azure.
