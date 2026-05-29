# gestion_taller/settings_prod.py
import os
from pathlib import Path

from dotenv import load_dotenv

from .settings import *  # noqa: F401,F403

# Cargar .env.prod de forma explícita para entornos que no exportan variables
_env_prod_path = Path(__file__).resolve().parent.parent / ".env.prod"
if _env_prod_path.exists():
    load_dotenv(_env_prod_path, override=True)

# Permitir override desde .env gitignored para secretos rotados localmente/servidor.
_env_override_path = Path(__file__).resolve().parent.parent / ".env"
if _env_override_path.exists():
    load_dotenv(_env_override_path, override=True)


# =============================================================================
# STATIC / MEDIA
# =============================================================================
STATIC_URL = "/static/"
STATIC_ROOT = os.getenv("STATIC_ROOT", "/srv/egarage/staticfiles")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/srv/egarage/media")


# =========================
# Helpers de entorno
Environment = "DJANGO_SETTINGS_MODULE=gestion_taller.settings_prod"


def env_str(key: str, default: str = "") -> str:
    v = os.getenv(key, default)
    return (v or "").strip()


def env_bool(key: str, default: bool = False) -> bool:
    return env_str(key, str(default)).lower() in {"1", "true", "yes", "on"}


def env_int(key: str, default: int = 0) -> int:
    raw = env_str(key, str(default))
    try:
        return int(raw)
    except ValueError:
        return int(default)


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default) or ""
    return [x.strip() for x in raw.split(",") if x.strip()]


# =========================
# Debug
# =========================
DEBUG = env_bool("DJANGO_DEBUG", False)


# =========================
# Hosts / CSRF
# =========================
# Fuente de verdad: DJANGO_ALLOWED_HOSTS en .env.prod (o variable de entorno).
# Para acceso directo por IP debe incluir la IP del servidor (ej. 159.223.200.106).
ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "egarage.cl,www.egarage.cl,atlantareciclajes.cl,www.atlantareciclajes.cl,localhost,127.0.0.1,159.223.200.106",
)

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "https://egarage.cl,https://www.egarage.cl,https://atlantareciclajes.cl,https://www.atlantareciclajes.cl",
)


# =========================
# HTTPS detrás de proxy (Nginx / DigitalOcean)
# =========================
# 🔥 IMPRESCINDIBLE: Configuración fija para producción (no controlada por env)
# Este header es CRÍTICO cuando Django está detrás de un proxy (Nginx, Cloudflare, etc.)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env_bool("DJANGO_USE_X_FORWARDED_HOST", True)

# 🔥 IMPRESCINDIBLE: Fijo en True para producción (requiere SECURE_PROXY_SSL_HEADER arriba)
# ⚠️ TEMPORAL: Si aún no tienes certificado SSL instalado, cambia esto a False
# o configura DJANGO_SECURE_SSL_REDIRECT=false en .env
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", True)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", True)

# Recomendado en producción (evita robo de cookie por JS)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # normalmente False para formularios estándar
SESSION_COOKIE_SAMESITE = env_str("DJANGO_SESSION_COOKIE_SAMESITE", "Lax") or "Lax"
CSRF_COOKIE_SAMESITE = env_str("DJANGO_CSRF_COOKIE_SAMESITE", "Lax") or "Lax"


# =========================
# HSTS (solo cuando SSL redirect está activo)
# =========================
SECURE_HSTS_SECONDS = env_int("DJANGO_SECURE_HSTS_SECONDS", 31536000) if SECURE_SSL_REDIRECT else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", True) if SECURE_SSL_REDIRECT else False
)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", True) if SECURE_SSL_REDIRECT else False


# =========================
# Security headers
# =========================
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = env_str("DJANGO_X_FRAME_OPTIONS", "DENY") or "DENY"
SECURE_REFERRER_POLICY = (
    env_str("DJANGO_SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin")
    or "strict-origin-when-cross-origin"
)


# =========================
# Email
# =========================
# Backend real por API HTTPS (Resend), sin dependencia de SMTP.
# EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"

DEFAULT_FROM_EMAIL = env_str("DEFAULT_FROM_EMAIL", "support@egarage.cl")
SERVER_EMAIL = env_str("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
SUPPORT_EMAIL = env_str("SUPPORT_EMAIL", DEFAULT_FROM_EMAIL)
EMAIL_HOST_USER = SUPPORT_EMAIL

EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 30)

