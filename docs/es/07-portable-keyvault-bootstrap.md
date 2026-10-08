# 07. Inicialización Key Vault y actualización de metadatos

[English](../07-portable-keyvault-bootstrap.md) | Español

Copia los ejemplos sintéticos de perfil/configuración a una carpeta privada
fuera del repositorio. Sustituye identidades y verifica límites publicados
y deployment real de cada modelo. No añadas claves a los JSON.

```bash
mkdir -p "$HOME/.config/my-foundry-input"
chmod 700 "$HOME/.config/my-foundry-input"
cp examples/profile.example.json "$HOME/.config/my-foundry-input/work.json"
cp examples/config.example.json "$HOME/.config/my-foundry-input/config.json"
```

Edita las copias. El vault y la cuenta deben existir. Aprovisionar no concede
automáticamente escritura de secretos. El propietario debe aprobar el rol
mínimo necesario; esta herramienta no concede ni retira roles.

```bash
python3 scripts/seed_vault.py "$HOME/.config/my-foundry-input/work.json" "$HOME/.config/my-foundry-input/config.json" --confirm-write
python3 scripts/foundry.py install "$HOME/.config/my-foundry-input/work.json"
python3 scripts/foundry.py doctor work
```

La inicialización rechaza secretos ya existentes. Lee la clave en memoria y la
escribe por HTTPS en Key Vault, nunca en argumentos de proceso. No rota claves.
Si falla el segundo secreto, inspecciona el estado parcial: no sobrescribas ni
borres la clave ciegamente. Las versiones Key Vault permiten recuperar valores.

Para actualizar **solo metadatos** revisados de la misma cuenta:

```bash
python3 scripts/seed_vault.py "$HOME/.config/my-foundry-input/work.json" "$HOME/.config/my-foundry-input/config.json" --update-config-only --confirm-write
```

Conserva la clave y rechaza redirigir su configuración a otra cuenta. Revisa
el diff del JSON antes de confirmar. Retira los permisos temporales de escritura;
el cliente normal solo requiere lectura de secretos y metadatos.

El segundo PC inicia sesión independientemente e instala el perfil sin secretos.
Las claves se obtienen al arrancar. No copies cachés Azure ni bases de datos de
credenciales VS Code. Los nombres por defecto son `copilot-foundry-config` y
`azure-openai-api-key`; el perfil puede definir otros nombres distintos entre sí.
