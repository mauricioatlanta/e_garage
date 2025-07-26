EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.atlantareciclajes.cl'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False

EMAIL_HOST_USER = 'suscripcion@atlantareciclajes.cl'
EMAIL_HOST_PASSWORD = ')+y-k+[tY6w&'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
from pathlib import Path
import os
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", get_random_secret_key())
DEBUG = True
ALLOWED_HOSTS = ['*']

# Aplicaciones instaladas
INSTALLED_APPS = [
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'dal',
    'dal_select2',
    'crispy_forms',
    'crispy_bootstrap5',
    'taller',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'django.contrib.humanize',
    'widget_tweaks',
    'django.contrib.sites',
    'rest_framework',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'taller.middleware.simple_translation.SimpleTranslationMiddleware',  # Simple translation middleware
    'django.middleware.locale.LocaleMiddleware',  # Para internacionalización
    'taller.middleware.rate_limiting.RateLimitMiddleware',  # Rate limiting temprano
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'taller.middleware.empresa_middleware.EmpresaMiddleware',
]

# Configuración de URLs
ROOT_URLCONF = 'gestion_taller.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'taller.context_processors.empresa_contexto',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_taller.wsgi.application'

# Base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Localización
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Idiomas disponibles
LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
]

# Directorio de traducciones
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Archivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# Archivos subidos por el usuario
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'



# Configuración general
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
APPEND_SLASH = True

# Mimetypes útiles en desarrollo
if DEBUG:
    import mimetypes
    mimetypes.add_type("text/css", ".css", True)
    mimetypes.add_type("application/javascript", ".js", True)

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = ["bootstrap5"]
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Autocomplete Light
AUTOCOMPLETE_LIGHT = {
    'SELECT2': {
        'i18n': False,
        'language': None
    }
}

# Django Allauth
SITE_ID = 1
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)
LOGIN_REDIRECT_URL = '/dashboard/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/login/'
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # Ahora requiere verificación de email para activar la cuenta
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 2
ACCOUNT_RATE_LIMITS = {
    "confirm_email": "1/m",
}

ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]

# Login default (no usado si usas Allauth)
LOGIN_URL = '/admin/login/'
