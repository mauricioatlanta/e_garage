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
    'taller',  # Asegúrate de que esta línea está presente
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'django.contrib.humanize',
]

# ============================================================
# 🔧 MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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
# 🌐 INTERNACIONALIZACIÓN
# ============================================================
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_L10N = True
USE_TZ = True

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
CRISPY_TEMPLATE_PACK = 'bootstrap4'


