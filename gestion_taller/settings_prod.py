# gestion_taller/settings_prod.py
import os
from pathlib import Path

from .settings import *  # noqa: F401,F403


# =========================
# Helpers de entorno
# =========================
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


def env_list(key: str, default: str = "") -> list[str]:
    # acepta separador por coma o salto de línea
    raw = env_str(key, default).replace("\n", ",")
    items = []
    for x in raw.split(","):
        x = x.strip()
        if x:
            items.append(x)
    return items


# =========================
# Debug
# =========================
DEBUG = env_bool("DJANGO_DEBUG", False)


# =========================
# Hosts / CSRF
# =========================
ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "egarage.cl,www.egarage.cl,atlantareciclajes.cl,www.atlantareciclajes.cl,.pythonanywhere.com,localhost,127.0.0.1",
)

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "https://egarage.cl,https://www.egarage.cl,https://atlantareciclajes.cl,https://www.atlantareciclajes.cl,https://*.pythonanywhere.com",
)


# =========================
# HTTPS detrás de proxy (PythonAnywhere)
# =========================
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env_bool("DJANGO_USE_X_FORWARDED_HOST", True)

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
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", True) if SECURE_SSL_REDIRECT else False
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", True) if SECURE_SSL_REDIRECT else False


# =========================
# Security headers
# =========================
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = env_str("DJANGO_X_FRAME_OPTIONS", "DENY") or "DENY"
SECURE_REFERRER_POLICY = env_str("DJANGO_SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin") or "strict-origin-when-cross-origin"


# =========================
# DB: SQLite shared + “airbag” de ruta
# =========================
if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    REQUIRED_DB = "/home/atlantareciclajes/apps/egarage/shared/db/db.sqlite3"
    DATABASES["default"]["NAME"] = env_str("DJANGO_DB_PATH", REQUIRED_DB)

    # Airbag: en producción NO permitas apuntar a otra DB por accidente
    # (si quieres desactivarlo temporalmente: DJANGO_ENFORCE_PROD_DB_PATH=False)
    if env_bool("DJANGO_ENFORCE_PROD_DB_PATH", True):
        current = str(Path(DATABASES["default"]["NAME"]).resolve())
        required = str(Path(REQUIRED_DB).resolve())
        if current != required:
            raise RuntimeError(f"PROD DB PATH inválido. Esperado: {required} | Actual: {current}")


# =========================
# Templates: fuerza carpeta canónica
# (evita que Django pesque templates “viejos” en deploy/backups)
# =========================
_base_dir = BASE_DIR if isinstance(BASE_DIR, Path) else Path(str(BASE_DIR))
TEMPLATES[0]["DIRS"] = [str(_base_dir / "templates")]

# Seguridad extra: evita que alguien meta rutas raras por accidente
TEMPLATES[0]["DIRS"] = [str(Path(p).resolve()) for p in TEMPLATES[0]["DIRS"]]
