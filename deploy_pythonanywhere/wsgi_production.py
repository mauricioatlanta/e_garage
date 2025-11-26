#!/usr/bin/env python
"""
WSGI Configuration para PythonAnywhere - eGarage

⚠️ IMPORTANTE: Este archivo debe cargar las variables de entorno (.env)
antes de iniciar Django.

Instrucciones:
1. En PythonAnywhere, ve a "Web" → "WSGI configuration file"
2. Reemplaza todo el contenido con este archivo
3. Asegúrate de actualizar las rutas según tu configuración:
   - project_home: Ruta completa a tu proyecto
   - .env: Debe estar en el directorio del proyecto
"""

import os
import sys
from pathlib import Path

# ⚠️ ACTUALIZAR: Ruta completa a tu proyecto en PythonAnywhere
# Formato: /home/tuusuario/egarage
project_home = "/home/tuusuario/egarage"

# Agregar directorio del proyecto al path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# ⚠️ CRÍTICO: Cargar .env explícitamente en producción
# Esto asegura que las variables de entorno estén disponibles ANTES de Django
from dotenv import load_dotenv

env_path = Path(project_home) / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    # Opcional: Logging para verificar que se cargó
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"[WSGI] .env loaded from {env_path}")
else:
    # Si no existe .env, intentar cargar desde variables del sistema
    import logging

    logger = logging.getLogger(__name__)
    logger.warning(f"[WSGI] .env not found at {env_path}. Using system environment variables.")

# Configurar Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

# Cargar aplicación WSGI
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
