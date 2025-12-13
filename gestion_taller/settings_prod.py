import os
from .settings import *  # noqa


def env_bool(key, default=False):
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(key, default=""):
    raw = os.getenv(key, default) or ""
    return [x.strip() for x in raw.split(",") if x.strip()]


# --- Debug ---
DEBUG = env_bool("DJANGO_DEBUG", False)

# --- FIX 400 (hosts) ---
ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "egarage.cl,www.egarage.cl,atlantareciclajes.cl,www.atlantareciclajes.cl,.pythonanywhere.com,localhost,127.0.0.1",
)

# --- CSRF (POST/login con HTTPS) ---
CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "https://egarage.cl,https://www.egarage.cl,https://atlantareciclajes.cl,https://www.atlantareciclajes.cl,https://*.pythonanywhere.com",
)

# --- HTTPS detrás de PythonAnywhere ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env_bool("DJANGO_USE_X_FORWARDED_HOST", True)

SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", True)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", True)

# --- HSTS ---
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
SECURE_HSTS_PRELOAD = True

# --- Security headers (los tenías antes) ---
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# --- DB: usar shared SOLO si es sqlite ---
if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    DATABASES["default"]["NAME"] = os.getenv(
        "DJANGO_DB_PATH",
        "/home/atlantareciclajes/apps/egarage/shared/db/db.sqlite3",
    )
