import os
import logging
from pathlib import Path

# ---------- CRÍTICO: Importar parche de base de datos ANTES de cualquier otra cosa ----------
# Esto debe ejecutarse ANTES de cargar dotenv o importar Django
# para asegurar que PGSSLMODE se establezca antes de que psycopg2 sea importado
try:
    # Importar el módulo (esto ejecuta el código de nivel superior que establece PGSSLMODE)
    import gestion_taller.db_patch
    from gestion_taller.db_patch import patch_postgresql_backend

    _PATCH_AVAILABLE = True
except ImportError:
    # Si el archivo no existe aún, crear función dummy
    def patch_postgresql_backend():
        return False

    _PATCH_AVAILABLE = False

from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

# ---------- Paths (debe estar antes de load_dotenv) ----------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------- Cargar Variables de Entorno ----------
# Cargar .env.local si existe (para desarrollo local), sino .env
# Esto permite tener configuraciones separadas para local y producción
_env_local_path = BASE_DIR / ".env.local"
_env_path = BASE_DIR / ".env"

if _env_local_path.exists():
    load_dotenv(_env_local_path, override=True)
elif _env_path.exists():
    load_dotenv(_env_path, override=True)
else:
    # Si no existe ningún .env, cargar el que encuentre dotenv
    load_dotenv()

# ---------- FIX SSL para PostgreSQL localhost ----------
# CRÍTICO: Establecer PGSSLMODE=disable ANTES de cualquier importación de Django/psycopg2
# Esto evita que psycopg2 intente usar SSL con servidores locales que no lo soportan
# Verificamos si estamos usando PostgreSQL localhost y desactivamos SSL
_db_url = os.getenv("DATABASE_URL", "")
_db_host = os.getenv("DJANGO_DB_HOST") or os.getenv("DB_HOST", "")

# Verificar si es localhost desde DATABASE_URL
_is_localhost = False
if _db_url and ("postgres" in _db_url.lower() or "postgresql" in _db_url.lower()):
    import urllib.parse

    try:
        _parsed = urllib.parse.urlparse(_db_url)
        _host = _parsed.hostname or ""
        if (
            _host.lower() in ("localhost", "127.0.0.1", "::1")
            or not _host
            or "localhost" in str(_host).lower()
        ):
            _is_localhost = True
    except Exception:
        pass

# Verificar si es localhost desde variables de entorno individuales
if not _is_localhost and _db_host:
    if _db_host.lower() in ("localhost", "127.0.0.1", "::1") or not _db_host:
        _is_localhost = True

# También verificar si hay DB_NAME configurado (indica que usaremos PostgreSQL)
# y si el host es localhost
_db_name = os.getenv("DJANGO_DB_NAME") or os.getenv("DB_NAME", "")
if not _is_localhost and _db_name:
    # Si hay nombre de BD pero no URL, verificar el host
    _check_host = os.getenv("DJANGO_DB_HOST") or os.getenv("DB_HOST", "127.0.0.1")
    if _check_host.lower() in ("localhost", "127.0.0.1", "::1") or not _check_host:
        _is_localhost = True

# Si es localhost, desactivar SSL INMEDIATAMENTE
# Esto debe hacerse antes de que psycopg2 sea importado
if _is_localhost:
    os.environ["PGSSLMODE"] = "disable"
    # También establecer otras variables relacionadas con SSL
    os.environ.setdefault("PGSSL", "0")

# ---------- Paths ----------
# BASE_DIR debe estar ANTES de load_dotenv para poder usarlo en la carga de .env
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------- Seguridad / Env helpers ----------
def env_bool(key, default=False):
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str | list[str] = "") -> list[str]:
    # Si default es una lista, convertirla a string separado por comas
    if isinstance(default, list):
        default = ",".join(default)
    raw = os.getenv(name, default) or ""
    return [x.strip() for x in raw.split(",") if x.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", get_random_secret_key())

# ✅ FIX: usar env_bool (evita errores por "True"/"False")
DEBUG = env_bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    [
        "127.0.0.1",
        "localhost",
        "159.223.200.106",
        "egarage.cl",
        "www.egarage.cl",
        "garage.cl",
        "www.garage.cl",
    ],
)

