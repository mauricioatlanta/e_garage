"""
Configuración de producción para eGarage
"""

import dj_database_url

from .base import *

# Debug deshabilitado para producción
DEBUG = False

# Hosts permitidos para producción
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Base de datos para producción (PostgreSQL recomendado)
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}
else:
    # Fallback a SQLite si no hay DATABASE_URL
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Archivos estáticos para producción
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Archivos subidos por el usuario
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Seguridad adicional para producción
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS en producción (descomentar si usas HTTPS)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# Configuración de archivos estáticos y media para producción
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Configuración de email para producción
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Logging para producción
LOGGING["handlers"]["file"]["filename"] = BASE_DIR / "logs" / "django_prod.log"
LOGGING["loggers"]["django"]["level"] = "WARNING"
LOGGING["loggers"]["taller"]["level"] = "INFO"
