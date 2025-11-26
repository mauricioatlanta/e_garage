"""
Configuración base para eGarage - Sistema de Gestión de Taller
Configuración común para todos los entornos (dev, prod, local)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from django.core.management.utils import get_random_secret_key

# Cargar variables de entorno desde .env
load_dotenv()

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Modo seguro para diagnóstico
SAFE_MODE = os.environ.get("EGARAGE_SAFE_MODE") == "1"

# Seguridad básica
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", get_random_secret_key())

# Aplicaciones instaladas
INSTALLED_APPS = [
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dal",
    "dal_select2",
    "crispy_forms",
    "crispy_bootstrap5",
    "taller",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "django.contrib.humanize",
    "widget_tweaks",
    "django.contrib.sites",
    "rest_framework",
    "ubicacion.apps.UbicacionConfig",
]

# Middleware común - ORDEN RECOMENDADO POR DJANGO
MIDDLEWARE = [
    # 1. Seguridad (primero)
    "django.middleware.security.SecurityMiddleware",
    # 2. Sesiones (antes de autenticación)
    "django.contrib.sessions.middleware.SessionMiddleware",
    # 3. Localización (antes de CommonMiddleware)
    "django.middleware.locale.LocaleMiddleware",
    # 4. Common (después de sesiones y locale)
    "django.middleware.common.CommonMiddleware",
    # 5. CSRF (antes de autenticación)
    "django.middleware.csrf.CsrfViewMiddleware",
    # 6. Autenticación
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # 7. Mensajes (después de autenticación)
    "django.contrib.messages.middleware.MessageMiddleware",
    # 8. Clickjacking (después de mensajes)
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 9. Allauth (después de autenticación) - Agregado dinámicamente si existe
    # 10. Middlewares personalizados (orden específico)
    # "taller.middleware.country_url_migration.CountryURLRedirectMiddleware",  # DESHABILITADO - Causa bucles infinitos
    # "taller.middleware.force_home_test.ForceHomeTestMiddleware",  # DESHABILITADO - Ya verificamos que funciona
    "taller.middleware.empresa_middleware.EmpresaMiddleware",
    # "gestion_taller.middleware.country_prefix.EnforceCountryPrefixMiddleware",  # DESHABILITADO - Causa bucles infinitos
    # "taller.middleware.country_context.CountryContextMiddleware",  # DESHABILITADO - Causa bucles infinitos con /es/
    # "taller.middleware.fix_language_middleware.FixLanguageMiddleware",  # DESHABILITADO - Causa bucles infinitos
    "taller.middleware.verificar_suscripcion.VerificarSuscripcionMiddleware",
]

# AccountMiddleware de allauth: agregar dinámicamente si existe
# Esto resuelve el problema de versiones de allauth que requieren el middleware
# pero donde el middleware no está disponible
# Usamos importlib para verificar sin importar directamente (evita AppRegistryNotReady)
import importlib.util


def check_middleware_exists(module_path):
    """Verifica si un módulo existe sin importarlo"""
    try:
        spec = importlib.util.find_spec(module_path)
        return spec is not None
    except (ImportError, ValueError, AttributeError):
        return False


# Verificar si el middleware existe sin importarlo (evita AppRegistryNotReady)
if check_middleware_exists("allauth.account.middleware"):
    # El middleware existe, agregarlo después de AuthenticationMiddleware
    # Usamos el string del middleware, Django lo importará cuando sea necesario
    try:
        auth_middleware_index = MIDDLEWARE.index(
            "django.contrib.auth.middleware.AuthenticationMiddleware"
        )
        MIDDLEWARE.insert(auth_middleware_index + 1, "allauth.account.middleware.AccountMiddleware")
    except (ValueError, IndexError):
        # Si no encontramos el middleware de autenticación, agregar al final
        MIDDLEWARE.append("allauth.account.middleware.AccountMiddleware")
else:
    # El middleware no existe, pero allauth puede requerirlo
    # Intentar desactivar la verificación si es posible (después de que Django esté listo)
    # Esto se hace en el método ready() de la app, no aquí
    pass

# Configuración de URLs
ROOT_URLCONF = "gestion_taller.urls"

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "taller.context_processors.empresa_contexto",
                "taller.context_processors.namespaces.ui_namespaces",
                "taller.context_processors.company_context",
                "taller.context_processors.company_branding",
                "taller.context_processors.company_header",
            ],
        },
    },
]

WSGI_APPLICATION = "gestion_taller.wsgi.application"

# 🌍 INTERNACIONALIZACIÓN Y LOCALIZACIÓN
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "es")  # Español por defecto (Chile)
TIME_ZONE = os.getenv("TIME_ZONE", "America/Santiago")
USE_I18N = True
USE_TZ = True

# Idiomas soportados
LANGUAGES = [
    ("es", "Español"),
    ("en", "English"),
]

# Directorio de traducciones
LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# Formatos por idioma
FORMAT_MODULE_PATH = ["gestion_taller.formats"]

# Configuración general
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
APPEND_SLASH = True

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = ["bootstrap5"]
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Autocomplete Light
AUTOCOMPLETE_LIGHT = {"SELECT2": {"i18n": False, "language": None}}

# Django Allauth
SITE_ID = 1
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)
LOGIN_REDIRECT_URL = "/login/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/login/"
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 2
ACCOUNT_RATE_LIMITS = {
    "confirm_email": "1/m",
}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]

# Configuración de sesiones
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 días
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 días

# Formulario personalizado de login
ACCOUNT_FORMS = {
    "login": "taller.forms.custom_login.CustomLoginForm",
}

# Login default
LOGIN_URL = "/accounts/login/"

# Adaptador personalizado para redirección según país
ACCOUNT_ADAPTER = "taller.views_extra.account_adapter.CountryAwareAccountAdapter"

# Email backend - Usando backend personalizado para evitar errores SMTP
EMAIL_BACKEND = "taller.backends.egarage_email.EgarageEmailBackend"
EMAIL_HOST = "srv24.cpanelhost.cl"
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = "subscription@egarage.cl"
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PASSWORD", "laila2013-")
DEFAULT_FROM_EMAIL = "eGarage <subscription@egarage.cl>"

# Logging útil (errores reales)
if SAFE_MODE:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": True,
        "handlers": {
            "null": {"class": "logging.NullHandler"},
            "console": {"class": "logging.StreamHandler", "level": "WARNING"},
        },
        "root": {"handlers": ["null"], "level": "WARNING"},
        "loggers": {
            "django": {"handlers": ["null"], "level": "WARNING", "propagate": False},
            "taller": {"handlers": ["null"], "level": "WARNING", "propagate": False},
            "django.request": {
                "handlers": ["console"],
                "level": "ERROR",
                "propagate": False,
            },
        },
    }
else:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {"console": {"class": "logging.StreamHandler"}},
        "root": {"handlers": ["console"], "level": "INFO"},
        "loggers": {
            "django.utils.autoreload": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "watchdog.observers": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "django.db.backends": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "taller": {"handlers": ["console"], "level": "INFO"},
        },
    }
