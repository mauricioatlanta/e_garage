# 🚀 Preparación para Producción - eGarage

**Fecha:** Diciembre 2024  
**Versión:** 1.0  
**Estado:** ✅ Configurado

---

## 📋 Resumen

Configuración completa para despliegue en producción con variables de entorno, WhiteNoise para archivos estáticos y seguridad mejorada.

> **📌 Para despliegue específico en PythonAnywhere, consulta:** [`DESPLEGUE_PYTHONANYWHERE.md`](./DESPLEGUE_PYTHONANYWHERE.md)

---

## ✅ Checklist de Pre-Producción

- [x] Variables de entorno configuradas (.env)
- [x] WhiteNoise configurado para archivos estáticos
- [x] Base de datos con soporte utf8mb4 (MySQL)
- [x] Security headers configurados
- [x] Código legacy limpiado (registro_unificado)

---

## 🔐 Variables de Entorno

### Archivo `.env`

Crea un archivo `.env` en la raíz del proyecto (junto a `manage.py`) con las siguientes variables:

```env
# Django Core
DJANGO_SECRET_KEY=tu-clave-super-secreta-y-larga-aqui
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=egarage.cl,www.egarage.cl,.pythonanywhere.com

# Base de Datos (MySQL para PythonAnywhere)
DB_ENGINE=mysql
DB_NAME=tu_usuario$egarage_db
DB_USER=tu_usuario
DB_PASSWORD=tu_password_seguro
DB_HOST=tu_usuario.mysql.pythonanywhere-services.com
DB_PORT=3306

# Email (SMTP)
EMAIL_HOST=srv24.cpanelhost.cl
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=subscription@egarage.cl
EMAIL_HOST_PASSWORD=tu_password_email
DEFAULT_FROM_EMAIL=eGarage <subscription@egarage.cl>

# Seguridad HTTPS (Producción)
DJANGO_CSRF_TRUSTED_ORIGINS=https://egarage.cl,https://www.egarage.cl
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
```

### Generar SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Verificar .gitignore

El archivo `.env` debe estar en `.gitignore` (ya está configurado):

```
.env
```

---

## ⚡ WhiteNoise - Archivos Estáticos

### Configuración

WhiteNoise ya está configurado en `settings.py`:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # ✅ Agregado
    # ... resto del middleware
]

# En producción
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

### Ventajas de WhiteNoise

- ✅ **Self-contained**: Django sirve sus propios estáticos
- ✅ **Compresión automática**: Archivos CSS/JS comprimidos
- ✅ **Cache headers**: Mejor rendimiento
- ✅ **Sin configuración manual**: No necesitas configurar carpetas en PythonAnywhere

### Comandos

```bash
# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# WhiteNoise los comprimirá automáticamente
```

---

## 🗄️ Base de Datos MySQL

### Configuración utf8mb4

La configuración ya está en `settings.py`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES', character_set_connection=utf8mb4, collation_connection=utf8mb4_unicode_ci",
        },
    }
}
```

### Verificar en MySQL

```sql
-- Verificar charset de la base de datos
SHOW CREATE DATABASE tu_base_de_datos;

-- Debe mostrar: DEFAULT CHARACTER SET utf8mb4
```

---

## 🛡️ Security Headers

### Configuración en settings.py

Ya está configurado:

```python
# HTTPS forzado (solo en producción)
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", not DEBUG)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", not DEBUG)

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "0" if DEBUG else "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", not DEBUG)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", not DEBUG)

# Otros headers
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
```

### Verificar Headers

Puedes verificar los headers con:

```bash
curl -I https://tu-dominio.com
```

Debes ver:
- `Strict-Transport-Security: max-age=31536000`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`

---

## 🧹 Limpieza de Código Legacy

### registro_unificado

**Estado:** ✅ Deprecado y redirigido

**Archivos modificados:**
- `taller/registro_views.py` - Redirige a `/registro/`
- `taller/views_extra/views.py` - Función renombrada a `registro_unificado_legacy()`

**Acción:** Las URLs legacy ahora redirigen permanentemente (301) al flujo moderno.

---

## 📦 Dependencias

### Instalación

```bash
pip install -r requirements.txt
```

### Verificar WhiteNoise

```bash
pip show whitenoise
```

Debe mostrar la versión instalada.

---

## 🚀 Comandos de Despliegue

### 1. Preparar Archivos Estáticos

```bash
# Recolectar y comprimir archivos estáticos
python manage.py collectstatic --noinput
```

### 2. Verificar Configuración

```bash
# Verificar que no hay errores
python manage.py check --deploy
```

### 3. Migraciones

```bash
# Aplicar migraciones
python manage.py migrate
```

### 4. Crear Superusuario (si es necesario)

```bash
python manage.py createsuperuser
```

---

## 🔍 Verificación Post-Despliegue

### 1. Verificar Archivos Estáticos

Visita: `https://tu-dominio.com/static/admin/css/base.css`

Debe cargar correctamente (no 404).

### 2. Verificar HTTPS

- ✅ Redirección automática de HTTP a HTTPS
- ✅ Cookies seguras
- ✅ CSRF funcionando

### 3. Verificar Base de Datos

```bash
python manage.py dbshell
```

```sql
-- Verificar charset
SHOW VARIABLES LIKE 'character_set%';
```

### 4. Verificar Email

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
send_mail('Test', 'Test message', 'subscription@egarage.cl', ['tu-email@example.com'])
```

---

## 📝 Archivos de Configuración

### .env.example

Template de variables de entorno (ya creado).

### settings.py

- ✅ Variables de entorno configuradas
- ✅ WhiteNoise configurado
- ✅ Security headers configurados
- ✅ Base de datos con utf8mb4

---

## ⚠️ Notas Importantes

### Seguridad

1. **NUNCA** commitees el archivo `.env` real
2. **SIEMPRE** usa `DEBUG=False` en producción
3. **SIEMPRE** configura `ALLOWED_HOSTS` con tu dominio real
4. **SIEMPRE** usa HTTPS en producción

### Performance

1. WhiteNoise comprime archivos automáticamente
2. Los archivos estáticos se cachean por 1 año
3. Usa `collectstatic` antes de cada despliegue

### Base de Datos

1. MySQL debe usar `utf8mb4` para soportar emojis
2. Configura conexiones persistentes si es posible
3. Usa índices en campos frecuentemente consultados

---

## ✅ Checklist Final

- [x] Variables de entorno configuradas
- [x] WhiteNoise instalado y configurado
- [x] Security headers configurados
- [x] Base de datos con utf8mb4
- [x] Código legacy limpiado
- [x] .env en .gitignore
- [x] .env.example creado
- [ ] Testing en servidor de staging
- [ ] Verificar archivos estáticos en producción
- [ ] Verificar HTTPS funcionando
- [ ] Verificar emails funcionando

---

**Última actualización:** Diciembre 2024  
**Autor:** Sistema de Preparación para Producción  
**Estado:** ✅ Configurado y Listo

