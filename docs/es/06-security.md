# 06. Seguridad y publicación

[English](../06-security.md) | Español

Guarda fuera del repositorio perfiles reales, IDs de tenant/suscripción, recursos,
endpoints, correos, logs, imports e informes. Los identificadores operativos no
siempre son credenciales, pero son privados según la política del proyecto.
Usa ejemplos sintéticos; no publiques una guía de tu instalación real.

La configuración es JSON validado, nunca `source` ni `eval`. Las claves viajan
en memoria por HTTPS, no en argumentos ni archivos compartidos. El filtrado del
entorno no aísla frente a root ni procesos controlados por el mismo usuario.
No actives trazas, vuelques cuerpos de petición ni subas historiales completos.

El consumidor necesita lectura. Los escritores y operadores de infraestructura
requieren permisos separados y acotados; ninguna herramienta concede Owner
para resolver errores. No debilites políticas del tenant o firewall para una prueba.

VS Code debe crear secretos cifrados propios en cada equipo. No edites ni copies
`state.vscdb`, inventes referencias o sustituyas el servicio core por el
namespace de secretos de una extensión cualquiera.

## Antes de publicar

```bash
python3 scripts/check_public.py
gitleaks dir . --redact --no-banner
gitleaks git . --redact --no-banner
```

El comprobador de privacidad detecta ciertos patrones operativos; Gitleaks,
patrones de credenciales. Ninguno garantiza ausencia absoluta de secretos.
Revisa el diff preparado y el contenido de la release. No uses `git add .`
sin revisión, exportes todas las referencias locales ni uses `git push --mirror`.
Puede haber checkpoints privados aunque sus archivos no tengan seguimiento.

Mantén secret scanning y push protection. CI no debe recibir secretos Azure
ni aprovisionar desde PRs. Si se publica un secreto, revoca/rota primero;
acuerda cualquier reescritura de historia aparte. Borrarlo del último commit
no lo elimina de forks, cachés o commits anteriores.

Consulta [SECURITY.md](../../SECURITY.md) para informar confidencialmente.
