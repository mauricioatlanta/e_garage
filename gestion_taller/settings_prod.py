import os
from pathlib import Path

# --- CONFIGURACIÓN INTELIGENTE LOCAL/PROD ---
DEBUG = os.environ.get("DEBUG", "False") == "True"

# Solo redirigir a HTTPS si NO estamos en modo DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# Evitar conflictos de proxy en local
if DEBUG:
    SECURE_PROXY_SSL_HEADER = None
else:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- RESTO DE CONFIGURACIÓN ---
# (Aquí Django cargará el resto de tus settings_prod.py)
# gestion_taller/settings_prod.py
import os
from pathlib import Path

from dotenv import load_dotenv

from .settings import *  # noqa: F401,F403

# Cargar .env.prod de forma explÃ­cita para entornos que no exportan variables
_env_prod_path = Path(__file__).resolve().parent.parent / ".env.prod"
if _env_prod_path.exists():
    load_dotenv(_env_prod_path, override=True)


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
    "egarage.cl,www.egarage.cl,atlantareciclajes.cl,www.atlantareciclajes.cl,.pythonanywhere.com,localhost,127.0.0.1,159.223.200.106",
)

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "https://egarage.cl,https://www.egarage.cl,https://atlantareciclajes.cl,https://www.atlantareciclajes.cl,https://*.pythonanywhere.com",
)


# =========================
# HTTPS detrÃ¡s de proxy (PythonAnywhere)
# =========================
# ðŸ”¥ IMPRESCINDIBLE: ConfiguraciÃ³n fija para producciÃ³n (no controlada por env)
# Este header es CRÃTICO cuando Django estÃ¡ detrÃ¡s de un proxy (Nginx, Cloudflare, etc.)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env_bool("DJANGO_USE_X_FORWARDED_HOST", True)

# ðŸ”¥ IMPRESCINDIBLE: Fijo en True para producciÃ³n (requiere SECURE_PROXY_SSL_HEADER arriba)
# âš ï¸ TEMPORAL: Si aÃºn no tienes certificado SSL instalado, cambia esto a False
# o configura DJANGO_SECURE_SSL_REDIRECT=false en .env
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", True)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", True)

# Recomendado en producciÃ³n (evita robo de cookie por JS)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # normalmente False para formularios estÃ¡ndar
SESSION_COOKIE_SAMESITE = env_str("DJANGO_SESSION_COOKIE_SAMESITE", "Lax") or "Lax"
CSRF_COOKIE_SAMESITE = env_str("DJANGO_CSRF_COOKIE_SAMESITE", "Lax") or "Lax"

_cookie_domain = env_str("DJANGO_COOKIE_DOMAIN", "")
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


# =========================
# HSTS (solo cuando SSL redirect estÃ¡ activo)
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
SECURE_REFERRER_POLICY = "same-origin"


# =========================
# Email
# =========================
# Backend real por API HTTPS (Resend), sin dependencia de SMTP.
EMAIL_BACKEND = "taller.email_backends.resend_backend.ResendEmailBackend"

DEFAULT_FROM_EMAIL = env_str("DEFAULT_FROM_EMAIL", "support@egarage.cl")
SERVER_EMAIL = env_str("SERVER_EMAIL", "support@egarage.cl")
SUPPORT_EMAIL = env_str("SUPPORT_EMAIL", "support@egarage.cl")

EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 30)

# Gmail API OAuth
GMAIL_CREDENTIALS_FILE = env_str("GMAIL_CREDENTIALS_FILE", "/srv/egarage/gmail_credentials.json")
GMAIL_TOKEN_FILE = env_str("GMAIL_TOKEN_FILE", "/srv/egarage/gmail_token.json")
GMAIL_USER_ID = env_str("GMAIL_USER_ID", "me")
RESEND_API_KEY = env_str("RESEND_API_KEY", "")

# VerificaciÃ³n de correo en producciÃ³n (allauth); por defecto obligatoria.
ACCOUNT_EMAIL_VERIFICATION = env_str("ACCOUNT_EMAIL_VERIFICATION", "mandatory")
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = env_bool("ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION", True)


# =========================
# DB: ConfiguraciÃ³n unificada para DigitalOcean
# =========================
# Permite usar SQLite temporalmente o PostgreSQL segÃºn variables de entorno
# Para migrar a PostgreSQL, configura estas variables en .env:
#   DJANGO_DB_ENGINE=postgresql
#   DJANGO_DB_NAME=egarage_db
#   DJANGO_DB_USER=egarage
#   DJANGO_DB_PASSWORD=tu_password
#   DJANGO_DB_HOST=127.0.0.1
#   DJANGO_DB_PORT=5432