# ---------- CSRF / HTTPS ----------
# 3. Configura los dominios permitidos para evitar errores 403 al loguear
# IMPORTANTE: Los dominios deben llevar el https:// inicial
CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    ["https://egarage.cl", "https://www.egarage.cl"],
)

# 3. Solo para probar el acceso ahora (puedes activarlos después)
# Desactivados por defecto para evitar ERR_TOO_MANY_REDIRECTS cuando hay proxy
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", False)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", False)

# Si realmente necesitas leer CSRF desde JS, déjalo False.
# (Muchos sitios lo ponen True para reducir superficie, pero depende de tu frontend)
CSRF_COOKIE_HTTPONLY = env_bool("DJANGO_CSRF_COOKIE_HTTPONLY", False)

# ❌ APÁGALO por ahora - Desactiva la redirección automática de Django
# Cuando Nginx/Cloudflare maneja HTTPS y Django está detrás del proxy, esta debe ser False
SECURE_SSL_REDIRECT = False

CSRF_COOKIE_SAMESITE = os.getenv("DJANGO_CSRF_COOKIE_SAMESITE", "Lax")
CSRF_USE_SESSIONS = env_bool("DJANGO_CSRF_USE_SESSIONS", False)

# ✅ FIX: HSTS seguro por defecto (no irreversible)
# - Por defecto: 1 hora en producción
# - IncludeSubdomains/preload: apagados salvo que lo actives explícitamente
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "0" if DEBUG else "3600"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", False)

SECURE_REFERRER_POLICY = os.getenv(
    "DJANGO_SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin"
)
X_FRAME_OPTIONS = os.getenv("DJANGO_X_FRAME_OPTIONS", "DENY")

# ---------- Proxy / HTTPS detrás de reverse proxy ----------
# 🔥 OBLIGATORIO detrás de Cloudflare - Avisa a Django que está detrás de un proxy que ya maneja HTTPS
# Esta configuración es CRÍTICA para evitar bucles de redirección cuando hay un proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# ---------- Sites / Allauth ----------
SITE_ID = 1
SITE_NAME = "eGarage"
SITE_DOMAIN = "egarage.cl"

ACCOUNT_ADAPTER = "taller.views_extra.account_adapter.CountryAwareAccountAdapter"
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "taller.backends.email_phone_auth.EmailOrPhoneBackend",  # Permite login por email o teléfono
    "allauth.account.auth_backends.AuthenticationBackend",
)

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "mandatory")
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 2
ACCOUNT_RATE_LIMITS = {"confirm_email": "1/m"}

ACCOUNT_FORMS = {
    "login": "taller.forms.custom_login.CustomLoginForm",
    "signup": "taller.forms.custom_signup.CustomSignupForm",
}

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/logout-redirect/"
# Permitir logout por GET: evita 403 CSRF al visitar /accounts/logout/ directamente
ACCOUNT_LOGOUT_ON_GET = True

# ---------- eGarage país e idioma por defecto ----------
# Si alguien entra por /accounts/login/ (ruta sin país), el fallback es Chile, no Uruguay.
# Uruguay solo accesible vía /uy/...; login/signup solo vía rutas país.
EGARAGE_DEFAULT_COUNTRY = "cl"
EGARAGE_DEFAULT_LANG = "es"
# Alias para middleware/context que usan getattr(settings, "DEFAULT_COUNTRY", "CL")
DEFAULT_COUNTRY = "CL"

# ---------- Feature Flags ----------
# Marketplace feature flag - deshabilitado por defecto
# Activar cuando el módulo esté completamente listo
EGARAGE_ENABLE_MARKETPLACE = env_bool("EGARAGE_ENABLE_MARKETPLACE", False)

