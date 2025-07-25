import os
from pathlib import Path


# ============================================================
# 📁 RUTA BASE
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# 🔐 SEGURIDAD
# ============================================================
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'laila2013')
DEBUG = True
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if not DEBUG else []

# ============================================================
# 🔌 APLICACIONES INSTALADAS
# ============================================================
INSTALLED_APPS = [
    'widget_tweaks',
    'dal',
    'dal_select2',
    'crispy_forms',  # ✅ ¡Agrega esta línea!
    'crispy_bootstrap4',
    'crispy_bootstrap5',  # ✅ Bootstrap 5 support
    'allauth',  # ✅ Django Allauth
    'allauth.account',  # ✅ Account management
    'allauth.socialaccount',  # ✅ Social account (opcional)
    'taller.apps.TallerConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # ✅ Necesario para allauth
    'django_extensions',
    'django.contrib.humanize',
]

# ============================================================
# 🔧 MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # ✅ Middleware de idioma
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'taller.middleware.empresa_middleware.EmpresaMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Añadido para django-allauth
]

# ============================================================
# 🔗 CONFIGURACIÓN DE URLS
# ============================================================
ROOT_URLCONF = 'gestion_taller.urls'

# ============================================================
# 📐 TEMPLATES (con builtins de humanize)
# ============================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Asegúrate de que esta línea esté configurada correctamente
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


# ============================================================
# 🚀 WSGI
# ============================================================
WSGI_APPLICATION = 'gestion_taller.wsgi.application'

ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']

# ============================================================
# 🗄️ BASE DE DATOS (PostgreSQL)
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'tallerpro'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'laila2013'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
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
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================================
# 🌐 INTERNACIONALIZACIÓN COMPLETA USA + ESPAÑA
# ============================================================
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'

USE_I18N = True
USE_L10N = True
USE_TZ = True

# Idiomas soportados
LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
]

# Directorios de archivos de traducción
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Zona horaria por defecto para USA
DEFAULT_USA_TIMEZONE = 'America/New_York'

# ============================================================
# 🎨 ARCHIVOS ESTÁTICOS Y MULTIMEDIA
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
# 🛠️ CONFIGURACIÓN DE DEPURACIÓN
# ============================================================
FORM_DEBUG = DEBUG  # Habilitar depuración de formularios si DEBUG está activado

SESSION_ENGINE = "django.contrib.sessions.backends.db"

# ✅ Configuración para Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ============================================================
# 📧 CONFIGURACIÓN DE EMAIL PARA DESARROLLO
# ============================================================
# Para desarrollo: usar console backend (emails aparecen en la consola)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ============================================================
# 📧 CONFIGURACIÓN DE EMAILS - eGarage
# ============================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.atlantareciclajes.cl'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = 'contacto@atlantareciclajes.cl'
EMAIL_HOST_PASSWORD = 'laila2013@'
DEFAULT_FROM_EMAIL = 'eGarage <contacto@atlantareciclajes.cl>'

# Para desarrollo - desactivar emails reales (descomenta la siguiente línea si es necesario):
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Para producción (comentado):
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'mail.atlantareciclajes.cl'
# EMAIL_PORT = 465
# EMAIL_USE_SSL = True
# EMAIL_USE_TLS = False
# EMAIL_HOST_USER = 'suscripcion@atlantareciclajes.cl'
# EMAIL_HOST_PASSWORD = ')+y-k+[tY6w&'
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ============================================================
# 🔐 CONFIGURACIÓN DE ALLAUTH
# ============================================================
# Desactivar verificación de email para desarrollo
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_CONFIRM_EMAIL_ON_GET = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

# Configuraciones adicionales de allauth
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Backend de autenticación
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ID del sitio para allauth
SITE_ID = 1


