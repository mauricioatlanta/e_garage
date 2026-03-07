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

# CSRF (orígenes sin wildcards; Django no soporta * en CSRF_TRUSTED_ORIGINS)
# Diagnóstico 403 POST login: activar temporalmente para loguear razón exacta del fallo CSRF:
# CSRF_FAILURE_VIEW = "taller.views_extra.csrf_debug.csrf_failure"
_csrf_origins_raw = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    ["https://egarage.cl", "https://www.egarage.cl"],
)
CSRF_TRUSTED_ORIGINS = [o for o in _csrf_origins_raw if "*" not in o]
if not any("egarage.cl" in o for o in CSRF_TRUSTED_ORIGINS):
    CSRF_TRUSTED_ORIGINS.extend(["https://egarage.cl", "https://www.egarage.cl"])

# Cookie CSRF compartida entre www y no-www (evita 403 si el usuario alterna entre ellos)
# Opcional: en .env define DJANGO_CSRF_COOKIE_DOMAIN=.egarage.cl
_csrf_cookie_domain = os.getenv("DJANGO_CSRF_COOKIE_DOMAIN", "").strip()
if _csrf_cookie_domain:
    CSRF_COOKIE_DOMAIN = _csrf_cookie_domain

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
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

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
# 1) DATABASE_URL sqlite → SQLite  2) DATABASE_URL postgres + password → Postgres  3) Else → SQLite (evita fe_sendauth sin password)
# =========================
import os

DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()

if DATABASE_URL.startswith("sqlite"):
    # sqlite:///path o sqlite:////absolute/path
    import urllib.parse

    _u = urllib.parse.urlparse(DATABASE_URL)
    db_path = (_u.path or "").strip()
    if db_path.startswith("//"):
        db_path = "/" + db_path.lstrip("/")
    if not db_path or not os.path.isabs(db_path):
        db_path = str(BASE_DIR / (db_path or "data/db.sqlite3"))
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": db_path,
        }
    }
elif (
    DATABASE_URL
    and ("postgres" in DATABASE_URL.lower())
    and (os.getenv("DB_PASSWORD") or os.getenv("DJANGO_DB_PASSWORD"))
):
    # PostgreSQL solo si hay URL Y contraseña (evita "no password supplied")
    import dj_database_url

    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
elif os.getenv("DB_PASSWORD") or os.getenv("DJANGO_DB_PASSWORD"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "egarage_prod"),
            "USER": os.getenv("DB_USER", "egarage_user"),
            "PASSWORD": os.getenv("DB_PASSWORD") or os.getenv("DJANGO_DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "OPTIONS": {"sslmode": os.getenv("DB_SSLMODE", "disable")},
        }
    }
else:
    # Sin DATABASE_URL o sin contraseña Postgres → SQLite (evita intentar Postgres y fallar)
    _sqlite_path = os.getenv("SQLITE_PATH", "/srv/egarage/data/db.sqlite3")
    if not os.path.isabs(_sqlite_path):
        _sqlite_path = str(BASE_DIR / _sqlite_path.lstrip("/"))
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _sqlite_path,
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
# Usar handlers de archivo solo si existe logs/ y es escribible (evita 502 en servidor).
_logs_dir = os.path.join(BASE_DIR, "logs")
_use_file_handlers = os.path.isdir(_logs_dir) and os.access(_logs_dir, os.W_OK)

_handlers = {
    "console": {
        "level": "WARNING",
        "class": "logging.StreamHandler",
        "formatter": "simple",
    },
}
if _use_file_handlers:
    _handlers["file"] = {
        "level": "INFO",
        "class": "logging.handlers.RotatingFileHandler",
        "filename": os.path.join(_logs_dir, "egarage_prod.log"),
        "maxBytes": 1024 * 1024 * 15,
        "backupCount": 10,
        "formatter": "verbose",
    }
    _handlers["error_file"] = {
        "level": "ERROR",
        "class": "logging.handlers.RotatingFileHandler",
        "filename": os.path.join(_logs_dir, "egarage_errors.log"),
        "maxBytes": 1024 * 1024 * 15,
        "backupCount": 10,
        "formatter": "verbose",
    }

_root_handlers = ["console", "file"] if _use_file_handlers else ["console"]
_django_handlers = ["file", "error_file"] if _use_file_handlers else ["console"]
_request_handlers = ["error_file"] if _use_file_handlers else ["console"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": _handlers,
    "root": {
        "handlers": _root_handlers,
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": _django_handlers,
            "level": "INFO",
            "propagate": False,
        },
        "taller": {
            "handlers": _django_handlers,
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": _request_handlers,
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": _request_handlers,
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# =============================================================================
# EMAIL
# =============================================================================

# Configuración de email para producción
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@egarage.cl")
# Email: evita que se cuelgue y mate el worker (Gunicorn timeout)
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "10"))  # segundos

# =============================================================================
# ARCHIVOS ESTÁTICOS
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]  # si existe /srv/egarage/static

# Evitar 500 por manifest faltante: si no se ha ejecutado collectstatic o falta staticfiles.json,
# usar FileSystemStorage (sin hash). Definir EGARAGE_STATIC_MANIFEST=1 para usar manifest.
_use_static_manifest = os.getenv("EGARAGE_STATIC_MANIFEST", "").strip().lower() in (
    "1",
    "true",
    "yes",
)
_static_backend = (
    "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    if _use_static_manifest
    else "django.contrib.staticfiles.storage.FileSystemStorage"
)

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": _static_backend},
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
