from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "egarage_db_ensayo",
        "USER": "egarage_user",
        "PASSWORD": "egarage_ensayo_local",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}

DEBUG = True
ALLOWED_HOSTS = ["*"]
