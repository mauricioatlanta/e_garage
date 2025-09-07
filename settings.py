# Configuración para django.contrib.sites
SITE_ID = 1
import os
from pathlib import Path

from decouple import config
from django.core.management.utils import get_random_secret_key

# BASE DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# 🔐 Seguridad
SECRET_KEY = config("DJANGO_SECRET_KEY", default=get_random_secret_key())
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

# 🔐 Seguridad extra en producción
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG

# 🧩 Aplicaciones instaladas
INSTALLED_APPS = [
    "dal",
    "dal_select2",
    "core",  # App para funcionalidades compartidas y commands
    "taller",
    # Apps Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Allauth y dependencias
    "django.contrib.sites",
    # Allauth y dependencias
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
]

# Configuración de sitios para allauth
SITE_ID = 1

# 🧱 Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "taller.middleware.force_english_usa.ForceEnglishUSA",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "gestion_taller.middleware.country_prefix.EnforceCountryPrefixMiddleware",  # 🚀 BISTURÍ: Corrección automática de prefijo
    "taller.middleware.verificar_suscripcion.VerificarSuscripcionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "taller.middleware.empresa_middleware.EmpresaMiddleware",
    "taller.middleware.suscripcion.SuscripcionMiddleware",
]

# 🌐 URLs
ROOT_URLCONF = "e_garage.urls"

# 🧠 Plantillas
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
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.static_version",
                "core.context_processors.empresa_info",
                "taller.context_processors.empresa_context",
            ],
        },
    },
]

# 🚀 WSGI
WSGI_APPLICATION = "gestion_taller.wsgi.application"

# 🗃️ Base de datos
DATABASES = {
    "default": {
        "ENGINE": config("DJANGO_DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": config("DJANGO_DB_NAME", default=BASE_DIR / "db.sqlite3"),
        "USER": config("DJANGO_DB_USER", default=""),
        "PASSWORD": config("DJANGO_DB_PASSWORD", default=""),
        "HOST": config("DJANGO_DB_HOST", default=""),
        "PORT": config("DJANGO_DB_PORT", default=""),
    }
}


# 🌍 Internacionalización
LANGUAGE_CODE = "en-us"
LANGUAGES = [
    ("en", "English"),
    ("es", "Español"),
]
LOCALE_PATHS = [
    BASE_DIR / "locale",
]
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_L10N = True
USE_TZ = True
THOUSAND_SEPARATOR = "."
USE_THOUSAND_SEPARATOR = True

# 📁 Archivos estáticos y media
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 🔧 Config extra
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
APPEND_SLASH = True

# ✅ Redirecciones de autenticación
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"


# Configuración de correo para pruebas con Gmail
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "mail.atlantareciclajes.cl"
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = "suscripcion@atlantareciclajes.cl"
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_PASSWORD")  # pon la clave en .env
DEFAULT_FROM_EMAIL = "eGarage <suscripcion@atlantareciclajes.cl>"


# 🧾 Logging
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
        "level": "DEBUG" if DEBUG else "INFO",
    },
}
