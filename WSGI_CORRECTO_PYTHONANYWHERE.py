#!/usr/bin/env python
# ======================================================
# WSGI Configuration para PythonAnywhere - eGarage
# ======================================================
# Archivo: /var/www/www_egarage_cl_wsgi.py
# ======================================================

import os
import sys
from pathlib import Path

# Ruta del proyecto
project_home = "/home/atlantareciclajes/apps/egarage/current"

# Agregar directorio del proyecto al path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Cambiar al directorio del proyecto
os.chdir(project_home)

# Cargar variables de entorno (.env) si existe
try:
    from dotenv import load_dotenv

    env_path = Path(project_home) / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # dotenv no está instalado, continuar sin él

# Configurar Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

# Cargar aplicación WSGI
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
