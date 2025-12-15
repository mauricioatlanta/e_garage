import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------- Seguridad / Env helpers ----------
def env_bool(key, default=False):
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(key, default=""):
    raw = os.getenv(key, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", get_random_secret_key())
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "*")  # e.g. "egarage.cl, www.egarage.cl"

# ---------- CSRF / HTTPS (solo si no estás detrás de proxy que ya haga esto) ----------
# En producción: define DJANGO_CSRF_TRUSTED_ORIGINS="https://egarage.cl, https://www.egarage.cl"
csrf_origins_env = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")
if csrf_origins_env:
    CSRF_TRUSTED_ORIGINS = [h if h.startswith("http") else f"https://{h}" for h in csrf_origins_env]
else:
    CSRF_TRUSTED_ORIGINS = []
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", not DEBUG)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_HTTPONLY = False  # Permitir acceso desde JavaScript si es necesario
CSRF_COOKIE_SAMESITE = "Lax"  # Más permisivo para desarrollo
CSRF_USE_SESSIONS = False  # Usar cookies en lugar de sesiones para CSRF
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "0" if DEBUG else "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", not DEBUG)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", not DEBUG)
SECURE_REFERRER_POLICY = os.getenv(
    "DJANGO_SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin"
)
X_FRAME_OPTIONS = os.getenv("DJANGO_X_FRAME_OPTIONS", "DENY")

# ---------- Proxy / HTTPS detrás de reverse proxy ----------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# ---------- CSRF trusted desde ALLOWED_HOSTS si no se define explícito ----------
# (Movido al final del archivo)

# ---------- Sites / Allauth ----------
SITE_ID = 1
SITE_NAME = "eGarage"
SITE_DOMAIN = "egarage.cl"

ACCOUNT_ADAPTER = "taller.views_extra.account_adapter.CountryAwareAccountAdapter"
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

# Allauth correcto
ACCOUNT_AUTHENTICATION_METHOD = "username_email"  # <- en vez de ACCOUNT_LOGIN_METHODS
ACCOUNT_EMAIL_VERIFICATION = os.getenv(
    "ACCOUNT_EMAIL_VERIFICATION",
    "mandatory",  # 🔒 Siempre obligatorio
)
ACCOUNT_EMAIL_REQUIRED = True  # 🔒 Email es REQUERIDO
ACCOUNT_CONFIRM_EMAIL_ON_GET = True  # Confirmar email con un solo clic
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 2
ACCOUNT_RATE_LIMITS = {"confirm_email": "1/m"}

ACCOUNT_FORMS = {
    "login": "taller.forms.custom_login.CustomLoginForm",
    # "signup": "taller.forms.custom_signup.CustomSignupForm",  # <- si quieres controlar campos
}

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"  # <- Enviar a home o dashboard country-aware
ACCOUNT_LOGOUT_REDIRECT_URL = "/logout-redirect/"

# ---------- Apps ----------
INSTALLED_APPS = [
    # 3rd
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dal",
    "dal_select2",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_extensions",
    "django.contrib.humanize",
    "widget_tweaks",
    "rest_framework",
    # Project
    "taller.apps.TallerConfig",
    "ubicacion.apps.UbicacionConfig",
    # Django contrib
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = ["bootstrap5"]
CRISPY_TEMPLATE_PACK = "bootstrap5"

AUTOCOMPLETE_LIGHT = {"SELECT2": {"i18n": False, "language": None}}

# ---------- DRF mínimos seguros ----------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}

# ---------- Static / WhiteNoise (opcional si no usas CDN) ----------
# if env_bool("DJANGO_WHITENOISE", not DEBUG):
#     MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
#     STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ---------- Middleware (reorden menor sugerido) ----------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # LocaleMiddleware debe ir DESPUÉS de SessionMiddleware
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # País/empresa (provee request.empresa / request.empresa.pais)
    "taller.middleware.empresa_middleware.EmpresaMiddleware",
    "taller.middleware.simple_country_redirect.SimpleCountryRedirectMiddleware",
    # Idioma (nuevo): decide idioma final por país y preferencia usuario
    "taller.middleware.lang_policy.LanguagePolicyMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Suscripción / trial (después de auth + allauth)
    "taller.middleware.verificar_suscripcion.VerificarSuscripcionMiddleware",
    # "taller.middleware.trial_middleware.TrialAccessMiddleware",
]

