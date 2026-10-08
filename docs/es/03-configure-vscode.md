# 03. Registrar proveedores VS Code de forma segura

[English](../03-configure-vscode.md) | Español

Las variables de terminal y los ajustes de selección del workspace no registran
proveedores. Usa grupos Custom Endpoint y el servicio nativo de credenciales.
No escribas claves en JSON ni copies SQLite de otro PC.

Usa perfiles v2 con capacidades revisadas. Genera una solicitud **privada y sin claves**:

```bash
python3 scripts/vscode_config.py work --output "$HOME/foundry-editor-import.json"
```

Se admiten varios nombres de perfil. Solo se exportan los modelos principales.
Cada uno usa su deployment, URL Responses completa, capacidades tool/vision y
límites individuales. La importación automática está verificada para Responses;
utiliza el diálogo seguro del editor para otras API.

## Alternativa estable: diálogo seguro

Crea un grupo Custom Endpoint por cuenta. Introduce la clave mediante su
control de credencial, no mediante chat ni un echo de terminal.
Utiliza los modelos del grupo generado como metadatos; no copies referencias
`apiKey` de otro equipo. Conserva proveedores ajenos.

## Importador experimental opcional

El código `tools/vscode-import/` ofrece un comando explícito, no un hook
automático. Verifica confianza del workspace, host Linux/WSL, identidad Azure,
vault, endpoint y metadatos antes de leer la clave.

Usa el VSIX de una release revisada. En desarrollo se genera un VSIX no
publicable con `python3 scripts/build_release.py --allow-dirty`.
Instálalo en el extension host Linux/WSL correcto mediante **Install from VSIX**.
Ejecuta **Foundry: Import Reviewed Profiles (Experimental)** desde la paleta.

Selecciona la solicitud y el `chatLanguageModels.json` del perfil activo.
El perfil estable/predeterminado Windows está bajo `%APPDATA%\Code\User`; desde
WSL selecciona su ruta `/mnt/c/...`. Perfiles nombrados, Insiders o instalaciones
portables pueden diferir. Si no existe el archivo, ábrelo/créalo desde el editor.

Revisa la confirmación modal. El importador respalda el JSON de forma privada,
importa secuencialmente y verifica persistencia/preservación.
Un grupo existente idéntico se omite; uno diferente detiene la importación.
Tras un fallo parcial, inspecciona el perfil activo antes de reintentar.
No se borran secretos ni se aplica un rollback amplio automáticamente.

Usa `lm.addLanguageModelsProviderGroup`, un comando **interno dependiente de versión**.
Si falta, utiliza el diálogo seguro. `context.secrets.store()` en una extensión
cualquiera tiene otro namespace y no fabrica referencias core
`${input:chat.lm.secret...}`. Los identificadores negativos son válidos.

Desinstala la extensión temporal al terminar. El backup privado queda bajo
`~/.local/state/copilot-foundry/vscode/`; no publiques ese directorio.

## Validación real

Elige destino de sesión **Local**, rol **Agent** y modelo etiquetado con el perfil.
Son controles distintos; Agent Host/Copilot puede ofrecer otro catálogo.
Prueba crear y leer un archivo **nuevo**, con inferencia pequeña aprobada.
Registra las combinaciones probadas: registrar JSON no equivale a probar chat
y herramientas.
