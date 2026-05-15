# ============================================================
# 🚀 CONFIGURACIÓN WSGI PARA PYTHONANYWHERE
# ============================================================
# Archivo: wsgi_pythonanywhere.py
# URL de producción: https://e-garage-atlantareciclajes.pythonanywhere.com

import os
import sys

# Añadir el path del proyecto al Python path
path = "/home/atlantareciclajes/e_garage"
if path not in sys.path:
    sys.path.insert(0, path)

# Configurar el módulo de settings para producción
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_garage.settings_production")

# Importar la aplicación WSGI de Django
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

print("🚀 WSGI Application cargada para PythonAnywhere")
