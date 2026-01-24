import os
import sys
from dotenv import load_dotenv

PROJECT_PATH = "/home/atlantareciclajes/apps/egarage/current"
ENV_PATH = os.path.join(PROJECT_PATH, ".env")

if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

# Cargar .env primero (si existe)
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)

# ======================================================
# CONFIGURACION DE VARIABLES DE ENTORNO PARA GMAIL
# ======================================================
# IMPORTANTE: Estas variables SOBRESCRIBEN las del .env
# Se cargan DESPUES del .env pero ANTES de Django
# ======================================================
os.environ['EMAIL_HOST'] = 'smtp.gmail.com'
os.environ['EMAIL_PORT'] = '587'
os.environ['EMAIL_USE_TLS'] = 'True'
os.environ['EMAIL_USE_SSL'] = 'False'
os.environ['EMAIL_HOST_USER'] = 'mauricioatlanta@gmail.com'
os.environ['EMAIL_PASSWORD'] = 'aohulwlfwzfvqajz'  # App Password de Gmail
os.environ['DEFAULT_FROM_EMAIL'] = 'eGarage <mauricioatlanta@gmail.com>'

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
