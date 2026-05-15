# Solución: App WhatsApp No Se Carga

## Problema

La app `whatsapp` está en `INSTALLED_APPS` en `settings.py`, pero Django no la está cargando cuando se ejecuta. Por eso no aparece en el admin.

## Diagnóstico

1. La app está en `INSTALLED_APPS` en el archivo `settings.py` (línea 90)
2. Pero NO aparece en la lista de apps instaladas cuando Django se ejecuta
3. La app se puede importar manualmente sin problemas
4. Los modelos se pueden importar sin problemas

## Solución Temporal

Ya actualicé `whatsapp/admin.py` para que no registre los modelos si la app no está disponible. Esto evita el error `LookupError` en el admin.

## Solución Definitiva

El problema puede ser que hay un error al importar la app durante el setup de Django que se está silenciando. Para solucionarlo:

### Opción 1: Usar el script para crear configuración directamente

```bash
python crear_config_whatsapp_directo.py
```

Este script crea la configuración directamente en la base de datos sin necesidad del admin.

### Opción 2: Verificar errores de importación

Revisa los logs del servidor Django al iniciar para ver si hay errores relacionados con `whatsapp`.

### Opción 3: Reiniciar el servidor completamente

1. Detén el servidor completamente (Ctrl+C)
2. Elimina archivos `__pycache__`:
   ```bash
   find whatsapp -type d -name __pycache__ -exec rm -r {} +
   ```
3. Reinicia el servidor:
   ```bash
   python manage.py runserver
   ```

## Nota

Si después de reiniciar la app sigue sin aparecer, puede haber un problema más profundo con la estructura de la app o con algún import circular. En ese caso, usa el script `crear_config_whatsapp_directo.py` para crear la configuración directamente.
