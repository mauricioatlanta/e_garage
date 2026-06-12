import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-recovery-key')
DEBUG = os.getenv('DJANGO_DEBUG', '1').lower() in {'1', 'true', 'yes', 'on'}
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = [
    'dal','dal_select2','django.contrib.admin','django.contrib.auth',
    'django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages',
    'django.contrib.staticfiles','django.contrib.humanize','django.contrib.sites','allauth','allauth.account',
    'allauth.socialaccount','gestion_taller','taller','marketplace','ubicacion',
    'widget_tweaks'
]
SITE_ID = 1
LANGUAGE_CODE = 'es'
LOCALE_PATHS = [BASE_DIR / 'locale']
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend','allauth.account.auth_backends.AuthenticationBackend']
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'taller.middleware.empresa_resolver.EmpresaResolverMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware','allauth.account.middleware.AccountMiddleware'
]
ROOT_URLCONF = 'gestion_taller.urls'
WSGI_APPLICATION = 'gestion_taller.wsgi.application'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates','DIRS': [os.path.join(BASE_DIR, 'templates')],'APP_DIRS': True,'OPTIONS': {'context_processors': ['django.template.context_processors.debug','django.template.context_processors.request','django.template.context_processors.i18n','django.contrib.auth.context_processors.auth','django.template.context_processors.media','django.template.context_processors.static','django.template.context_processors.tz','django.contrib.messages.context_processors.messages','taller.context_processors.empresa_contexto','taller.context_processors.namespaces.ui_namespaces','taller.context_processors.company_context','taller.context_processors.company_branding','taller.context_processors.company_header','taller.context_processors.panel_chrome.us_authenticated_compact_chrome','taller.context_processors.panel_chrome.us_signup_slim_header','taller.context_processors.ui_labels.ui_labels_context','taller.context_processors.subscription_notice.subscription_notice'],},}]
_db_path = os.getenv('DJANGO_DB_PATH') or str(BASE_DIR / 'db.sqlite3')
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': _db_path}}
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = ['https://egarage.cl', 'https://www.egarage.cl']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = ['https://egarage.cl', 'https://www.egarage.cl']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'support@egarage.cl')
SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', DEFAULT_FROM_EMAIL)
# Local: console para ver emails en terminal. Producción: sobreescribir con env var.
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# --- Auth / allauth ---
LOGIN_REDIRECT_URL = '/'
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = False
ACCOUNT_ADAPTER = 'taller.views_extra.account_adapter.CountryAwareAccountAdapter'
# 'optional': allauth envía el email de verificación pero no lo exige para hacer login.
# En producción sobreescribir con ACCOUNT_EMAIL_VERIFICATION=mandatory en el env.
ACCOUNT_EMAIL_VERIFICATION = os.getenv('ACCOUNT_EMAIL_VERIFICATION', 'optional')
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']

# --- Payments: Flow / MercadoPago / PayPal ---
FLOW_API_KEY = (os.getenv('FLOW_API_KEY') or '').strip()
FLOW_SECRET_KEY = (os.getenv('FLOW_SECRET_KEY') or '').strip()
FLOW_API_URL = (os.getenv('FLOW_API_URL') or 'https://sandbox.flow.cl/api').strip()
FLOW_URL_RETURN = (os.getenv('FLOW_URL_RETURN') or '').strip()
FLOW_URL_CONFIRMATION = (os.getenv('FLOW_URL_CONFIRMATION') or '').strip()
FLOW_TIMEOUT = int(os.getenv('FLOW_TIMEOUT', '15'))
FLOW_ENABLED = os.getenv(
    'FLOW_ENABLED',
    '1' if FLOW_API_KEY and FLOW_SECRET_KEY else '0',
).lower() in {'1', 'true', 'yes', 'on'}

MERCADOPAGO_ACCESS_TOKEN = (os.getenv('MERCADOPAGO_ACCESS_TOKEN') or '').strip()
MERCADOPAGO_PUBLIC_KEY = (os.getenv('MERCADOPAGO_PUBLIC_KEY') or '').strip()
MP_ACCESS_TOKEN = MERCADOPAGO_ACCESS_TOKEN
MP_PUBLIC_KEY = MERCADOPAGO_PUBLIC_KEY
MP_URL_SUCCESS = (os.getenv('MP_URL_SUCCESS') or '').strip()
MP_URL_FAILURE = (os.getenv('MP_URL_FAILURE') or '').strip()
MP_URL_PENDING = (os.getenv('MP_URL_PENDING') or '').strip()
MP_URL_WEBHOOK = (os.getenv('MP_URL_WEBHOOK') or '').strip()
MP_TIMEOUT = int(os.getenv('MP_TIMEOUT', '15'))
MP_ENABLED = os.getenv(
    'MP_ENABLED',
    '1' if MP_ACCESS_TOKEN else '0',
).lower() in {'1', 'true', 'yes', 'on'}

PAYPAL_BUSINESS_EMAIL = (os.getenv('PAYPAL_BUSINESS_EMAIL') or SUPPORT_EMAIL).strip()


STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
