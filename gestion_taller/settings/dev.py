"""
Configuración de desarrollo para eGarage
"""

from .base import *

# Debug habilitado para desarrollo
DEBUG = True

# Hosts permitidos para desarrollo
ALLOWED_HOSTS = ["*"]

# Base de datos SQLite para desarrollo
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Archivos estáticos para desarrollo
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Archivos subidos por el usuario
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Mimetypes útiles en desarrollo
import mimetypes
mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("application/javascript", ".js", True)

# Logging más detallado para desarrollo
LOGGING["loggers"]["django"]["level"] = "DEBUG"
LOGGING["loggers"]["taller"]["level"] = "DEBUG"
