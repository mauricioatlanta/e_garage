# 🚀 **COMANDOS DE DESPLIEGUE**

## **1. Variables de Entorno (configurar en servidor)**
```bash
# Configuración básica
export DJANGO_SETTINGS_MODULE="gestion_taller.settings.production"
export DEBUG="False"
export SECRET_KEY="your-secret-key-here"

# Base de datos PostgreSQL
export DATABASE_URL="postgres://user:password@host:port/dbname"

# Hosts y CSRF
export ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"
export CSRF_TRUSTED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"

# SMTP (opcional)
export EMAIL_HOST="smtp.gmail.com"
export EMAIL_PORT="587"
export EMAIL_USE_TLS="True"
export EMAIL_HOST_USER="your-email@gmail.com"
export EMAIL_HOST_PASSWORD="your-app-password"

# Sentry (opcional)
export SENTRY_DSN="https://your-sentry-dsn@sentry.io/project-id"
```

## **2. Migraciones y Estáticos**
```bash
# Resolver problema NOT NULL (si no se ha hecho)
# Editar taller/models/documento.py (agregar null=True, blank=True)

# Migraciones
python manage.py makemigrations taller
python manage.py migrate

# Archivos estáticos
python manage.py collectstatic --noinput
```

## **3. Verificación**
```bash
# Verificar configuración
python manage.py shell -c "from django.conf import settings; print('DEBUG=', settings.DEBUG)"

# Verificar base de datos
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1'); print('DB OK')"
```

## **4. Gunicorn (Render)**
```bash
# Comando de inicio
gunicorn gestion_taller.wsgi:application --workers 3 --timeout 120 --bind 0.0.0.0:8000

# Con variables de entorno
DJANGO_SETTINGS_MODULE=gestion_taller.settings.production gunicorn gestion_taller.wsgi:application --workers 3 --timeout 120
```

## **5. Health Check**
```bash
# Crear endpoint /health/ (opcional)
curl http://localhost:8000/health/
# Debe devolver 200 OK
```

## **6. Post-Deploy Checklist**
```bash
# 1. Crear documento en /cl/ y /us/
# 2. Verificar totales en admin
# 3. Revisar logs
# 4. Probar correo (si aplica)
# 5. Verificar métricas dashboard
```

## **7. Comandos PowerShell (Windows)**
```powershell
# Variables
$ENV:DJANGO_SETTINGS_MODULE="gestion_taller.settings.production"
$ENV:DEBUG="False"

# Migrar y collectstatic
python manage.py migrate
python manage.py collectstatic --noinput

# Sanity check
python manage.py shell -c "from django.conf import settings; print('DEBUG=', settings.DEBUG); print('STATICFILES_STORAGE=', settings.STATICFILES_STORAGE)"
```

## **8. Git y Deploy**
```bash
# Commit final
git add .
git commit -m "backend==frontend sync ✅ - Production ready"

# Push a main
git push origin main

# En Render: el deploy se ejecuta automáticamente
# En DigitalOcean: reiniciar app desde dashboard
```

## **9. Verificación Post-Deploy**
```bash
# Smoke test funcional
curl -I http://yourdomain.com/cl/es/documentos/form/
curl -I http://yourdomain.com/us/en/documentos/form/

# Verificar archivos estáticos
curl -I http://yourdomain.com/static/taller/common/js/documentos_form.js

# Health check
curl http://yourdomain.com/health/
```

## **10. Rollback (si es necesario)**
```bash
# Volver a release anterior
git revert HEAD
git push origin main

# Restaurar backup DB (si hubo migraciones destructivas)
# Verificar healthcheck
curl http://yourdomain.com/health/
```
