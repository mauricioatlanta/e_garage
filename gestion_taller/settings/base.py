"""
Configuración base para eGarage - Sistema de Gestión de Taller
Configuración común para todos los entornos (dev, prod, local)
"""

import os
from pathlib import Path
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

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

# Middleware común
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "taller.middleware.country_url_migration.CountryURLRedirectMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Empresa + País
    "taller.middleware.empresa_middleware.EmpresaMiddleware",
    "gestion_taller.middleware.country_prefix.EnforceCountryPrefixMiddleware",
    "taller.middleware.country_context.CountryContextMiddleware",
    # Idioma (elige SOLO una)
    "taller.middleware.fix_language_middleware.FixLanguageMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    # Suscripción / trial
    "taller.middleware.verificar_suscripcion.VerificarSuscripcionMiddleware",
]

# Configuración de URLs
ROOT_URLCONF = "gestion_taller.urls"

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates_canonical"],
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
USE_L10N = True
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

# Email backend
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "mail.atlantareciclajes.cl"
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = "suscripcion@atlantareciclajes.cl"
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PASSWORD", ",*naHZ0xIFO")
DEFAULT_FROM_EMAIL = "eGarage <suscripcion@atlantareciclajes.cl>"

# Logging base
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
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
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
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
