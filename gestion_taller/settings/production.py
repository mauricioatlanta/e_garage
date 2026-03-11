"""
Configuración de producción para eGarage en Render
"""

from pathlib import Path

import dj_database_url

from .base import *

# Debug deshabilitado para producción
DEBUG = False

# Hosts permitidos para producción
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Base de datos para producción
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    if DATABASE_URL.startswith("sqlite"):
        # SQLite: no usar ssl_require (rompe con sslmode)
        DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
    else:
        # Postgres/MySQL/etc: ssl requerido en prod
        DATABASES = {
            "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
        }
else:
    # Fallback a SQLite si no hay DATABASE_URL
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# WhiteNoise para archivos estáticos - insertar después de SecurityMiddleware
MIDDLEWARE = MIDDLEWARE.copy()
# Insertar WhiteNoise después de SecurityMiddleware
security_index = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
MIDDLEWARE.insert(security_index + 1, "whitenoise.middleware.WhiteNoiseMiddleware")

# Archivos estáticos con WhiteNoise
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Archivos subidos por el usuario (en disco persistente de Render)
MEDIA_URL = "/media/"
MEDIA_ROOT = Path("/opt/render/project/src/media")

# Seguridad adicional para producción
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HTTPS en producción (Render maneja SSL automáticamente)
# 🔥 IMPRESCINDIBLE: Configuración fija para producción
# Este header es CRÍTICO cuando Django está detrás de un proxy (Nginx, Cloudflare, etc.)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# 🔥 IMPRESCINDIBLE: Fijo en True para producción (requiere SECURE_PROXY_SSL_HEADER arriba)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Configuración de caché para producción
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Logging para producción
import os
from pathlib import Path

# Crear directorio de logs si no existe
logs_dir = (
    Path("/opt/render/project/src/logs") if os.path.exists("/opt/render") else BASE_DIR / "logs"
)
logs_dir.mkdir(exist_ok=True)

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
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        "file": {
            "class": "logging.FileHandler",
            "filename": str(logs_dir / "django_prod.log"),
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        "taller": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Configuración de email para producción
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "srv24.cpanelhost.cl")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "True").lower() == "true"
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD") or os.getenv("EMAIL_PASSWORD", "")
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "10"))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "noreply@egarage.com")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", EMAIL_HOST_USER or DEFAULT_FROM_EMAIL)

# Configuración de sesiones
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_SAVE_EVERY_REQUEST = True

# Configuración de archivos
# Límites de subida de archivos (debe coincidir con client_max_body_size en Nginx)
# Nginx está configurado para 50MB, Django permite hasta 20MB en memoria
# Archivos más grandes se guardan en disco temporal automáticamente
FILE_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20MB