EMAIL_HOST = env_str("EMAIL_HOST", "srv24.cpanelhost.cl")
EMAIL_PORT = env_int("EMAIL_PORT", 465)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", True)
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
EMAIL_HOST_USER = env_str("EMAIL_HOST_USER", SUPPORT_EMAIL)
EMAIL_HOST_PASSWORD = env_str("EMAIL_HOST_PASSWORD", "")

# Gmail API OAuth
GMAIL_CREDENTIALS_FILE = env_str("GMAIL_CREDENTIALS_FILE", "/srv/egarage/gmail_credentials.json")
GMAIL_TOKEN_FILE = env_str("GMAIL_TOKEN_FILE", "/srv/egarage/gmail_token.json")
GMAIL_USER_ID = env_str("GMAIL_USER_ID", "me")
RESEND_API_KEY = env_str("RESEND_API_KEY", "")
ANYMAIL = {
    "RESEND_API_KEY": RESEND_API_KEY,
}

# Verificación de correo en producción (allauth); por defecto obligatoria.
ACCOUNT_EMAIL_VERIFICATION = env_str("ACCOUNT_EMAIL_VERIFICATION", "mandatory")
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = env_bool("ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION", True)

# Allauth usa /accounts/profile/ por defecto si no existe una redireccion explicita.
# En eGarage, despues de iniciar sesion se debe entrar al workspace country-aware.
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/cl/es/workspace/"
ACCOUNT_ADAPTER = "taller.views_extra.account_adapter.CountryAwareAccountAdapter"
ACCOUNT_FORMS = {
    "login": "taller.forms.custom_login.CustomLoginForm",
    "signup": "taller.forms.custom_signup.CustomSignupForm",
}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]


# =========================
# DB: Configuración unificada para DigitalOcean
# =========================
# Permite usar SQLite temporalmente o PostgreSQL según variables de entorno
# Para migrar a PostgreSQL, configura estas variables en .env:
#   DJANGO_DB_ENGINE=postgresql
#   DJANGO_DB_NAME=egarage_db
#   DJANGO_DB_USER=egarage
#   DJANGO_DB_PASSWORD=tu_password
#   DJANGO_DB_HOST=127.0.0.1
#   DJANGO_DB_PORT=5432

DB_ENGINE = env_str("DJANGO_DB_ENGINE", "sqlite3").lower()

if DB_ENGINE == "postgresql" or DB_ENGINE == "postgres":
    # PostgreSQL - Configuración para producción
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env_str("DJANGO_DB_NAME", "egarage_db"),
            "USER": env_str("DJANGO_DB_USER", "egarage"),
            "PASSWORD": env_str("DJANGO_DB_PASSWORD"),
            "HOST": env_str("DJANGO_DB_HOST", "127.0.0.1"),
            "PORT": env_str("DJANGO_DB_PORT", "5432"),
            "OPTIONS": {
                "connect_timeout": 10,
            },
        }
    }

    # Validar que la contraseña esté configurada
    if not DATABASES["default"]["PASSWORD"]:
        raise RuntimeError(
            "DJANGO_DB_PASSWORD debe estar configurado cuando se usa PostgreSQL. "
            "Configúralo en tu archivo .env o variables de entorno."
        )
else:
    # SQLite - Temporal para migración a DigitalOcean
    # ⚠️ ADVERTENCIA: SQLite no es recomendado para producción con múltiples workers
    # Usa esto solo durante la migración inicial
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": env_str("DJANGO_DB_NAME", "/srv/egarage/db.sqlite3"),
        }
    }

    # Validación desactivada temporalmente para permitir SQLite durante la migración
    # Cuando migres a PostgreSQL, descomenta estas líneas para forzar PostgreSQL:
    # if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    #     raise RuntimeError(
    #         "SQLite NO está permitido en producción. "
    #         "Configura DJANGO_DB_ENGINE=postgresql en tu archivo .env"
    #     )


# =========================
# Templates: fuerza carpeta canónica
# (evita que Django pesque templates “viejos” en deploy/backups)
# =========================
_base_dir = BASE_DIR if isinstance(BASE_DIR, Path) else Path(str(BASE_DIR))
TEMPLATES[0]["DIRS"] = [str(_base_dir / "templates")]

# Seguridad extra: evita que alguien meta rutas raras por accidente
TEMPLATES[0]["DIRS"] = [str(Path(p).resolve()) for p in TEMPLATES[0]["DIRS"]]

_context_processors = TEMPLATES[0].setdefault("OPTIONS", {}).setdefault("context_processors", [])
for _processor in [
    "django.template.context_processors.media",
    "django.template.context_processors.static",
    "django.template.context_processors.tz",
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
    "taller.context_processors.subscription_status.subscription_status",
    "taller.context_processors.subscription_notice.subscription_notice",
    "taller.context_processors.support_context",
    "taller.context_processors.ayuda_contextual.ayuda_contextual",
]:
    if _processor not in _context_processors:
        _context_processors.append(_processor)

