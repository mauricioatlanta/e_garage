# Adaptador personalizado para redirección según país
ACCOUNT_ADAPTER = 'taller.views_extra.account_adapter.CountryAwareAccountAdapter'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.atlantareciclajes.cl'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = 'suscripcion@atlantareciclajes.cl'
import os
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD', ',*naHZ0xIFO')
DEFAULT_FROM_EMAIL = 'eGarage <suscripcion@atlantareciclajes.cl>'
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
    'ubicacion.apps.UbicacionConfig',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # 🌐 Locale middleware PRIMERO
    'taller.middleware.country_url_migration.CountryURLRedirectMiddleware',  # Redirects legados /es/→/cl/
    'taller.middleware.country_context.CountryContextMiddleware',  # Detección de país
    'taller.middleware.i18n_country_middleware.CountryLanguageMiddleware',  # 🌐 Idioma por país DESPUÉS
    'taller.middleware.rate_limiting.RateLimitMiddleware',  # Rate limiting temprano
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'taller.middleware.company_country.CompanyCountryMiddleware',  # Nuevo middleware de tenant único
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'taller.middleware.empresa_middleware.EmpresaMiddleware',
    # 'taller.middlewares.activate_language',  # ❌ DESHABILITADO - CONFLICTO CON CountryLanguageMiddleware
    # 'taller.middleware.trial_middleware.TrialAccessMiddleware',  # 🔒 Trial de 30 días (descomentar para activar)
]

# Configuración de URLs
ROOT_URLCONF = 'gestion_taller.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates_canonical", BASE_DIR / "templates"],
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
                'django.template.context_processors.i18n',  # ✅ AGREGADO - Context processor de i18n
                'taller.context_processors.company_branding_context',  # ✅ NUESTRO - DEJAR SOLO ESTE
                # 'taller.context_processors.empresa_contexto',  # ❌ DESHABILITADO - CONFLICTO
                # 'taller.context_processors.namespaces.ui_namespaces',  # ❌ DESHABILITADO - CONFLICTO
                # 'taller.context_processors.company_branding',  # ❌ DESHABILITADO - CONFLICTO
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

# 🌍 INTERNACIONALIZACIÓN Y LOCALIZACIÓN
LANGUAGE_CODE = 'es'  # Español por defecto (Chile)
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Idiomas soportados
LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
]

# Directorio de traducciones
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Formatos por idioma (opcional)
FORMAT_MODULE_PATH = ['gestion_taller.formats']

# Configuración de cookies de idioma
LANGUAGE_COOKIE_NAME = 'django_language'
LANGUAGE_COOKIE_SAMESITE = 'Lax'
LANGUAGE_COOKIE_SECURE = False  # en local http
LANGUAGE_COOKIE_PATH = '/'

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
LOGIN_REDIRECT_URL = '/login/'  # Redirige a la vista country-aware después del login
ACCOUNT_LOGOUT_REDIRECT_URL = '/login/'  # Redirige a la vista country-aware después del logout
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Sin verificación de email para desarrollo
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 2
ACCOUNT_RATE_LIMITS = {
    "confirm_email": "1/m",
}

ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]

# Configuración de sesiones para "recordar credenciales"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 días por defecto
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Las sesiones persisten al cerrar el navegador

# Configuración para recordar login (allauth)
ACCOUNT_SESSION_REMEMBER = True  # Habilitar funcionalidad "recordar"
ACCOUNT_SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 días cuando se marca "recordar"

# Formulario personalizado de login
ACCOUNT_FORMS = {
    'login': 'taller.forms.custom_login.CustomLoginForm',
}

# Login default (actualizado para sistema multi-país con allauth global)
LOGIN_URL = '/accounts/login/'
