# 🔍 Diagnóstico Internal Server Error (500)

El error cambió de 502 a 500, lo que significa:
- ✅ Nginx está conectando correctamente a Gunicorn
- ❌ Hay un error en la aplicación Django

## Variables de entorno imprescindibles (egarage.cl)

En producción el servidor **debe** tener:

- `EGARAGE_ENV=prod` — para cargar `gestion_taller.settings.prod` (ALLOWED_HOSTS, DEBUG=False, etc.).
- Si no se ha ejecutado `collectstatic` o falta `staticfiles/staticfiles.json`, **no** definir `EGARAGE_STATIC_MANIFEST` (o `=0`). Así se usa `FileSystemStorage` y se evita 500 por manifest faltante. Cuando el manifest exista, usar `EGARAGE_STATIC_MANIFEST=1`.

## Comandos de Diagnóstico

```bash
# 1. Ver logs de error de Gunicorn (MUY IMPORTANTE – aquí sale el traceback del 500)
sudo tail -100 /srv/egarage/logs/gunicorn_error.log
# Si el proyecto está en otra ruta (ej. home):
tail -100 ~/e_garage/logs/gunicorn_error.log 2>/dev/null || tail -100 /var/log/gunicorn/error.log

# 2. Ver logs de acceso para ver qué URL está causando el error
sudo tail -20 /srv/egarage/logs/gunicorn_access.log

# 3. Comprobar que se usa settings de producción
cd /srv/egarage  # o la ruta real del proyecto
source venv/bin/activate
echo $EGARAGE_ENV   # debe ser "prod"

# 4. Probar la app localmente con settings prod (reproducir el 500)
EGARAGE_ENV=prod python manage.py runserver 0.0.0.0:8000
# Luego en el navegador: http://IP:8000/ o https://egarage.cl/ si apuntas al servidor

# 5. Probar una URL directa al backend (bypass Nginx)
curl -v http://127.0.0.1:8001/
curl -v http://127.0.0.1:8001/cl/es/bienvenida/
```

El error 500 puede ser causado por:
- **Manifest de estáticos faltante**: no se ejecutó `collectstatic` o no existe `staticfiles/staticfiles.json`. Solución: no usar manifest (dejar `EGARAGE_STATIC_MANIFEST` sin definir) o ejecutar `collectstatic` y luego `EGARAGE_STATIC_MANIFEST=1`.
- **EGARAGE_ENV distinto de `prod`**: se cargan otros settings (ej. dev) y puede fallar ALLOWED_HOSTS o la base de datos.
- Módulos comentados que se están usando en las vistas
- Error en la base de datos (conexión, migraciones pendientes)
- Error en el código de la vista o en un context processor
- Configuración incorrecta

## Para /us/centro-operaciones-espacial/ específicamente

```bash
# Ejecutar diagnóstico local
cd /srv/egarage && source venv/bin/activate
python manage.py shell
>>> exec(open('scripts/diagnostico_centro_operaciones_500.py').read())
```

La vista ahora registra excepciones con `logger.exception()`. El traceback completo aparecerá en los logs de Gunicorn.
