"""
===============================================================
🚀 CONFIGURACIÓN DE PRODUCCIÓN PARA PYTHONANYWHERE
===============================================================
Configuración optimizada para el despliegue en PythonAnywhere
URL: https://e-garage-atlantareciclajes.pythonanywhere.com
Fecha: 24 de julio de 2025
"""

import os
from pathlib import Path

# ============================================================
# 📁 RUTA BASE
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# 🔐 SEGURIDAD PARA PRODUCCIÓN
# ============================================================
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'ej+v^g#=l@x+$#$n&8k3w#!zf_9z8j@4m5n6p7q8r9s0t1u2v3w4x5y6z')
DEBUG = False
ALLOWED_HOSTS = [
    'e-garage-atlantareciclajes.pythonanywhere.com',
    'www.e-garage-atlantareciclajes.pythonanywhere.com',
    'atlantareciclajes.pythonanywhere.com',  # Fallback
    '127.0.0.1',
    'localhost',
]

# ============================================================
# 🔌 APLICACIONES INSTALADAS
# ============================================================
INSTALLED_APPS = [
    'widget_tweaks',
    'dal',
    'dal_select2',
    'crispy_forms',
    'crispy_bootstrap4',
    'crispy_bootstrap5',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'taller.apps.TallerConfig',
    'rest_framework',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

# ============================================================
# 🔧 MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'taller.middleware.EmpresaMiddleware',
]

# ============================================================
# 🌐 CONFIGURACIÓN DE URLs
# ============================================================
ROOT_URLCONF = 'gestion_taller.urls'  # Usar gestion_taller.urls como en producción
WSGI_APPLICATION = 'e_garage.wsgi.application'

# ============================================================
# 🗄️ BASE DE DATOS - MYSQL PYTHONANYWHERE
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'atlantareciclajes$egarage'),
        'USER': os.getenv('DB_USER', 'atlantareciclajes'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'laila2013@'),
        'HOST': os.getenv('DB_HOST', 'atlantareciclajes.mysql.pythonanywhere-services.com'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ============================================================
# 🔑 CONFIGURACIÓN DE AUTENTICACIÓN
# ============================================================
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================================
# 🌍 INTERNACIONALIZACIÓN
# ============================================================
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# ============================================================
# 📁 ARCHIVOS ESTÁTICOS Y MEDIA
# ============================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Configuración para WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Archivos media
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================================
# 📧 CONFIGURACIÓN DE EMAIL
# ============================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.atlantareciclajes.cl'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'contacto@atlantareciclajes.cl'
EMAIL_HOST_PASSWORD = 'laila2013@'
DEFAULT_FROM_EMAIL = 'eGarage <contacto@atlantareciclajes.cl>'
SERVER_EMAIL = 'servidor@atlantareciclajes.cl'

# ============================================================
# 🔒 CONFIGURACIÓN DE SEGURIDAD PARA PRODUCCIÓN
# ============================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# Solo para HTTPS en producción
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True

# ============================================================
# 🎨 CONFIGURACIÓN DE FORMULARIOS
# ============================================================
CRISPY_TEMPLATE_PACK = 'bootstrap5'
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

# ============================================================
# 👤 CONFIGURACIÓN DE ALLAUTH
# ============================================================
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_UNIQUE_EMAIL = True
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_ON_GET = True

# ============================================================
# 🔌 CONFIGURACIÓN DE REST FRAMEWORK
# ============================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# ============================================================
# 🌐 CONFIGURACIÓN CORS
# ============================================================
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://e-garage-atlantareciclajes.pythonanywhere.com",
    "https://www.e-garage-atlantareciclajes.pythonanywhere.com",
]

# ============================================================
# 📊 CONFIGURACIÓN DE LOGGING
# ============================================================
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
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
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
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================
# ⚡ CONFIGURACIÓN DE CACHE
# ============================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# ============================================================
# 📱 CONFIGURACIÓN ADICIONAL
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de sesiones
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Configuración de uploads
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

print("🚀 Configuración de producción PythonAnywhere cargada exitosamente")
print(f"📊 DEBUG: {DEBUG}")
print(f"🌐 ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"🗄️ BASE DE DATOS: MySQL en PythonAnywhere")
print(f"📧 EMAIL: Configurado con atlantareciclajes.cl")
print(f"🔒 SEGURIDAD: Configuración de producción activada")