# ---------- Apps ----------
INSTALLED_APPS = [
    # Project (debe ir primero para que el AppConfig se ejecute temprano)
    "gestion_taller.apps.GestionTallerConfig",  # Aplica parche SSL para PostgreSQL localhost
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
    "taller.whatsapp.apps.WhatsappConfig",  # WhatsApp admin notifications and click-to-WhatsApp
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

# Agregar marketplace condicionalmente si el feature flag está habilitado
if EGARAGE_ENABLE_MARKETPLACE:
    INSTALLED_APPS.append("marketplace.apps.MarketplaceConfig")

CRISPY_ALLOWED_TEMPLATE_PACKS = ["bootstrap5"]
CRISPY_TEMPLATE_PACK = "bootstrap5"

AUTOCOMPLETE_LIGHT = {"SELECT2": {"i18n": False, "language": None}}

# ---------- DRF mínimos seguros ----------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}

# ---------- Middleware ----------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "taller.middleware.force_accounts_to_cl.ForceAccountsToCLMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "taller.middleware.rate_limiting.RateLimitMiddleware",
    "taller.middleware.empresa_middleware.EmpresaMiddleware",
    "taller.middleware.onboarding_middleware.OnboardingMiddleware",
    "taller.middleware.simple_country_redirect.SimpleCountryRedirectMiddleware",
    "taller.middleware.lang_policy.LanguagePolicyMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# AccountMiddleware de allauth: agregar dinámicamente si existe
try:
    from allauth.account.middleware import AccountMiddleware

    auth_middleware_index = MIDDLEWARE.index(
        "django.contrib.auth.middleware.AuthenticationMiddleware"
    )
    MIDDLEWARE.insert(auth_middleware_index + 1, "allauth.account.middleware.AccountMiddleware")
except ImportError:
    try:
        import allauth.account.apps

        if not hasattr(allauth.account.apps.AccountConfig.ready, "_patched_for_middleware"):
            original_ready = allauth.account.apps.AccountConfig.ready

            def patched_ready(self):
                try:
                    from allauth.account.middleware import AccountMiddleware  # noqa: F401

                    return original_ready(self)
                except ImportError:
                    pass

            patched_ready._patched_for_middleware = True
            allauth.account.apps.AccountConfig.ready = patched_ready
    except Exception:
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
                "taller.context_processors.country.country_context",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "taller.context_processors.country.country_context",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "taller.context_processors.country.country_context",
                "taller.context_processors.empresa_contexto",
                "taller.context_processors.namespaces.ui_namespaces",
                "taller.context_processors.company_context",
                "taller.context_processors.company_branding",
                "taller.context_processors.company_country",
                "taller.context_processors.company_header",
                "taller.context_processors.panel_chrome.us_authenticated_compact_chrome",
                "taller.context_processors.panel_chrome.us_signup_slim_header",
                "taller.context_processors.country_config.country_context",
                "taller.context_processors.feature_flags.country_features",
                "taller.context_processors.ui_labels.ui_labels_context",
                "taller.context_processors.support_context",
                "taller.context_processors.ayuda_contextual.ayuda_contextual",
            ],
        },
    },
]

