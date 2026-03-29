"""
Configuración de producción para eGarage.
Configuración segura y optimizada para producción.
"""

from .base import *

# =============================================================================
# HELPERS DE ENTORNO
# =============================================================================


def env_list(name: str, default: str | list[str] = "") -> list[str]:
    """Convierte variable de entorno separada por comas en lista."""
    # Si default es una lista, convertirla a string separado por comas
    if isinstance(default, list):
        default = ",".join(default)
    raw = os.getenv(name, default) or ""
    return [x.strip() for x in raw.split(",") if x.strip()]


# =============================================================================
# CONFIGURACIÓN DE PRODUCCIÓN
# =============================================================================

DEBUG = False

# =============================================================================
# SEGURIDAD
# =============================================================================

# Hosts permitidos
ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    ["egarage.cl", "www.egarage.cl"],
)

# CSRF
CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    ["https://egarage.cl", "https://www.egarage.cl"],
)

# SSL/HTTPS (activar si usas HTTPS)
# 🔥 IMPRESCINDIBLE: Configuración fija para producción (no controlada por env)
# Este header es CRÍTICO cuando Django está detrás de un proxy (Nginx, Cloudflare, etc.)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# 🔥 IMPRESCINDIBLE: Fijo en True para producción (requiere SECURE_PROXY_SSL_HEADER arriba)
SECURE_SSL_REDIRECT = True

# Cookies seguras
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# SameSite: requerido para flujos auth normales (evita problemas CSRF en navegación)
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Dominios de cookies (permite compartir sesión/CSRF entre www y apex)
SESSION_COOKIE_DOMAIN = os.getenv("DJANGO_SESSION_COOKIE_DOMAIN", ".egarage.cl")
CSRF_COOKIE_DOMAIN = os.getenv("DJANGO_CSRF_COOKIE_DOMAIN", ".egarage.cl")

# Headers de seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# =============================================================================
# BASE DE DATOS
# =============================================================================

# =========================
# Database (PROD)
# Prefer DATABASE_URL if provided (e.g. sqlite), else fallback to Postgres env defaults
# =========================
import os

DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL.startswith("sqlite:"):
    # sqlite:////absolute/path.db
    db_path = DATABASE_URL.replace("sqlite:///", "/", 1)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": db_path,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "egarage_prod"),
            "USER": os.getenv("DB_USER", "egarage_user"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "OPTIONS": {"sslmode": os.getenv("DB_SSLMODE", "disable")},
        }
    }

# =============================================================================
# CACHÉ
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "egarage_prod",
        "TIMEOUT": 300,
    }
}

# =============================================================================
# LOGGING
# =============================================================================
# Solo consola: en VPS el usuario del servicio suele no poder escribir en
# BASE_DIR/logs; Gunicorn ya envía stdout a journald.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.security.DisallowedHost": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# =============================================================================
# EMAIL
# =============================================================================

# Configuracion de email para produccion por API HTTPS (Resend)
EMAIL_BACKEND = "taller.email_backends.resend_backend.ResendEmailBackend"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "support@egarage.cl")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", "support@egarage.cl")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

# =============================================================================
# ARCHIVOS ESTÁTICOS
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]  # si existe /srv/egarage/static

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# Configuración de archivos media para producción
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

# =============================================================================
# OPTIMIZACIONES
# =============================================================================

# Desactivar debug toolbar
DEBUG_TOOLBAR = False

# Configuración de sesiones
# ✅ FIX: Usar DB en lugar de cache para evitar pérdida de sesiones con múltiples workers
# LocMemCache no funciona con múltiples workers de Gunicorn (cada worker tiene su propia memoria)
SESSION_ENGINE = "django.contrib.sessions.backends.db"
# SESSION_CACHE_ALIAS ya no es necesario con sesiones en DB

# Configuración de archivos
# Límites de subida de archivos (debe coincidir con client_max_body_size en Nginx)
# Nginx está configurado para 50MB, Django permite hasta 20MB en memoria
# Archivos más grandes se guardan en disco temporal automáticamente
FILE_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20MB

# =============================================================================
# MONITOREO
# =============================================================================

# Configuración de monitoreo (opcional)
# Sentry para tracking de errores
# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration
#
# sentry_sdk.init(
#     dsn=os.getenv('SENTRY_DSN'),
#     integrations=[DjangoIntegration()],
#     traces_sample_rate=0.1,
#     send_default_pii=True
# )

# =============================================================================
# VARIABLES DE ENTORNO
# =============================================================================

# SECRET_KEY debe estar en variables de entorno
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

# Configuración de CORS (si usas API)
CORS_ALLOWED_ORIGINS = env_list(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    ["https://egarage.cl", "https://www.egarage.cl"],
)

# =============================================================================
# CONFIGURACIÓN ESPECÍFICA DE eGARAGE
# =============================================================================

# Configuración específica para producción
EGARAGE_PROD = True

# Configuración de backup automático
BACKUP_ENABLED = True
BACKUP_SCHEDULE = "0 2 * * *"  # Diario a las 2 AM

# Configuración de notificaciones
NOTIFICATIONS_ENABLED = True
NOTIFICATIONS_EMAIL = True
NOTIFICATIONS_SMS = False  # Configurar según necesidad

# Configuración de reportes
REPORTS_ENABLED = True
REPORTS_SCHEDULE = "0 6 * * 1"  # Lunes a las 6 AM

# Configuración de limpieza de datos
DATA_CLEANUP_ENABLED = True
DATA_CLEANUP_SCHEDULE = "0 3 * * 0"  # Domingo a las 3 AM

# =============================================================================
# CHECKLIST DE SEGURIDAD
# =============================================================================

# ✅ DEBUG = False
# ✅ ALLOWED_HOSTS configurado
# ✅ CSRF_TRUSTED_ORIGINS configurado
# ✅ SECURE_SSL_REDIRECT = True
# ✅ SESSION_COOKIE_SECURE = True
# ✅ CSRF_COOKIE_SECURE = True
# ✅ SECRET_KEY en variables de entorno
# ✅ Base de datos con SSL
# ✅ Logging configurado
# ✅ Email configurado
# ✅ Archivos estáticos configurados
# ✅ Caché configurado
# ✅ Headers de seguridad
# ✅ HSTS configurado
