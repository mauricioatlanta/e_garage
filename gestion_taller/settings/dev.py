"""
Configuración de desarrollo para eGarage
"""

from .base import *

# Debug habilitado para desarrollo
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Hosts permitidos para desarrollo
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# Base de datos - PostgreSQL si hay variables de entorno, SQLite por defecto
if os.getenv("DATABASE_URL"):
    import dj_database_url
    import urllib.parse
    # Obtener la URL y verificar si es localhost
    database_url = os.getenv("DATABASE_URL")
    parsed_url = urllib.parse.urlparse(database_url)
    
    # Si el host es localhost, construir configuración manualmente (evita problemas con dj_database_url y SSL)
    if parsed_url.hostname in ("localhost", "127.0.0.1", "::1", None) or "localhost" in str(parsed_url.hostname or "").lower():
        # Extraer credenciales de la URL
        username = parsed_url.username or ""
        password = parsed_url.password or ""
        # Forzar IPv4 para evitar problemas con IPv6 y SSL
        hostname = "127.0.0.1"  # Siempre usar IPv4 para localhost
        port = parsed_url.port or 5432
        database = parsed_url.path.lstrip("/") or ""
        
        # Construir configuración manualmente con SSL desactivado
        # IMPORTANTE: psycopg2 requiere que sslmode se pase como parte del DSN o en connect_kwargs
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": database,
                "USER": username,
                "PASSWORD": password,
                "HOST": hostname,
                "PORT": port,
                "OPTIONS": {
                    "sslmode": "disable",  # Forzar desactivación de SSL
                },
                "CONN_MAX_AGE": 600,
            }
        }
    else:
        # Para hosts remotos, usar dj_database_url normalmente
        db_config = dj_database_url.parse(database_url, conn_max_age=600)
        DATABASES = {"default": db_config}
elif os.getenv("DJANGO_DB_NAME") or os.getenv("DB_NAME"):
    # PostgreSQL con configuración desde variables de entorno
    db_host = os.getenv("DJANGO_DB_HOST") or os.getenv("DB_HOST", "localhost")
    # Forzar IPv4 para evitar problemas con IPv6 y SSL
    if db_host.lower() in ("localhost", "::1"):
        db_host = "127.0.0.1"
    
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DJANGO_DB_NAME") or os.getenv("DB_NAME"),
            "USER": os.getenv("DJANGO_DB_USER") or os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DJANGO_DB_PASSWORD") or os.getenv("DB_PASSWORD"),
            "HOST": db_host,
            "PORT": os.getenv("DJANGO_DB_PORT") or os.getenv("DB_PORT", "5432"),
            "OPTIONS": {
                "sslmode": "disable",  # Desactivar SSL para localhost
            },
        }
    }
else:
    # SQLite por defecto para desarrollo
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Archivos estáticos para desarrollo
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Archivos subidos por el usuario
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Mimetypes útiles en desarrollo
import mimetypes

mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("application/javascript", ".js", True)

# Logging más detallado para desarrollo (solo si no está en modo seguro)
if not SAFE_MODE:
    # La configuración de logging ya está optimizada en base.py
    # No necesitamos modificar nada aquí
    pass
