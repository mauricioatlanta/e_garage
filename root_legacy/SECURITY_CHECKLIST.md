# 🔒 Checklist de Seguridad para Producción

## ✅ Configuración Básica

- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS` configurado con dominios reales
- [ ] `CSRF_TRUSTED_ORIGINS` configurado
- [ ] `SECRET_KEY` en variables de entorno (NO en código)
- [ ] Base de datos con SSL habilitado

## ✅ SSL/HTTPS

- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SECURE_PROXY_SSL_HEADER` configurado
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_HSTS_SECONDS` configurado
- [ ] `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- [ ] `SECURE_HSTS_PRELOAD = True`

## ✅ Headers de Seguridad

- [ ] `SECURE_BROWSER_XSS_FILTER = True`
- [ ] `SECURE_CONTENT_TYPE_NOSNIFF = True`
- [ ] `X_FRAME_OPTIONS = 'DENY'`
- [ ] `SECURE_REFERRER_POLICY` configurado

## ✅ Cookies

- [ ] `SESSION_COOKIE_HTTPONLY = True`
- [ ] `CSRF_COOKIE_HTTPONLY = True`
- [ ] `SESSION_COOKIE_AGE` configurado
- [ ] `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`

## ✅ Base de Datos

- [ ] Usuario de base de datos con permisos mínimos
- [ ] Conexión SSL requerida
- [ ] Backup automático configurado
- [ ] Rotación de logs configurada

## ✅ Logging

- [ ] Logs de errores configurados
- [ ] Rotación de logs configurada
- [ ] Logs de seguridad monitoreados
- [ ] Alertas de errores críticos

## ✅ Email

- [ ] SMTP configurado con autenticación
- [ ] `DEFAULT_FROM_EMAIL` configurado
- [ ] Notificaciones de seguridad habilitadas

## ✅ Archivos

- [ ] `FILE_UPLOAD_MAX_MEMORY_SIZE` limitado
- [ ] `DATA_UPLOAD_MAX_MEMORY_SIZE` limitado
- [ ] Validación de tipos de archivo
- [ ] Escaneo de malware (opcional)

## ✅ Monitoreo

- [ ] Sentry o similar configurado
- [ ] Alertas de errores críticos
- [ ] Monitoreo de rendimiento
- [ ] Logs de acceso monitoreados

## ✅ Backup

- [ ] Backup automático de base de datos
- [ ] Backup de archivos media
- [ ] Pruebas de restauración
- [ ] Almacenamiento seguro de backups

## ✅ Variables de Entorno

```bash
# Variables críticas que deben estar en .env
SECRET_KEY=tu-secret-key-super-seguro
DB_PASSWORD=tu-password-de-base-de-datos
EMAIL_HOST_PASSWORD=tu-password-de-email
REDIS_URL=redis://localhost:6379/1
SENTRY_DSN=tu-sentry-dsn
```

## ✅ Comandos de Verificación

```bash
# Verificar configuración de Django
python manage.py check --deploy

# Verificar seguridad
python manage.py check --deploy --settings=gestion_taller.settings.prod

# Verificar índices de base de datos
python manage.py dbshell
\di  # Listar índices

# Verificar logs
tail -f logs/egarage_prod.log
tail -f logs/egarage_errors.log
```

## ✅ Herramientas de Seguridad

- [ ] `safety` - Verificar dependencias vulnerables
- [ ] `bandit` - Análisis estático de seguridad
- [ ] `django-security` - Verificaciones de seguridad
- [ ] `django-csp` - Content Security Policy

## ✅ Configuración del Servidor

- [ ] Firewall configurado
- [ ] SSH con clave pública
- [ ] Usuario no-root para la aplicación
- [ ] Servidor web configurado (Nginx/Apache)
- [ ] SSL/TLS configurado
- [ ] Rate limiting configurado

## ✅ Pruebas de Seguridad

- [ ] Pruebas de penetración básicas
- [ ] Verificación de headers de seguridad
- [ ] Pruebas de inyección SQL
- [ ] Pruebas de XSS
- [ ] Pruebas de CSRF

## 🚨 Alertas Críticas

- [ ] Configurar alertas para errores 500
- [ ] Configurar alertas para intentos de login fallidos
- [ ] Configurar alertas para cambios en configuración
- [ ] Configurar alertas para uso anómalo de recursos

## 📋 Comandos de Mantenimiento

```bash
# Verificar dependencias vulnerables
safety check

# Análisis de seguridad
bandit -r . -f json -o bandit-report.json

# Verificar configuración
python manage.py check --deploy

# Backup de base de datos
python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json

# Limpiar logs antiguos
find logs/ -name "*.log" -mtime +30 -delete
```

## 🔄 Actualizaciones

- [ ] Plan de actualizaciones regulares
- [ ] Proceso de actualización documentado
- [ ] Rollback plan configurado
- [ ] Pruebas post-actualización

## 📞 Contactos de Emergencia

- [ ] Lista de contactos para incidentes de seguridad
- [ ] Procedimientos de respuesta a incidentes
- [ ] Plan de comunicación en caso de brecha
- [ ] Documentación de recuperación

---

**⚠️ IMPORTANTE**: Este checklist debe ser revisado y actualizado regularmente. La seguridad es un proceso continuo, no un estado final.