DB_ENGINE = env_str("DJANGO_DB_ENGINE", "sqlite3").lower()

if DB_ENGINE == "postgresql" or DB_ENGINE == "postgres":
    # PostgreSQL - ConfiguraciÃ³n para producciÃ³n
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

    # Validar que la contraseÃ±a estÃ© configurada
    if not DATABASES["default"]["PASSWORD"]:
        raise RuntimeError(
            "DJANGO_DB_PASSWORD debe estar configurado cuando se usa PostgreSQL. "
            "ConfigÃºralo en tu archivo .env o variables de entorno."
        )
else:
    # SQLite - Temporal para migraciÃ³n a DigitalOcean
    # âš ï¸ ADVERTENCIA: SQLite no es recomendado para producciÃ³n con mÃºltiples workers
    # Usa esto solo durante la migraciÃ³n inicial
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": env_str("DJANGO_DB_NAME", "/srv/egarage/db.sqlite3"),
        }
    }

    # ValidaciÃ³n desactivada temporalmente para permitir SQLite durante la migraciÃ³n
    # Cuando migres a PostgreSQL, descomenta estas lÃ­neas para forzar PostgreSQL:
    # if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    #     raise RuntimeError(
    #         "SQLite NO estÃ¡ permitido en producciÃ³n. "
    #         "Configura DJANGO_DB_ENGINE=postgresql en tu archivo .env"
    #     )


# =========================
# Templates: fuerza carpeta canÃ³nica
# (evita que Django pesque templates â€œviejosâ€ en deploy/backups)
# =========================
_base_dir = BASE_DIR if isinstance(BASE_DIR, Path) else Path(str(BASE_DIR))
TEMPLATES[0]["DIRS"] = [str(_base_dir / "templates")]

# Seguridad extra: evita que alguien meta rutas raras por accidente
TEMPLATES[0]["DIRS"] = [str(Path(p).resolve()) for p in TEMPLATES[0]["DIRS"]]

# --- FIX FINAL DIGITALOCEAN ---
# DEBUG = False (COMENTADO)

# Corregir rutas que tienen "/app/" de mÃ¡s
STATIC_ROOT = "/srv/egarage/staticfiles"
MEDIA_ROOT = "/srv/egarage/media"

# Forzar la base de datos a la ruta real de tu servidor
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/srv/egarage/db.sqlite3",
    }
}

# Deshabilitar el bloqueo de SQLite
# if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
#     raise RuntimeError("PostgreSQL es obligatorio")

# ConfiguraciÃ³n crÃ­tica para el SSL que acabas de instalar
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = ["https://egarage.cl", "https://www.egarage.cl"]


# ===== FIX IDIOMA USA/CHILE EN PRODUCCION =====
# Django LocaleMiddleware solo no interpreta /us/en/... en esta arquitectura.
# Reinsertamos el middleware que fuerza idioma por prefijo paÃ­s/idioma.
if "taller.middleware.lang_policy.LanguagePolicyMiddleware" not in MIDDLEWARE:
    try:
        idx = MIDDLEWARE.index("taller.middleware.empresa_middleware.EmpresaMiddleware")
        MIDDLEWARE.insert(idx, "taller.middleware.lang_policy.LanguagePolicyMiddleware")
    except ValueError:
        MIDDLEWARE.append("taller.middleware.lang_policy.LanguagePolicyMiddleware")

# =============================================================================
# Staticfiles: solo backends que existen SIEMPRE en el paquete desplegado.
# NO usar taller.storage.LenientCompressedManifestStaticFilesStorage aquÃ­ hasta
# que taller/storage.py estÃ© garantizado en el servidor; si no, InvalidStorageError
# y cualquier {% static %} en plantillas â†’ 500 (ej. /uy/es/bienvenida/).
# Tras cada deploy: python manage.py collectstatic --noinput
# =============================================================================
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
# Django 5+: STORAGES y STATICFILES_STORAGE son mutuamente excluyentes (heredado de settings.py).
globals().pop("STATICFILES_STORAGE", None)
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False

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

# === FIX COUNTRY CONTEXT PROCESSOR ===
try:
    if (
        "taller.context_processors.country.country_context"
        not in TEMPLATES[0]["OPTIONS"]["context_processors"]
    ):
        TEMPLATES[0]["OPTIONS"]["context_processors"].append(
            "taller.context_processors.country.country_context"
        )
except Exception as e:
    print("ERROR CP:", e)

# --- OVERRIDE FINAL PARA DESARROLLO LOCAL ---
import os

os.environ["DEBUG"] = "True"
DEBUG = True
ALLOWED_HOSTS = ["*"]
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_PROXY_SSL_HEADER = None
# --------------------------------------------
