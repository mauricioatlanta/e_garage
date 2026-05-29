import os

from django.core.wsgi import get_wsgi_application

# 🔥 FORZAR settings_prod en producción (no usar setdefault)
# Esto evita que systemd/gunicorn sea pisado por configuración de desarrollo
os.environ["DJANGO_SETTINGS_MODULE"] = "gestion_taller.settings_prod"

application = get_wsgi_application()
