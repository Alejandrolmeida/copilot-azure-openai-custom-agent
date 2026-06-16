# 06. Recomendaciones de seguridad

🌐 Idioma: [English](../06-security.md) | Español

## Nunca confirmes secretos

No confirmes:

- Claves de API
- `.env`
- Tokens de acceso personal
- Identificadores de tenant si son sensibles en tu organización
- Endpoints privados
- Nombres de clientes
- Nombres internos de proyectos

El `.gitignore` de este repositorio excluye `.env` y `.env.*`.

## Prefiere gestores de secretos

Para desarrollo local puedes usar:

- Azure Key Vault
- Secretos de GitHub Codespaces
- Keychain del sistema operativo
- Gestores de contraseñas
- Variables de entorno inyectadas por tu perfil de shell

## Patrón con Azure Key Vault

Guarda tu clave de Azure OpenAI:

```bash
az keyvault secret set \
  --vault-name YOUR_KEY_VAULT_NAME \
  --name azure-openai-api-key \
  --value YOUR_API_KEY
```

Después configura `.env` sin la clave:

```bash
AZURE_KEYVAULT_NAME=YOUR_KEY_VAULT_NAME
AZURE_KEYVAULT_SECRET_NAME=azure-openai-api-key
AZURE_SUBSCRIPTION_ID=YOUR_SUBSCRIPTION_ID
```

El wrapper puede cargar el secreto en tiempo de ejecución.

Para una configuración totalmente portable donde endpoint, nombre de
implementación, identidad de modelo, presupuestos de tokens y nombre del secreto
de la clave se cargan desde Key Vault después de `az login`, consulta
[07. Bootstrap portable con Azure Key Vault](07-portable-keyvault-bootstrap.md).

## Privilegio mínimo

- Usa recursos separados para experimentación.
- Rota las claves con regularidad.
- Restringe el acceso de red cuando sea posible.
- Usa identidad administrada o Microsoft Entra ID cuando tu cliente y servicio
  lo admitan.
- Supervisa el uso de tokens y los costes.

## Lista de comprobación para un tutorial público

Antes de publicar un repo:

```bash
grep -R --line-number \
  -E 'sk-|api[_-]?key|secret|tenant|subscription|openai.azure.com' . \
  --exclude-dir=.git \
  --exclude=.env.example
```

Revisa cada coincidencia. Los endpoints de marcador de posición están bien; los
valores reales no.
