import os

env = os.environ.get("EGARAGE_ENV", "dev").lower()
if env == "prod":
    from .prod import *
elif env == "min":
    from .min import *
else:
    from .dev import *

    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.locale.LocaleMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "allauth.account.middleware.AccountMiddleware",  # 👈 OBLIGATORIO PARA ALLAUTH
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "taller.middleware.empresa_middleware.EmpresaMiddleware",
        "taller.middleware.verificar_suscripcion.VerificarSuscripcionMiddleware",
    ]
