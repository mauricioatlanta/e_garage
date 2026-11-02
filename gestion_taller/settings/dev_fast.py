from gestion_taller.settings.dev import *

ROOT_URLCONF = "gestion_taller.urls"

INSTALLED_APPS = [a for a in INSTALLED_APPS if a]

MIDDLEWARE = [m for m in MIDDLEWARE if m]

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Evita freeze mimetypes windows py313
import mimetypes
mimetypes.init(files=[])

