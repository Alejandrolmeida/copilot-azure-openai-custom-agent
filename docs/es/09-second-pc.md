# 09. Otro PC Windows con WSL

[English](../09-second-pc.md) | Español

Es una instalación cliente, no otro despliegue Azure.
Instala/verifica WSL, Ubuntu y VS Code Windows con su extensión WSL. Solicita
permiso administrativo y reinicio si el instalador oficial los requiere.
Instala Python, Azure CLI y Copilot CLI dentro de la distribución elegida.

Usa una release/copia revisada de esta versión en una carpeta Linux permanente.
Verifica `SHA256SUMS`. No copies wrappers que apunten al PC anterior, cachés
Azure, bases del editor, historiales ni credenciales MCP.

```bash
az login --tenant YOUR_TENANT_ID
python3 scripts/foundry.py configure work
python3 scripts/foundry.py doctor work
export PATH="$HOME/.local/bin:$PATH"
copilot-foundry work
code .
```

Comprueba que VS Code conecta a la misma distribución y usuario WSL. Genera
un [import nuevo](03-configure-vscode.md) con la ruta real del perfil de destino.
Crea referencias cifradas locales, no referencias copiadas.

Prueba chat/herramientas con un archivo nuevo y poco consumo. Registra qué
perfiles/modelos se probaron; configuración no equivale a validación real.
Ambos PCs comparten cuota y presupuesto Azure; el nuevo equipo no añade capacidad.
Un ID de sesión antiguo puede no existir allí: usa historial disponible o
un traspaso saneado, no un archivo completo de sesión privada.

Los MCP son opcionales e independientes. Inventaría `/mcp` primero. Prefiere
servidores oficiales Azure, GitHub, filesystem y memory; limita carpetas,
usa autenticación local y un archivo de memoria privado nuevo. No copies
rutas absolutas de ejecutables del otro PC ni incluyas conectores de correo.
