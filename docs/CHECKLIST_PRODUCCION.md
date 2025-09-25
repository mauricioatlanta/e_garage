# Checklist de Producción - eGarage

## 🔒 Seguridad Básica

### Variables de Entorno Críticas
- [ ] `DJANGO_DEBUG=False`
- [ ] `DJANGO_SECRET_KEY` - Clave única y segura
- [ ] `ALLOWED_HOSTS` - Sin `"*"`, solo dominios reales
- [ ] `EMAIL_PASSWORD` - Contraseña real de email
- [ ] `DATABASE_URL` - Conexión a PostgreSQL/MySQL

### HTTPS/SSL
- [ ] `DJANGO_CSRF_TRUSTED_ORIGINS` - URLs con https://
- [ ] `DJANGO_SECURE_SSL_REDIRECT=True`
- [ ] `DJANGO_SESSION_COOKIE_SECURE=True`
- [ ] `DJANGO_CSRF_COOKIE_SECURE=True`
- [ ] `DJANGO_SECURE_HSTS_SECONDS=31536000`

### Proxy/Reverse Proxy (si aplica)
- [ ] `SECURE_PROXY_SSL_HEADER` - Si usas Nginx/PA/Render
- [ ] `USE_X_FORWARDED_HOST=True`

## 🗄️ Base de Datos

- [ ] PostgreSQL o MySQL configurado
- [ ] `DATABASE_URL` apuntando a BD de producción
- [ ] Migraciones aplicadas: `python manage.py migrate`
- [ ] Backup automático configurado

## 📧 Email

- [ ] `EMAIL_HOST` - Servidor SMTP de producción
- [ ] `EMAIL_HOST_USER` - Usuario SMTP
- [ ] `EMAIL_PASSWORD` - Contraseña real
- [ ] `EMAIL_USE_SSL=True` o `EMAIL_USE_TLS=True`
- [ ] Prueba de envío de email funcional

## 🔐 Allauth (Autenticación)

- [ ] `ACCOUNT_EMAIL_VERIFICATION="mandatory"`
- [ ] `ACCOUNT_EMAIL_REQUIRED=True`
- [ ] `ACCOUNT_CONFIRM_EMAIL_ON_GET=False`

## 📁 Archivos Estáticos

### Opción A: WhiteNoise
- [ ] `DJANGO_WHITENOISE=True`
- [ ] `python manage.py collectstatic`
- [ ] WhiteNoiseMiddleware en MIDDLEWARE

### Opción B: CDN
- [ ] CDN configurado (AWS CloudFront, etc.)
- [ ] `STATIC_URL` apuntando al CDN
- [ ] `python manage.py collectstatic`

## 🌐 Dominio y DNS

- [ ] Dominio configurado (ej: egarage.cl)
- [ ] DNS apuntando al servidor
- [ ] Certificado SSL válido
- [ ] Redirección HTTP → HTTPS

## 🔄 Sistema de Idiomas

- [ ] Chile: `request.LANGUAGE_CODE == 'es'` (forzado)
- [ ] USA: `request.LANGUAGE_CODE == 'en'` por defecto
- [ ] USA: Switcher de idioma funcional
- [ ] No se muestra switcher en Chile

## 🚀 Deployment

### Comandos Pre-Deploy
```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py compilemessages  # si usas i18n
```

### Verificaciones Post-Deploy
- [ ] Página de inicio carga correctamente
- [ ] Login funcional
- [ ] Registro funcional
- [ ] Email de confirmación llega
- [ ] Autocomplete funciona (clientes/vehículos)
- [ ] Documentos se crean correctamente
- [ ] Sistema de idiomas funciona

## 📊 Monitoreo

### Logs
- [ ] Logs de errores configurados
- [ ] Logs de seguridad monitoreados
- [ ] Logs de email configurados

### Métricas
- [ ] Uptime monitoring
- [ ] Error rate monitoring
- [ ] Performance monitoring

## 🧪 Pruebas Finales

### Funcionalidad Core
- [ ] Crear cliente
- [ ] Crear vehículo
- [ ] Crear documento
- [ ] Autocomplete funciona
- [ ] Filtros por empresa funcionan

### Seguridad
- [ ] CSRF tokens funcionan
- [ ] Cookies seguras
- [ ] Headers de seguridad presentes
- [ ] No hay información sensible en logs

### Idiomas
- [ ] Chile: Solo español, sin switcher
- [ ] USA: Inglés por defecto, switcher a español
- [ ] Preferencias se mantienen en sesión

## 🔧 Configuración de Servidor

### Nginx (ejemplo)
```nginx
server {
    listen 80;
    server_name egarage.cl www.egarage.cl;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name egarage.cl www.egarage.cl;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Variables de Entorno de Producción
```bash
# .env de producción
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-super-secret-key-here
DJANGO_ALLOWED_HOSTS=egarage.cl,www.egarage.cl
DJANGO_CSRF_TRUSTED_ORIGINS=https://egarage.cl,https://www.egarage.cl
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000

DATABASE_URL=postgres://user:password@localhost:5432/egarage
EMAIL_HOST=srv24.cpanelhost.cl
EMAIL_HOST_USER=subscription@egarage.cl
EMAIL_PASSWORD=your-real-email-password
ACCOUNT_EMAIL_VERIFICATION=mandatory
ACCOUNT_CONFIRM_EMAIL_ON_GET=False
```

## ✅ Sign-off

- [ ] **Desarrollo**: Todas las funcionalidades probadas
- [ ] **Seguridad**: Configuración de seguridad aplicada
- [ ] **Performance**: Optimizaciones aplicadas
- [ ] **Monitoreo**: Logs y métricas configurados
- [ ] **Backup**: Estrategia de backup implementada
- [ ] **Documentación**: Documentación actualizada

**Fecha de Deploy**: _______________
**Responsable**: _______________
**Versión**: _______________
