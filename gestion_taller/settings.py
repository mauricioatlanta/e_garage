import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-recovery-key')
DEBUG = True
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = [
    'dal','dal_select2','django.contrib.admin','django.contrib.auth',
    'django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages',
    'django.contrib.staticfiles','django.contrib.sites','allauth','allauth.account',
    'allauth.socialaccount','gestion_taller','taller','marketplace','ubicacion'
]
SITE_ID = 1
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend','allauth.account.auth_backends.AuthenticationBackend']
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware','allauth.account.middleware.AccountMiddleware'
]
ROOT_URLCONF = 'gestion_taller.urls'
WSGI_APPLICATION = 'gestion_taller.wsgi.application'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates','DIRS': [os.path.join(BASE_DIR, 'templates')],'APP_DIRS': True,'OPTIONS': {'context_processors': ['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','taller.context_processors.subscription_notice.subscription_notice'],},}]
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3','NAME': BASE_DIR / 'db.sqlite3'}}
STATIC_URL = '/static/'
ALLOWED_HOSTS = ['egarage.cl', 'www.egarage.cl', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://egarage.cl', 'https://www.egarage.cl']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ALLOWED_HOSTS = ['egarage.cl', 'www.egarage.cl', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://egarage.cl', 'https://www.egarage.cl']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

EMAIL_BACKEND = 'gestion_taller.resend_backend.ResendBackend'
RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'support@egarage.cl')

# --- ARREGLO DE LOGIN ---
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
LOGIN_REDIRECT_URL = '/'

# Habilitar login por username o email
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'

# --- ARREGLO DE LOGIN ---
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
LOGIN_REDIRECT_URL = '/'

# Habilitar login por username o email
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'

import os

STATICFILES_DIRS = [BASE_DIR / 'static']

ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = False

# allauth 65.x - configuracion actualizada
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email', 'username*', 'password1*', 'password2*']

# Desactivar rate limit de allauth en desarrollo
ACCOUNT_RATE_LIMITS = {
    'login_failed': None,
    'login_attempt': None,
    'confirm_email': None,
    'password_reset': None,
    'password_reset_by_key': None,
    'signup': None,
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
