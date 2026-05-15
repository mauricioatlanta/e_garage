import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = 'django-insecure-recovery-key'
DEBUG = False
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
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates','DIRS': [os.path.join(BASE_DIR, 'templates')],'APP_DIRS': True,'OPTIONS': {'context_processors': ['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages'],},}]
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3','NAME': BASE_DIR / 'db.sqlite3'}}
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
ALLOWED_HOSTS = ['egarage.cl', 'www.egarage.cl', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://egarage.cl', 'https://www.egarage.cl']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ALLOWED_HOSTS = ['egarage.cl', 'www.egarage.cl', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://egarage.cl', 'https://www.egarage.cl']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

EMAIL_BACKEND = 'gestion_taller.resend_backend.ResendBackend'
RESEND_API_KEY = 're_ayHbTkv4_F3rhviV1ewsWBhBH2Cm8dgNp'
DEFAULT_FROM_EMAIL = 'support@egarage.cl'

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


STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
