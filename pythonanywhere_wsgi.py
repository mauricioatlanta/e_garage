"""
Archivo WSGI para PythonAnywhere
Edita este archivo desde el panel Web → WSGI configuration file.
"""

import os
import sys
from pathlib import Path

# --- Rutas del proyecto ---
# Ajusta a tu estructura real en PA
project_root = Path("/home/tu_usuario/e_garage")  # <--- CAMBIA por tu ruta real
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# --- Entorno Django ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
os.environ.setdefault("DEBUG", "False")

# Opcional: variables adicionales
# os.environ.setdefault("ALLOWED_HOSTS", "tu-usuario.pythonanywhere.com, www.tudominio.cl, tudominio.cl")
# os.environ.setdefault("CSRF_TRUSTED_ORIGINS", "https://tu-usuario.pythonanywhere.com, https://www.tudominio.cl, https://tudominio.cl")

# --- Aplicación WSGI ---
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# ---- SERVIR STATIC/MEDIA EN NGINX DE PA (se configura en el panel Web) ----
# En PythonAnywhere, los archivos estáticos y de media NO se sirven aquí.
# Mapea rutas en el panel Web:
#   Static files:
#       URL:  /static/ -> /home/tu_usuario/e_garage/staticfiles
#   Media files:
#       URL:  /media/  -> /home/tu_usuario/e_garage/media
