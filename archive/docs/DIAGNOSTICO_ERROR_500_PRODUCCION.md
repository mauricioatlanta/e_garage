# Diagnóstico del Error 500 en Producción

## Situación
El admin de Django en producción (`https://www.egarage.cl/admin/`) está devolviendo un error 500 (Internal Server Error).

## ✅ Cambios Realizados para Hacer el Código Más Robusto

Se han realizado cambios para que el código no falle si hay problemas con la app de WhatsApp:

1. **`whatsapp/admin.py`**: Ahora captura todas las excepciones, no solo `ImportError` y `LookupError`
2. **`whatsapp/apps.py`**: El método `ready()` ahora solo loggea errores en modo DEBUG
3. **`gestion_taller/urls.py`**: La importación de `whatsapp.admin` ahora captura cualquier excepción

**⚠️ IMPORTANTE:** Estos cambios necesitan ser desplegados en producción para que surtan efecto.

## Pasos para Diagnosticar

### 1. Ver los Logs del Servidor (PythonAnywhere)

En PythonAnywhere, ve a:
1. **Web tab** → **Error log** (últimas líneas)

O desde la consola de Bash:
```bash
tail -n 100 ~/logs/error.log
```

Busca el traceback completo que muestra qué línea de código está fallando.

### 2. Posibles Causas

#### A. La app `whatsapp` no está en INSTALLED_APPS en producción
**Solución:** Verifica que `gestion_taller/settings.py` en producción tenga:
```python
INSTALLED_APPS = [
    # ...
    "whatsapp.apps.WhatsAppConfig",
    # ...
]
```

#### B. Error al importar los modelos de WhatsApp
**Síntoma:** El traceback menciona `whatsapp.models` o `EmpresaWhatsAppConfig`
**Solución:** Verifica que el código de `whatsapp/models.py` esté desplegado correctamente.

#### C. Error en `whatsapp/apps.py` método `ready()`
**Síntoma:** El traceback menciona `whatsapp.admin` o `register_whatsapp_admin`
**Solución temporal:** Comentar temporalmente el contenido del método `ready()`:
```python
def ready(self):
    pass  # Comentado temporalmente para evitar errores
```

#### D. Migraciones pendientes
**Síntoma:** `django.db.utils.OperationalError: no such table: whatsapp_empresa_config`
**Solución:** Ejecutar migraciones en producción:
```bash
python manage.py migrate
```

### 3. Solución Temporal Rápida (Si es Urgente)

Si necesitas que el admin funcione YA y el problema es la app de WhatsApp:

#### Opción 1: Desactivar temporalmente WhatsApp (MÁS RÁPIDA)
En `gestion_taller/settings.py` de producción, comenta temporalmente:
```python
INSTALLED_APPS = [
    # ...
    # "whatsapp.apps.WhatsAppConfig",  # Temporalmente desactivado
    # ...
]
```

Luego reinicia el servidor web en PythonAnywhere (Web tab → Reload).

#### Opción 2: Desplegar los Cambios Realizados (RECOMENDADA)
Los cambios ya realizados en el código deberían prevenir este error. Solo necesitas:
1. Hacer commit y push de los cambios
2. Desplegar en PythonAnywhere
3. Reiniciar el servidor web

#### Opción 3: Si el código no está disponible en producción
Asegúrate de que los archivos `whatsapp/admin.py`, `whatsapp/apps.py` y `gestion_taller/urls.py` estén actualizados en el servidor.

### 4. Verificar el Estado Actual

En la consola de PythonAnywhere, ejecuta:
```bash
python manage.py check
```

Este comando te dirá si hay problemas de configuración.

### 5. Probar Importaciones Manualmente

En la consola de PythonAnywhere:
```bash
python manage.py shell
```

Luego intenta:
```python
from whatsapp.models import EmpresaWhatsAppConfig
from whatsapp.admin import register_whatsapp_admin
import whatsapp.apps
```

Si alguna de estas líneas falla, ese es el problema.

## Próximos Pasos

1. **Revisa los logs** y comparte el traceback completo
2. Si no puedes acceder a los logs, usa la **Opción 1** (desactivar temporalmente)
3. Una vez que identifiques el error, aplica la solución correspondiente