# ---------- DB ----------
# Base de datos - PostgreSQL si hay DATABASE_URL, SQLite por defecto
if os.getenv("DATABASE_URL"):
    database_url = os.getenv("DATABASE_URL")

    # Si es PostgreSQL y es localhost, agregar sslmode=disable a la URL
    if "postgres" in database_url.lower() or "postgresql" in database_url.lower():
        import urllib.parse

        parsed_url = urllib.parse.urlparse(database_url)

        # Verificar si es localhost
        hostname = parsed_url.hostname or ""
        is_localhost = hostname.lower() in ("localhost", "127.0.0.1", "::1") or not hostname

        if is_localhost:
            # Agregar sslmode=disable a la URL si no está presente
            if "sslmode" not in database_url.lower():
                separator = "&" if "?" in database_url else "?"
                database_url = f"{database_url}{separator}sslmode=disable"

            # Usar dj_database_url si está disponible, pero forzar sslmode=disable
            try:
                import dj_database_url

                db_config = dj_database_url.parse(database_url, conn_max_age=600)
                # Asegurar que OPTIONS tenga sslmode=disable
                if "OPTIONS" not in db_config:
                    db_config["OPTIONS"] = {}
                db_config["OPTIONS"]["sslmode"] = "disable"
                db_config["OPTIONS"]["client_encoding"] = "UTF8"
                # Forzar host a 127.0.0.1
                db_config["HOST"] = "127.0.0.1"
                DATABASES = {"default": db_config}
            except ImportError:
                # Si dj_database_url no está instalado, parsear manualmente
                username = urllib.parse.unquote(parsed_url.username or "")
                password = urllib.parse.unquote(parsed_url.password or "")
                hostname = "127.0.0.1"  # Forzar IPv4
                port = parsed_url.port or 5432
                database = urllib.parse.unquote(parsed_url.path.lstrip("/") or "")

                DATABASES = {
                    "default": {
                        "ENGINE": "django.db.backends.postgresql",
                        "NAME": database,
                        "USER": username,
                        "PASSWORD": password,
                        "HOST": hostname,
                        "PORT": port,
                        "OPTIONS": {
                            "sslmode": "disable",
                            "client_encoding": "UTF8",
                        },
                        "CONN_MAX_AGE": 600,
                    }
                }
        else:
            # Para hosts remotos, usar dj_database_url normalmente
            try:
                import dj_database_url

                DATABASES = {"default": dj_database_url.parse(database_url, conn_max_age=600)}
            except ImportError:
                # Parsear manualmente
                username = urllib.parse.unquote(parsed_url.username or "")
                password = urllib.parse.unquote(parsed_url.password or "")
                hostname = parsed_url.hostname or "127.0.0.1"
                port = parsed_url.port or 5432
                database = urllib.parse.unquote(parsed_url.path.lstrip("/") or "")

                DATABASES = {
                    "default": {
                        "ENGINE": "django.db.backends.postgresql",
                        "NAME": database,
                        "USER": username,
                        "PASSWORD": password,
                        "HOST": hostname,
                        "PORT": port,
                        "CONN_MAX_AGE": 600,
                    }
                }
    else:
        # No es PostgreSQL, usar dj_database_url normalmente
        try:
            import dj_database_url

            DATABASES = {"default": dj_database_url.parse(database_url, conn_max_age=600)}
        except ImportError:
            # Fallback a SQLite si no se puede parsear
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": BASE_DIR / "db.sqlite3",
                }
            }
elif os.getenv("DJANGO_DB_NAME") or os.getenv("DB_NAME"):
    # PostgreSQL con configuración desde variables de entorno individuales
    db_host = os.getenv("DJANGO_DB_HOST") or os.getenv(
        "DB_HOST", "127.0.0.1"
    )  # Default a 127.0.0.1, no localhost
    # CRÍTICO: Forzar IPv4 para localhost (evita problemas con IPv6 y SSL)
    # localhost puede resolverse a ::1 (IPv6) que puede tener problemas con SSL
    # NUNCA usar "localhost" como string, siempre usar "127.0.0.1"
    if db_host.lower() in ("localhost", "::1", "0.0.0.0") or not db_host:
        db_host = "127.0.0.1"

    # Determinar si debemos desactivar SSL (para localhost)
    is_localhost = db_host == "127.0.0.1" or db_host.lower() in ("localhost", "127.0.0.1")

    # Establecer variable de entorno ANTES de construir la configuración
    # Esto asegura que psycopg2 la use desde el inicio
    if is_localhost:
        os.environ["PGSSLMODE"] = "disable"
        # También establecerlo como variable de entorno de PostgreSQL
        os.environ["PGSSL"] = "0"

    # Construir configuración de base de datos
    # CRÍTICO: Siempre usar 127.0.0.1 explícitamente para localhost (nunca "localhost")
    # Esto evita que psycopg2 resuelva a IPv6 (::1) que puede tener problemas con SSL
    db_config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DJANGO_DB_NAME") or os.getenv("DB_NAME"),
        "USER": os.getenv("DJANGO_DB_USER") or os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD") or os.getenv("DB_PASSWORD"),
        "HOST": db_host,  # Ya está forzado a 127.0.0.1 si es localhost
        "PORT": os.getenv("DJANGO_DB_PORT") or os.getenv("DB_PORT", "5432"),
    }

    # Configurar SSL solo si no es localhost
    # Para localhost, desactivar SSL explícitamente en OPTIONS también
    if is_localhost:
        # Para localhost, desactivar SSL explícitamente
        # CRÍTICO: Asegurar que OPTIONS tenga sslmode=disable ANTES de cualquier conexión
        db_config["OPTIONS"] = {
            "sslmode": "disable",
            "client_encoding": "UTF8",
        }
        # Asegurar que la variable de entorno esté establecida ANTES de importar psycopg2
        os.environ["PGSSLMODE"] = "disable"
        os.environ.setdefault("PGSSL", "0")
    else:
        db_config["OPTIONS"] = {
            "sslmode": "prefer",  # Preferir SSL pero no requerirlo para hosts remotos
            "client_encoding": "UTF8",
        }

    DATABASES = {"default": db_config}