# --- FIX FINAL DIGITALOCEAN ---
DEBUG = False

# Corregir rutas que tienen "/app/" de más
STATIC_ROOT = "/srv/egarage/staticfiles"
MEDIA_ROOT = "/srv/egarage/media"

# Forzar la base de datos a la ruta real de tu servidor
# Deshabilitar el bloqueo de SQLite
# if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
#     raise RuntimeError("PostgreSQL es obligatorio")

# Configuración crítica para el SSL que acabas de instalar
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = ["https://egarage.cl", "https://www.egarage.cl"]


# ===== FIX IDIOMA USA/CHILE EN PRODUCCION =====
# Django LocaleMiddleware solo no interpreta /us/en/... en esta arquitectura.
# Reinsertamos el middleware que fuerza idioma por prefijo país/idioma.
if "taller.middleware.lang_policy.LanguagePolicyMiddleware" not in MIDDLEWARE:
    try:
        idx = MIDDLEWARE.index("taller.middleware.empresa_middleware.EmpresaMiddleware")
        MIDDLEWARE.insert(idx, "taller.middleware.lang_policy.LanguagePolicyMiddleware")
    except ValueError:
        MIDDLEWARE.append("taller.middleware.lang_policy.LanguagePolicyMiddleware")

# =============================================================================
# Staticfiles: solo backends que existen SIEMPRE en el paquete desplegado.
# NO usar taller.storage.LenientCompressedManifestStaticFilesStorage aquí hasta
# que taller/storage.py esté garantizado en el servidor; si no, InvalidStorageError
# y cualquier {% static %} en plantillas → 500 (ej. /uy/es/bienvenida/).
# Tras cada deploy: python manage.py collectstatic --noinput
# =============================================================================
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
# Django 5+: STORAGES y STATICFILES_STORAGE son mutuamente excluyentes (heredado de settings.py).
globals().pop("STATICFILES_STORAGE", None)
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# =============================================================================
# Logging: solo consola (journald / stdout de Gunicorn).
# Evita FileHandler bajo /srv/egarage/logs sin permisos y el error
# "Unable to configure handler 'file'" si loggers referencian handlers inexistentes.
# =============================================================================
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
        "level": "INFO",
    },
    "loggers": {
        "django.security.DisallowedHost": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

SESSION_COOKIE_DOMAIN = ".egarage.cl"
CSRF_COOKIE_DOMAIN = ".egarage.cl"

# === FIX AUTH COOKIE DOMAIN EGARAGE ===
SESSION_COOKIE_DOMAIN = ".egarage.cl"
CSRF_COOKIE_DOMAIN = ".egarage.cl"
SESSION_COOKIE_PATH = "/"
CSRF_COOKIE_PATH = "/"


# === REDIS CACHE (SAFE SAAS) ===
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "TIMEOUT": 300,
    }
}


# Fix móvil: evita mismatch entre cookie csrftoken y formulario cacheado/prefetch Cloudflare/Samsung
CSRF_USE_SESSIONS = True

# BLOQUE SQLITE FINAL DESACTIVADO:
# La base de datos de producción debe quedar definida arriba por DJANGO_DB_ENGINE.
# Nunca sobrescribir DATABASES aquí.

EMAIL_BACKEND = env_str("EMAIL_BACKEND", "gestion_taller.resend_backend.ResendBackend")
RESEND_API_KEY = env_str("RESEND_API_KEY", "")
DEFAULT_FROM_EMAIL = env_str("DEFAULT_FROM_EMAIL", "support@egarage.cl")
ACCOUNT_LOGIN_METHODS = {'email'}

# Pasarelas de pago
FLOW_API_KEY = env_str("FLOW_API_KEY", "")
FLOW_SECRET_KEY = env_str("FLOW_SECRET_KEY", "")
FLOW_API_URL = env_str("FLOW_API_URL", "https://www.flow.cl/api")
FLOW_ENABLED = bool(
    os.getenv("FLOW_ENABLED", "1" if (FLOW_API_KEY and FLOW_SECRET_KEY) else "0") not in ("0", "false", "False", "")
)

MP_ACCESS_TOKEN = env_str("MP_ACCESS_TOKEN", "")
MP_ENABLED = bool(
    os.getenv("MP_ENABLED", "1" if MP_ACCESS_TOKEN else "0") not in ("0", "false", "False", "")
)
