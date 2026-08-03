# gestion_taller/settings_test.py
"""
Settings exclusivos para pytest en servidor y CI.

Uso:
    export DJANGO_SETTINGS_MODULE=gestion_taller.settings_test
    pytest commerce -q

No usar en producción — para eso existe settings_prod.py.
"""
import os
import tempfile

from gestion_taller.settings import *  # noqa: F401,F403

# ── Base de datos: SQLite en memoria (rápido, sin archivos residuales) ─────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ── Hash de contraseñas: MD5 (suficiente para tests, mucho más rápido que pbkdf2) ─
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ── Email: captura en memoria, sin SMTP real ──────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ── Cache: en proceso, sin Redis ──────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ── Hosts: permisivo (tests usan testserver y dominios de fixtures) ───────────
ALLOWED_HOSTS = ["*", "testserver", "teststore.local"]
CSRF_TRUSTED_ORIGINS = []

# ── Sin SSL redirect ni headers de seguridad que rompan el test client ────────
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_PROXY_SSL_HEADER = None

# ── Sin cookie domains fijos (el test client no envía dominio) ────────────────
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None

# ── Media: directorio temporal (tests que suben archivos usan tmp_path) ───────
MEDIA_ROOT = os.path.join(tempfile.gettempdir(), "egarage_test_media")
MEDIA_URL = "/media/"

# ── Logging: silencio total en CI ─────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {"class": "logging.NullHandler"},
    },
    "root": {"handlers": ["null"], "level": "CRITICAL"},
}

# ── Commerce: mapa vacío (cada test inyecta el tenant con override_settings) ──
COMMERCE_TENANT_MAP: dict = {}

# ── Pasarelas de pago: desactivadas ───────────────────────────────────────────
FLOW_ENABLED = False
MP_ENABLED = False