else:
    # SQLite por defecto
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # Ruta relativa al proyecto
        }
    }

# ---------- i18n / l10n ----------
LANGUAGE_CODE = "es"
LANGUAGES = [("en", "English"), ("es", "Español")]
LOCALE_PATHS = [BASE_DIR / "locale"]
FORMAT_MODULE_PATH = ["gestion_taller.formats"]
USE_I18N = True
USE_TZ = True

# ---------- Static / Media ----------
# CRÍTICO: STATIC_URL debe estar definido ANTES de STORAGES
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = Path(os.getenv("STATIC_ROOT", str(BASE_DIR / "staticfiles")))

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))

# ---------- STORAGES (Django 5) ----------
# Configuración de almacenamiento para archivos estáticos y media
# IMPORTANTE: STATIC_URL y MEDIA_URL deben estar definidos ANTES de STORAGES
if not DEBUG:
    # Producción: usar WhiteNoise para staticfiles
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_AUTOREFRESH = False
else:
    # Desarrollo: usar almacenamiento estándar
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
    }
# Django 5+: no definir STATICFILES_STORAGE si ya existe STORAGES["staticfiles"] (mutuamente excluyentes).

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
APPEND_SLASH = True

# ---------- Dev helpers ----------
if DEBUG:
    import mimetypes

    mimetypes.add_type("text/css", ".css", True)
    mimetypes.add_type("application/javascript", ".js", True)

# ---------- Sesiones ----------
# ✅ IMPORTANTE: SESSION_ENGINE por defecto es "django.contrib.sessions.backends.db"
# En producción (settings/prod.py) se usa DB explícitamente para evitar problemas
# con múltiples workers de Gunicorn (LocMemCache no es compartido entre workers)
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
ACCOUNT_SESSION_REMEMBER = True

# ---------- Support Information (Single Source of Truth) ----------
SUPPORT_EMAIL = "support@egarage.cl"
SUPPORT_WHATSAPP_E164 = "+56953574683"
SUPPORT_WHATSAPP_DISPLAY = "+56 9 5357 4683"
SUPPORT_WHATSAPP_WA_ME = "56953574683"

# ---------- WhatsApp Admin Notifications ----------
# Notificaciones WhatsApp para admin de eGarage (nuevas suscripciones/renovaciones)
WHATSAPP_ADMIN_NOTIFICATIONS_ENABLED = env_bool("WHATSAPP_ADMIN_NOTIFICATIONS_ENABLED", False)
WHATSAPP_ADMIN_PROVIDER = os.getenv("WHATSAPP_ADMIN_PROVIDER", "dummy")  # "dummy" | "meta"
WHATSAPP_ADMIN_NUMBER = os.getenv("WHATSAPP_ADMIN_NUMBER", "+56953574683")
# Credenciales Meta Cloud API (solo si provider="meta")
WHATSAPP_ADMIN_PHONE_NUMBER_ID = os.getenv("WHATSAPP_ADMIN_PHONE_NUMBER_ID", None)
WHATSAPP_ADMIN_ACCESS_TOKEN = os.getenv("WHATSAPP_ADMIN_ACCESS_TOKEN", None)

# ---------- Email ----------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "srv24.cpanelhost.cl"
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = SUPPORT_EMAIL
DEFAULT_FROM_EMAIL = f"eGarage <{SUPPORT_EMAIL}>"
EMAIL_TIMEOUT = 30

