# 02. Infraestructura Bicep opcional

[English](../02-create-azure-openai-deployment.md) | Español

Reutilizar recursos es la opción predeterminada. Aprovisionar crea recursos
facturables y requiere permiso separado de la instalación cliente. Las pruebas
predeterminadas no despliegan en Azure.

Copia `examples/provision.example.json` **fuera del repositorio**. Sustituye
identidades sintéticas, nombres y región. El ejemplo reutiliza cuenta/vault
y no despliega modelos: no es un plan de infraestructura listo para aplicar.

Para recursos nuevos cambia `use_existing_*` a false. Utiliza
`create_resource_group` solo si es necesario. Proporciona rangos IPv4 públicos
en `allowed_ips`, o acepta acceso de red amplio mediante `allow_public_access`.
Los vaults nuevos usan RBAC, retención de 90 días y protección de purga:
comprende esa protección irreversible antes de aprobar.

Para acceso público, elige `public_selected_ips` (denegación predeterminada
con IP públicas de salida autorizadas y no vacías **tanto** en Azure OpenAI
como en Key Vault) si dispones de salida estable. `public_any_ip` permite
acceso desde cualquier IP y exige aprobación explícita y aceptación
documentada del mayor riesgo residual. Ninguna opción elimina la autenticación:
el cliente usa Entra para leer Key Vault y una clave API para inferencia.
Private Endpoints y DNS privado son una arquitectura alternativa, no forman
parte de esta plantilla.

Consulta disponibilidad sin inferencia:

```bash
python3 scripts/foundry.py catalog --subscription YOUR_SUBSCRIPTION_ID --location YOUR_REGION --model gpt-5-mini
```

Cada entrada de `deployments` requiere `model`, `version`, `deployment`, `sku`,
`capacity` (entero positivo) y `allow_global` (booleano).
Usa versión y SKU del catálogo real. `GlobalStandard` exige `allow_global: true`;
la región del recurso no limita su procesamiento global a esa región.
`Standard` y `DataZoneStandard` tienen disponibilidad/cuota diferentes.
No se soportan capacidad provisionada ni spillover implícito.

Los límites de la ficha del modelo no son unidades de asignación. El preflight
suma capacidad por modelo/SKU de esa suscripción y verifica cuota disponible.
ARM valida la capacidad. Si falta el mínimo, el valor predeterminado del catálogo
no debe interpretarse como mínimo.

`reader_object_id` crea opcionalmente **Secrets User**, nunca escritura.
Déjalo vacío si el acceso se administra fuera. `budget_amount: 0` desactiva
el presupuesto. Si lo activas, indica `budget_start` el primer día del mes y
`budget_emails` privados; el importe usa la moneda de facturación de la
suscripción. Las alertas no detienen el gasto ni deben sobrescribir presupuestos.

```bash
python3 scripts/provision.py plan "$HOME/.config/my-foundry-input/provision.json" --report "$HOME/foundry-plan.json"
python3 scripts/provision.py apply "$HOME/.config/my-foundry-input/provision.json" --approval "$HOME/foundry-plan.json" --confirm YOUR_SUBSCRIPTION_ID --report "$HOME/foundry-apply.json"
```

Lee todos los `changes` y avisos del plan privado antes de aplicar.
La aprobación cubre hashes del manifiesto/plantillas y resultado what-if:
cualquier cambio de estado exige un plan nuevo. Los informes deben ser archivos
nuevos fuera del repositorio. Solo se admite Create/NoChange/Ignore; modificaciones,
borrados y resultados opacos detienen la operación. No es un gestor general
ni una herramienta de redimensionado. Se pueden reutilizar deployments iguales;
nunca se adoptan silenciosamente cuentas ajenas como nuevas.

Bicep usa modo incremental. No hay secretos en parámetros ni outputs.
Después del despliegue, [inicializa Key Vault](07-portable-keyvault-bootstrap.md).
Ante aplicación parcial/fallida, inspecciona ARM antes de repetir. No borres
recursos previos como rollback; conserva los informes privados y las identidades.

Antes de ejecutar el cliente, inspecciona en Azure los firewalls efectivos de
**ambos** servicios, RBAC, autenticación local y monitorización. Los recursos
reutilizados conservan sus controles de acceso; la plantilla no configura
diagnósticos ni alertas de seguridad para los nuevos. El firewall de Key Vault
no restringe el uso de una clave API ya copiada del vault. Consulta la
[posición de seguridad y pruebas de aceptación](06-security.md#posición-de-seguridad-del-acceso-público)
antes de usar datos no sintéticos.

Fuentes: [Bicep](https://learn.microsoft.com/azure/azure-resource-manager/bicep/overview),
[what-if](https://learn.microsoft.com/azure/azure-resource-manager/bicep/deploy-what-if).
