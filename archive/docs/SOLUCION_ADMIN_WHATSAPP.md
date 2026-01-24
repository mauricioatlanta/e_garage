# 🔧 Solución: No Aparece WhatsApp en Admin

## Problema

Los modelos de WhatsApp no aparecen en el admin de Django.

## Solución Aplicada

Se ha actualizado `whatsapp/apps.py` para importar automáticamente el admin cuando la app se carga.

## Verificación

Para verificar que funciona:

1. **Reinicia el servidor Django:**
   ```bash
   # Detén el servidor (Ctrl+C) y vuelve a iniciarlo
   python manage.py runserver
   ```

2. **Accede al admin:**
   ```
   http://127.0.0.1:8000/admin/
   ```

3. **Deberías ver:**
   - En el menú lateral: **"eGarage Air (WhatsApp)"** o **"WhatsApp"**
   - Dentro: **"Configuraciones WhatsApp Empresas"** y **"Sesiones WhatsApp"**

## Si Aún No Aparece

### Opción 1: Verificar que la app esté en INSTALLED_APPS

En `gestion_taller/settings.py`, verifica que esté:
```python
INSTALLED_APPS = [
    # ...
    "whatsapp.apps.WhatsAppConfig",
    # ...
]
```

### Opción 2: Forzar importación del admin

Ejecuta en la shell de Django:
```python
python manage.py shell
>>> import whatsapp.admin
>>> from django.contrib import admin
>>> from whatsapp.models import EmpresaWhatsAppConfig
>>> admin.site.is_registered(EmpresaWhatsAppConfig)
True
```

### Opción 3: Usar el script helper

Usa el script `crear_admin_whatsapp.py` que crea la configuración directamente:
```bash
python crear_admin_whatsapp.py
# Selecciona opción 2
```

## Acceso Directo

Si necesitas acceder directamente sin pasar por el menú:

```
http://127.0.0.1:8000/admin/whatsapp/empresawhatsappconfig/
```

## Nota

Si las tablas no existen aún (problema de migraciones), el admin puede no mostrar los modelos. En ese caso:
1. Crea las tablas manualmente usando el SQL en `WHATSAPP_FIX_MIGRACIONES.md`
2. O usa el script `crear_admin_whatsapp.py` que crea la configuración directamente
