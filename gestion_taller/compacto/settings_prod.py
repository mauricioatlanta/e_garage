# settings_prod.py - Configuración de producción para eGarage
import os

from .settings import *  # Importa toda la configuración base

# Debug deshabilitado en producción por defecto
DEBUG = False

# Override para permitir debug en casos específicos de desarrollo local
if os.environ.get("FORCE_DEBUG", "0") == "1":
    DEBUG = True

# Hosts permitidos para producción
ALLOWED_HOSTS = [
    "atlantareciclajes.cl",
    "127.0.0.1",
    "localhost",
]

# Configuración para proxy SSL (Nginx / DigitalOcean)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Configuración de seguridad SSL
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

_cookie_domain = (os.environ.get("DJANGO_COOKIE_DOMAIN") or "").strip()
if not _cookie_domain:
    for _origin in CSRF_TRUSTED_ORIGINS or []:
        _origin = (_origin or "").strip()
        if not _origin or "://" not in _origin:
            continue
        _host = _origin.split("://", 1)[1].split("/", 1)[0].strip()
        _host = _host.replace("*.", "").strip()
        if _host.startswith("www."):
            _host = _host[4:]
        if _host:
            _cookie_domain = "." + _host.lstrip(".")
            break
if _cookie_domain:
    CSRF_COOKIE_DOMAIN = _cookie_domain
    SESSION_COOKIE_DOMAIN = _cookie_domain

# Overrides para desarrollo local si se fuerza DEBUG
if DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# HSTS (HTTP Strict Transport Security) - Solo activar cuando todo esté bajo HTTPS
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF trusted origins para dominios de producción
CSRF_TRUSTED_ORIGINS = [
    "https://atlantareciclajes.cl",
]

# Cabeceras de seguridad adicionales
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Configuración de logging para producción
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
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
            "filename": "django_prod.log",
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
            "level": "INFO",
            "propagate": False,
        },
        "taller": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Deshabilitamos la configuración de mimetypes que solo es para desarrollo
if not DEBUG:
    # Configuración de cacheo en producción
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }

    # Configuración optimizada para archivos estáticos en producción
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Overrides de archivos estáticos para django-autocomplete-light (Select2)
DAL_SELECT2_CSS = {"all": ("autocomplete_light_custom/vendor/select2/dist/css/select2.min.css",)}

DAL_SELECT2_JS = (
    "autocomplete_light_custom/vendor/select2/dist/js/select2.full.min.js",
    "autocomplete_light_custom/init.js",
    "autocomplete_light_custom/jquery.init.js",
    "autocomplete_light_custom/autocomplete.init.js",
)
