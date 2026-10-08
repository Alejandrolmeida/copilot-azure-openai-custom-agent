# 04. Perfiles CLI y sesiones

[English](../04-configure-copilot-cli.md) | Español

Empieza con un vault que contenga [configuración y API key](07-portable-keyvault-bootstrap.md).
Conserva el checkout en una ubicación permanente: los accesos apuntan a su
script y al Python local, no a rutas de otro equipo.

```bash
python3 scripts/foundry.py configure work
python3 scripts/foundry.py doctor work
export PATH="$HOME/.local/bin:$PATH"
copilot-foundry work
```

Para configurar sin interacción proporciona `--subscription`, `--tenant` y
`--vault`. Para nombres de secretos personalizados, edita un perfil JSON privado
e instálalo directamente:

```bash
python3 scripts/foundry.py install "$HOME/.config/my-foundry-input/work.json"
```

El nombre del archivo sin extensión será el perfil. Se crean
`~/.config/copilot-foundry/work.json`, `copilot-foundry`, `copilot-work` y
`Copilot-work` en `~/.local/bin`. Se mantienen nombres como `foundry1`.
Se rechazan archivos diferentes o enlaces simbólicos; revisa, no sobrescribas.
Persiste PATH en la configuración del shell real sin reemplazarla.

```bash
copilot-foundry work --model gpt-5-mini
copilot-foundry work --resume
copilot-foundry work --resume=YOUR_SESSION_ID
copilot-foundry work --model gpt-5-mini -- -p "Reply exactly OK."
```

Solo se seleccionan modelos principales configurados; no se ofrecen auxiliares.
Sin `--model`, el selector pide un número; `q`, EOF o Ctrl+C cancelan.
Sin TTY, `--model` es obligatorio. Los argumentos adicionales van tras `--`;
se rechazan overrides del proveedor/modelo/protección.

El lanzador valida tenant, vault y recurso, limpia credenciales alternativas
heredadas, lee la clave en memoria y la excluye del entorno de herramientas con
`--secret-env-vars`. No actives trazas ni vuelques el entorno.
Los procesos bajo control del mismo usuario/root siguen siendo una amenaza.

Los perfiles v2 no fuerzan esfuerzo de razonamiento: aplica el comportamiento
del modelo en el CLI. Los v1 mantienen su esfuerzo anterior por compatibilidad.
No se modifican ajustes globales de subagentes.
Antes de iniciar Copilot, el lanzador lee de Azure el límite de tokens por
60 segundos del deployment elegido. Reserva como máximo un cuarto de esos
TPM para una petición, hasta un cuarto de ese presupuesto para salida, y
limita la entrada y salida anunciadas. Si falta la cuota, no coincide el
deployment o es insuficiente, falla antes de leer la API key.
`--print-config` muestra tanto los límites configurados del modelo como
los límites efectivos al arrancar. Este límite no garantiza evitar todo 429:
sesiones simultáneas, turnos rápidos, imágenes y otros consumidores comparten
el deployment. Respeta Retry-After; compacta o abre una sesión nueva si
crece el historial.
Para una peticion **individual** grande despues de aprobarse mas cuota, usa
`copilot-foundry work --model MODELO --full-context`. Se detiene antes de leer
la clave si el TPM real no cubre los limites configurados de entrada y salida
dejando al menos un 12,5 % libre (1.200.000 TPM para 922.000 + 128.000).
Este modo evita el limite conservador por peticion; concurrencia, estimacion
de tokens y otros consumidores pueden seguir causando 429, y los contextos
grandes cuestan mas. No solicita cuota ni modifica deployments.

## Cambio y diagnóstico

El lanzador de proveedor único fija endpoint y deployment al arrancar.
`/model` no cambia de suscripción. Sal y relanza otro perfil/modelo con
`--resume`. No abras dos procesos sobre la misma sesión.
Un ID de otro PC no tiene por qué existir localmente.

`doctor` es el diagnóstico resumido compartible. `--print-config` contiene
identificadores operativos: conserva su salida en privado.
`--smoke-test` consume tokens explícitamente, exige `OK` y uso registrado,
y limita la salida a 1.024 tokens o al máximo del modelo si es menor.
El modelo debe soportar la API declarada; no hay fallback automático.
