"""
Configuración de producción para eGarage.
Configuración segura y optimizada para producción.
"""

from .base import *

# =============================================================================
# CONFIGURACIÓN DE PRODUCCIÓN
# =============================================================================

DEBUG = False

# =============================================================================
# SEGURIDAD
# =============================================================================

# Hosts permitidos (configurar según tu dominio)
ALLOWED_HOSTS = [
    "tu-dominio.com",
    "www.tu-dominio.com",
    "api.tu-dominio.com",
    # Añadir IPs de servidores si es necesario
    # "192.168.1.100",
]

# CSRF
CSRF_TRUSTED_ORIGINS = [
    "https://tu-dominio.com",
    "https://www.tu-dominio.com",
    "https://api.tu-dominio.com",
]

# SSL/HTTPS (activar si usas HTTPS)
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookies seguras
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Headers de seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# =============================================================================
# BASE DE DATOS
# =============================================================================

# Configuración de base de datos para producción
# Usar variables de entorno para credenciales
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'egarage_prod'),
        'USER': os.getenv('DB_USER', 'egarage_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# =============================================================================
# CACHÉ
# =============================================================================

# Configuración de caché para producción
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'egarage_prod',
        'TIMEOUT': 300,  # 5 minutos
    }
}

# =============================================================================
# LOGGING
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'egarage_prod.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'egarage_errors.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'taller': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['error_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# =============================================================================
# EMAIL
# =============================================================================

# Configuración de email para producción
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@tu-dominio.com')

# =============================================================================
# ARCHIVOS ESTÁTICOS
# =============================================================================

# Configuración de archivos estáticos para producción
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Configuración de archivos media para producción
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# =============================================================================
# OPTIMIZACIONES
# =============================================================================

# Desactivar debug toolbar
DEBUG_TOOLBAR = False

# Configuración de sesiones
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Configuración de archivos
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# =============================================================================
# MONITOREO
# =============================================================================

# Configuración de monitoreo (opcional)
# Sentry para tracking de errores
# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration
# 
# sentry_sdk.init(
#     dsn=os.getenv('SENTRY_DSN'),
#     integrations=[DjangoIntegration()],
#     traces_sample_rate=0.1,
#     send_default_pii=True
# )

# =============================================================================
# VARIABLES DE ENTORNO
# =============================================================================

# SECRET_KEY debe estar en variables de entorno
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configuración de CORS (si usas API)
CORS_ALLOWED_ORIGINS = [
    "https://tu-dominio.com",
    "https://www.tu-dominio.com",
]

# =============================================================================
# CONFIGURACIÓN ESPECÍFICA DE eGARAGE
# =============================================================================

# Configuración específica para producción
EGARAGE_PROD = True

# Configuración de backup automático
BACKUP_ENABLED = True
BACKUP_SCHEDULE = '0 2 * * *'  # Diario a las 2 AM

# Configuración de notificaciones
NOTIFICATIONS_ENABLED = True
NOTIFICATIONS_EMAIL = True
NOTIFICATIONS_SMS = False  # Configurar según necesidad

# Configuración de reportes
REPORTS_ENABLED = True
REPORTS_SCHEDULE = '0 6 * * 1'  # Lunes a las 6 AM

# Configuración de limpieza de datos
DATA_CLEANUP_ENABLED = True
DATA_CLEANUP_SCHEDULE = '0 3 * * 0'  # Domingo a las 3 AM

# =============================================================================
# CHECKLIST DE SEGURIDAD
# =============================================================================

# ✅ DEBUG = False
# ✅ ALLOWED_HOSTS configurado
# ✅ CSRF_TRUSTED_ORIGINS configurado
# ✅ SECURE_SSL_REDIRECT = True
# ✅ SESSION_COOKIE_SECURE = True
# ✅ CSRF_COOKIE_SECURE = True
# ✅ SECRET_KEY en variables de entorno
# ✅ Base de datos con SSL
# ✅ Logging configurado
# ✅ Email configurado
# ✅ Archivos estáticos configurados
# ✅ Caché configurado
# ✅ Headers de seguridad
# ✅ HSTS configurado