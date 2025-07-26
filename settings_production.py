# ============================================================
# 🏭 CONFIGURACIÓN DE PRODUCCIÓN PARA PYTHONANYWHERE
# ============================================================
# Archivo: settings_production.py
# URL de producción: https://e-garage-atlantareciclajes.pythonanywhere.com

import os
import logging
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# 🔐 CONFIGURACIÓN DE SEGURIDAD PARA PRODUCCIÓN
# ============================================================
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'laila2013-production-key-change-in-server')
DEBUG = False

# Dominios permitidos para PythonAnywhere
ALLOWED_HOSTS = [
    'e-garage-atlantareciclajes.pythonanywhere.com',
    'www.e-garage-atlantareciclajes.pythonanywhere.com',
    'atlantareciclajes.pythonanywhere.com',
    '127.0.0.1',
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
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_extensions',
    'django.contrib.humanize',
]

# ============================================================
# 🔧 MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'taller.middleware.empresa_middleware.EmpresaMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'gestion_taller.urls'

# ============================================================
# 📐 TEMPLATES
# ============================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'taller.context_processors.empresa_contexto',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_taller.wsgi.application'

ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']

# ============================================================
# 🗄️ BASE DE DATOS - MYSQL PARA PYTHONANYWHERE
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'atlantareciclajes$egarage'),
        'USER': os.environ.get('DB_USER', 'atlantareciclajes'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'laila2013'),
        'HOST': os.environ.get('DB_HOST', 'atlantareciclajes.mysql.pythonanywhere-services.com'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ============================================================
# 🔐 VALIDADORES DE CONTRASEÑA
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================================
# 🌐 INTERNACIONALIZACIÓN
# ============================================================
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'

USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

DEFAULT_USA_TIMEZONE = 'America/New_York'

# ============================================================
# 🎨 ARCHIVOS ESTÁTICOS Y MEDIA PARA PYTHONANYWHERE
# ============================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================================
# 🌍 CONFIGURACIÓN DE SELECT2
# ============================================================
SELECT2_I18N = 'es'

# ============================================================
# 🛠️ CONFIGURACIÓN FORM DEBUG
# ============================================================
FORM_DEBUG = False  # Desactivado en producción

SESSION_ENGINE = "django.contrib.sessions.backends.db"

# ✅ Configuración para Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ============================================================
# 📧 CONFIGURACIÓN DE EMAIL PARA PRODUCCIÓN
# ============================================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'mail.atlantareciclajes.cl'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = 'contacto@atlantareciclajes.cl'
EMAIL_HOST_PASSWORD = 'laila2013@'
DEFAULT_FROM_EMAIL = 'eGarage Sistema <contacto@atlantareciclajes.cl>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ============================================================
# 🔐 CONFIGURACIÓN DE ALLAUTH PARA PRODUCCIÓN
# ============================================================
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# ============================================================
# 🔒 CONFIGURACIONES DE SEGURIDAD ADICIONALES
# ============================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Para HTTPS en producción (descomentar cuando esté disponible SSL)
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# ============================================================
# 📊 LOGGING PARA PRODUCCIÓN
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
            'filename': os.path.join(BASE_DIR, 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'taller': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# ============================================================
# 🚀 CONFIGURACIONES DE RENDIMIENTO
# ============================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ============================================================
# 📧 CONFIGURACIÓN DE ADMINISTRADORES
# ============================================================
ADMINS = [
    ('Admin eGarage', 'contacto@atlantareciclajes.cl'),
]

MANAGERS = ADMINS

# ============================================================
# 📱 CONFIGURACIONES ADICIONALES DE ARCHIVOS
# ============================================================
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880   # 5MB

print("🚀 CONFIGURACIÓN DE PRODUCCIÓN CARGADA PARA PYTHONANYWHERE")
