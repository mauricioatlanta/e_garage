# gestion_taller/settings_prod.py
import os
from pathlib import Path

from .settings import *  # noqa: F401,F403


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
# Email (envío de documentos, notificaciones)
# =========================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
DEFAULT_FROM_EMAIL = env_str("DEFAULT_FROM_EMAIL", "noreply@tudominio.com")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

EMAIL_HOST = env_str("EMAIL_HOST", "")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env_str("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env_str("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)


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

# --- FIX FINAL DIGITALOCEAN ---
DEBUG = False

# Corregir rutas que tienen "/app/" de más
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