_email_pwd = os.getenv("EMAIL_HOST_PASSWORD")
if _email_pwd:
    EMAIL_HOST_PASSWORD = _email_pwd
elif DEBUG:
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
    if not EMAIL_HOST_PASSWORD:
        logger = logging.getLogger(__name__)
        logger.warning("EMAIL_HOST_PASSWORD not set - email functionality will not work")
else:
    raise RuntimeError("EMAIL_HOST_PASSWORD must be set in production (check .env file)")

# ---------- Sentry ----------
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN and not DEBUG:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        )

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(
                    transaction_style="url",
                    middleware_spans=True,
                    signals_spans=True,
                    cache_spans=True,
                ),
                sentry_logging,
            ],
            traces_sample_rate=0.1,
            send_default_pii=False,
            environment="production",
            release=os.getenv("SENTRY_RELEASE", "egarage@unknown"),
            before_send=lambda event, hint: event,
        )
        logger = logging.getLogger(__name__)
        logger.info("✅ Sentry initialized successfully")
    except ImportError:
        logger = logging.getLogger(__name__)
        logger.warning(
            "⚠️ Sentry DSN configured but sentry-sdk not installed. Run: pip install sentry-sdk"
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Failed to initialize Sentry: {e}")

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


# ---------- Branding Defaults ----------
DEFAULT_BRAND_LOGO_URL = "/static/branding/egarage_logo.svg"
DEFAULT_BRAND_NAME = "eGarage"
DEFAULT_BRAND_TAGLINE = "Control total para tu taller"
DEFAULT_BRAND_COUNTRY = "cl"
DEFAULT_BRAND_CURRENCY = "CLP"
DEFAULT_BRAND_PRIMARY_COLOR = "#0d6efd"
DEFAULT_BRAND_SECONDARY_COLOR = "#6c757d"

# ---------- Admin Audit Configuration ----------
ADMIN_AUDIT_PHONE = os.getenv("ADMIN_AUDIT_PHONE", "+56963607348")

# ---------- FIX SSL para PostgreSQL localhost (Configuración Final) ----------
# CRÍTICO: Verificar y forzar configuración SSL después de que DATABASES está configurado
if DATABASES.get("default", {}).get("ENGINE") == "django.db.backends.postgresql":
    db_default = DATABASES["default"]
    db_host = db_default.get("HOST", "")

    # Si es localhost (127.0.0.1), forzar sslmode=disable en OPTIONS
    if db_host in ("127.0.0.1", "localhost") or not db_host or db_host == "":
        # Forzar HOST a 127.0.0.1 explícitamente (nunca usar "localhost")
        # Esto evita que psycopg2 resuelva a IPv6 (::1)
        db_default["HOST"] = "127.0.0.1"

        # Asegurar que OPTIONS existe y tiene sslmode=disable
        if "OPTIONS" not in db_default:
            db_default["OPTIONS"] = {}

        # Forzar sslmode=disable explícitamente
        db_default["OPTIONS"]["sslmode"] = "disable"

        # También establecer variable de entorno como respaldo
        # Esto se hace ANTES de que psycopg2 sea importado
        os.environ["PGSSLMODE"] = "disable"
        os.environ.setdefault("PGSSL", "0")

        # Aplicar monkey patch al backend de PostgreSQL
        # Esto se hace después de que DATABASES está configurado pero ANTES de que Django intente conectarse
        # IMPORTANTE: Aplicar el parche inmediatamente, no esperar a que se cree la conexión
        if _PATCH_AVAILABLE:
            try:
                # Aplicar el parche de forma inmediata
                # Esto interceptará get_connection_params y get_new_connection antes de que psycopg2 construya el DSN
                patch_applied = patch_postgresql_backend()
                if patch_applied:
                    import logging

                    logger = logging.getLogger(__name__)
                    if DEBUG:
                        logger.info("✅ Parche SSL aplicado correctamente para conexiones locales")
                else:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        "⚠️ No se pudo aplicar parche SSL. Usando configuración OPTIONS estándar."
                    )
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"⚠️ Error al aplicar parche SSL: {e}. Usando configuración OPTIONS estándar."
                )
