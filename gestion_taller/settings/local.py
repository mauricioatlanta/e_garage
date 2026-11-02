"""
Configuración local para eGarage
Archivo para overrides personales (gitignored)
"""

from .dev import *

# Overrides personales para desarrollo local
# DEBUG = True
# ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Base de datos local personalizada
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": "egarage_local",
#         "USER": "tu_usuario",
#         "PASSWORD": "tu_password",
#         "HOST": "localhost",
#         "PORT": "5432",
#     }
# }

# Configuración de email local
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Logging más detallado para desarrollo local
# LOGGING["loggers"]["django"]["level"] = "DEBUG"
# LOGGING["loggers"]["taller"]["level"] = "DEBUG"

# Configuración específica para tu entorno local
# TIME_ZONE = "America/Santiago"
# LANGUAGE_CODE = "es"

# Usar la misma BD que pytest (tiene los datos reales de desarrollo)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/home/mauricio/.egarage/db.sqlite3",
    }
}

# Commerce Engine — tenant map para desarrollo local
# Empresa 4 = MonteAzul Import Test (catálogo real, 100 productos)
COMMERCE_TENANT_MAP = {
    "localhost": 4,
    "127.0.0.1": 4,
    "monteazul.local": 4,
}
ALLOWED_HOSTS = ["*"]
