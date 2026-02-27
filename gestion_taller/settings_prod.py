# gestion_taller/settings_prod.py
import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F401,F403

# =============================================================================
# SECRET_KEY (obligatorio en producción - evita W009)
# =============================================================================
# Leer SECRET_KEY o DJANGO_SECRET_KEY desde .env.prod (EnvironmentFile en systemd).
# Sin esto, Django usa fallback inseguro y check --deploy reporta W009.
# Al ejecutar "manage.py test" se permite clave temporal para no depender de .env.prod.
_SECRET = os.getenv("SECRET_KEY") or os.getenv("DJANGO_SECRET_KEY")
if not _SECRET or _SECRET.strip() == "":
    if "test" in sys.argv:
        from django.core.management.utils import get_random_secret_key
        SECRET_KEY = get_random_secret_key()
    else:
        raise ImproperlyConfigured(
            "En producción defina SECRET_KEY o DJANGO_SECRET_KEY en .env.prod (o en el unit de gunicorn)."
        )
else:
    SECRET_KEY = _SECRET.strip()

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
ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "egarage.cl,www.egarage.cl,atlantareciclajes.cl,www.atlantareciclajes.cl,.pythonanywhere.com,localhost,127.0.0.1,159.223.200.106",
)

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "https://egarage.cl,https://www.egarage.cl,https://atlantareciclajes.cl,https://www.atlantareciclajes.cl,https://*.pythonanywhere.com",
)


# =========================
# HTTPS detrás de proxy (PythonAnywhere)
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
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"


# =========================
# HSTS (solo cuando SSL redirect está activo)
# =========================
SECURE_HSTS_SECONDS = env_int("DJANGO_SECURE_HSTS_SECONDS", 31536000) if SECURE_SSL_REDIRECT else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", True) if SECURE_SSL_REDIRECT else False
)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", True) if SECURE_SSL_REDIRECT else False


# =========================
# LOGGING: solo consola en producción (evita PermissionError en /srv/egarage/logs/)
# =========================
# Si no se fuerza aquí, un settings que herede file/error_file puede hacer fallar
# a los workers de Gunicorn si el usuario no tiene permiso de escritura en logs/.
import sys

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(levelname)s %(asctime)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stderr,
            "formatter": "default",
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "taller": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

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
# DB: DATABASE_URL tiene prioridad (evita Postgres con ruta SQLite)
# =========================
# 1) Si DATABASE_URL es sqlite → siempre SQLite (ignora DJANGO_DB_ENGINE/DJANGO_DB_NAME)
# 2) Si quieres Postgres: DJANGO_DB_ENGINE=postgresql Y DJANGO_DB_PASSWORD obligatorio
# 3) Si no → SQLite en /srv/egarage/data/db.sqlite3

_database_url = (os.getenv("DATABASE_URL") or "").strip()

if _database_url.lower().startswith("sqlite"):
    # DATABASE_URL=sqlite:////srv/egarage/data/db.sqlite3 → usar SQLite (nunca Postgres)
    import urllib.parse

    _u = urllib.parse.urlparse(_database_url)
    _path = (_u.path or "").strip()
    if _path.startswith("//"):
        _path = "/" + _path.lstrip("/")
    if not _path or not os.path.isabs(_path):
        _path = str(BASE_DIR / (_path or "data/db.sqlite3"))
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _path,
        }
    }
elif env_str("DJANGO_DB_ENGINE", "sqlite3").lower() in ("postgresql", "postgres") and env_str(
    "DJANGO_DB_PASSWORD"
):
    # PostgreSQL solo con contraseña (evita fe_sendauth: no password supplied)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env_str("DJANGO_DB_NAME", "egarage_db"),
            "USER": env_str("DJANGO_DB_USER", "egarage"),
            "PASSWORD": env_str("DJANGO_DB_PASSWORD"),
            "HOST": env_str("DJANGO_DB_HOST", "127.0.0.1"),
            "PORT": env_str("DJANGO_DB_PORT", "5432"),
            "OPTIONS": {"connect_timeout": 10},
        }
    }
else:
    # SQLite por defecto (sin DATABASE_URL sqlite y sin Postgres con password)
    _sqlite_name = env_str("SQLITE_PATH", "/srv/egarage/data/db.sqlite3")
    if not os.path.isabs(_sqlite_name):
        _sqlite_name = str(BASE_DIR / _sqlite_name.lstrip("/"))
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _sqlite_name,
        }
    }


# =========================
# Templates: fuerza carpeta canónica
# (evita que Django pesque templates “viejos” en deploy/backups)
# =========================
_base_dir = BASE_DIR if isinstance(BASE_DIR, Path) else Path(str(BASE_DIR))
TEMPLATES[0]["DIRS"] = [str(_base_dir / "templates")]

# Seguridad extra: evita que alguien meta rutas raras por accidente
TEMPLATES[0]["DIRS"] = [str(Path(p).resolve()) for p in TEMPLATES[0]["DIRS"]]

# --- FIX FINAL DIGITALOCEAN ---
DEBUG = False

# 🔥 CRÍTICO: ALLOWED_HOSTS debe estar explícitamente definido aquí
# para evitar Error 400 (Bad Request) cuando las variables de entorno no se cargan correctamente
# Incluye IP del servidor (159.223.200.106) para acceso directo y health checks
ALLOWED_HOSTS = [
    "egarage.cl",
    "www.egarage.cl",
    "atlantareciclajes.cl",
    "www.atlantareciclajes.cl",
    "127.0.0.1",
    "localhost",
    "159.223.200.106",
]

# Corregir rutas que tienen "/app/" de más
STATIC_ROOT = "/srv/egarage/staticfiles"
MEDIA_ROOT = "/srv/egarage/media"

# 🔥 CRÍTICO: Asegurar que Django encuentre los templates
# Incluye tanto la carpeta raíz como la carpeta de la app (por si acaso)
_base_dir = BASE_DIR if isinstance(BASE_DIR, Path) else Path(str(BASE_DIR))
TEMPLATES[0]["DIRS"] = [
    str(_base_dir / "templates"),
    str(_base_dir / "taller" / "templates"),  # Por si hay templates dentro de la app
]
# Seguridad extra: normalizar rutas
TEMPLATES[0]["DIRS"] = [str(Path(p).resolve()) for p in TEMPLATES[0]["DIRS"] if Path(p).exists()]

# DB ya definido arriba (DATABASE_URL sqlite → SQLite; Postgres con password → Postgres; sino → SQLite)

# Configuración crítica para el SSL que acabas de instalar
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = ["https://egarage.cl", "https://www.egarage.cl"]

# ==========================================
# AUTH FIX (Multi-country login neutral)
# ==========================================
LOGIN_URL = "/accounts/login/"

# /accounts/login/ sin prefijo → deducir país desde next (o from), luego redirect a /<cc>/accounts/login/.
# Ubicación: después de SessionMiddleware, antes de LocaleMiddleware.
MIDDLEWARE = list(MIDDLEWARE)
try:
    idx = MIDDLEWARE.index("django.contrib.sessions.middleware.SessionMiddleware")
    MIDDLEWARE.insert(idx + 1, "taller.middleware.force_accounts_to_cl.ForceAccountsToCLMiddleware")
except ValueError:
    MIDDLEWARE.insert(0, "taller.middleware.force_accounts_to_cl.ForceAccountsToCLMiddleware")