# AccountMiddleware de allauth: agregar dinámicamente si existe
# Esto resuelve el problema de versiones de allauth que requieren el middleware
# pero donde el middleware no está disponible
try:
    from allauth.account.middleware import AccountMiddleware

    # El middleware existe, agregarlo después de AuthenticationMiddleware
    auth_middleware_index = MIDDLEWARE.index(
        "django.contrib.auth.middleware.AuthenticationMiddleware"
    )
    MIDDLEWARE.insert(auth_middleware_index + 1, "allauth.account.middleware.AccountMiddleware")
except ImportError:
    # El middleware no existe, pero allauth puede requerirlo
    # Intentar desactivar la verificación si es posible
    try:
        import allauth.account.apps

        # Monkey patch para desactivar la verificación del middleware (solo una vez)
        if not hasattr(allauth.account.apps.AccountConfig.ready, "_patched_for_middleware"):
            original_ready = allauth.account.apps.AccountConfig.ready

            def patched_ready(self):
                # Verificar si el middleware está en MIDDLEWARE antes de lanzar error
                try:
                    from allauth.account.middleware import AccountMiddleware

                    # Si el middleware existe, usar la verificación original
                    return original_ready(self)
                except ImportError:
                    # El middleware no existe, omitir la verificación
                    pass

            patched_ready._patched_for_middleware = True
            allauth.account.apps.AccountConfig.ready = patched_ready
    except Exception:
        # Si falla el monkey patch, continuar sin el middleware
        pass

# ---------- URLs / WSGI ----------
ROOT_URLCONF = "gestion_taller.urls"
WSGI_APPLICATION = "gestion_taller.wsgi.application"

# ---------- Templates ----------
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

# ---------- DB ----------
if os.getenv("DATABASE_URL"):
    import dj_database_url

    DATABASES = {"default": dj_database_url.parse(os.getenv("DATABASE_URL"), conn_max_age=600)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---------- i18n / l10n ----------
LANGUAGE_CODE = "es"  # fallback global
LANGUAGES = [("en", "English"), ("es", "Español")]
LOCALE_PATHS = [BASE_DIR / "locale"]
FORMAT_MODULE_PATH = ["gestion_taller.formats"]
USE_I18N = True
USE_TZ = True

# ---------- Static / Media ----------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
APPEND_SLASH = True

# ---------- Dev helpers ----------
if DEBUG:
    import mimetypes

    mimetypes.add_type("text/css", ".css", True)
    mimetypes.add_type("application/javascript", ".js", True)

# ---------- Sesiones ----------
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 días
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
ACCOUNT_SESSION_REMEMBER = True
# (Django usa SESSION_COOKIE_AGE; no necesitas ACCOUNT_SESSION_COOKIE_AGE)

# ---------- Email ----------
EMAIL_BACKEND = "taller.backends.egarage_email.EgarageEmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "srv24.cpanelhost.cl")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", True)
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "subscription@egarage.cl")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "eGarage <subscription@egarage.cl>")

# En dev, evita KeyError; en prod exige la var.
_email_pwd = os.getenv("EMAIL_PASSWORD")
if _email_pwd:
    EMAIL_HOST_PASSWORD = _email_pwd
elif DEBUG:
    EMAIL_HOST_PASSWORD = "laila2013-"  # Nueva contraseña ASCII
else:
    raise RuntimeError("EMAIL_PASSWORD must be set in production")

# ---------- Logging básico ----------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO" if not DEBUG else "DEBUG"},
    "loggers": {
        "django.security.DisallowedHost": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# ---------- Extra headers ----------
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_CONTENT_TYPE_NOSNIFF = True

# ---------- CSRF trusted desde ALLOWED_HOSTS si no se define explícito ----------
if len(CSRF_TRUSTED_ORIGINS) == 0:
    if DEBUG:
        # En desarrollo, agregar localhost y 127.0.0.1
        CSRF_TRUSTED_ORIGINS = [
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ]
    else:
        CSRF_TRUSTED_ORIGINS = [
            f"https://{h}" for h in ALLOWED_HOSTS if h not in {"*", "localhost", "127.0.0.1"}
        ]

# ---------- Branding Defaults ----------
# Fallbacks amables para cuando no hay empresa configurada
DEFAULT_BRAND_LOGO_URL = "/static/branding/egarage_logo.svg"
DEFAULT_BRAND_NAME = "eGarage"
DEFAULT_BRAND_TAGLINE = "Control total para tu taller"
DEFAULT_BRAND_COUNTRY = "cl"
DEFAULT_BRAND_CURRENCY = "CLP"
DEFAULT_BRAND_PRIMARY_COLOR = "#0d6efd"
DEFAULT_BRAND_SECONDARY_COLOR = "#6c757d"
