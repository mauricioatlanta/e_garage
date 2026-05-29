"""eGarage — módulo limpiado para pre-commit (docstring al inicio)."""

# """
# ===============================================================
# 🚀 CONFIGURACIÓN WSGI PARA DIGITALOCEAN - eGARAGE
# ===============================================================
# Configuración WSGI optimizada para el despliegue en DigitalOcean
# URL: https://e-garage-atlantareciclajes
# Usuario: atlantareciclajes
# Fecha: 24 de julio de 2025

# INSTRUCCIONES PARA DIGITALOCEAN:
# 1. Copiar este archivo como wsgi.py en el directorio principal
# 2. Asegurarse de que la ruta del proyecto sea correcta
# 3. Verificar que el módulo de configuración esté disponible
# ===============================================================
# """

import os
import sys
from pathlib import Path

# ============================================================
# 📁 CONFIGURACIÓN DE RUTAS
# ============================================================
# Ruta del proyecto en DigitalOcean
PROJECT_PATH = "/home/atlantareciclajes/e_garage"
VENV_PATH = "/home/atlantareciclajes/.virtualenvs/e_garage_env"

# Agregar el directorio del proyecto al path de Python
if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

# Agregar el directorio padre del proyecto
parent_path = str(Path(PROJECT_PATH).parent)
if parent_path not in sys.path:
    sys.path.insert(0, parent_path)

# ============================================================
# 🌍 CONFIGURACIÓN DE ENTORNO
# ============================================================
# Configurar el módulo de configuración de Django
# ===============================================================
# 🔧 CONFIGURACIÓN DE ENTORNO
# ===============================================================
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_garage.settings_production")

# Variables de entorno para producción
os.environ.setdefault("DB_NAME", "atlantareciclajes$egarage")
os.environ.setdefault("DB_USER", "atlantareciclajes")
os.environ.setdefault("DB_PASSWORD", "laila2013@")
os.environ.setdefault("DB_HOST", "atlantareciclajes.mysql.digitalocean-services.com")
os.environ.setdefault("DB_PORT", "3306")

# Clave secreta (en producción debería estar en variables de entorno)
os.environ.setdefault(
    "DJANGO_SECRET_KEY", "ej+v^g#=l@x+$#$n&8k3w#!zf_9z8j@4m5n6p7q8r9s0t1u2v3w4x5y6z"
)

# ============================================================
# 🚀 INICIALIZACIÓN DE DJANGO
# ============================================================
try:
    import django
    from django.core.wsgi import get_wsgi_application

    # Configurar Django
    django.setup()

    # Obtener la aplicación WSGI
    application = get_wsgi_application()

    print("✅ WSGI configurado exitosamente para DigitalOcean")
    print(f"📁 Proyecto: {PROJECT_PATH}")
    print("🗄️ Base de datos: MySQL en DigitalOcean")
    print("🌐 Configuración: e_garage.settings_production")

except Exception as e:
    print(f"❌ Error al configurar WSGI: {e}")
    raise


# ============================================================
# 🔧 CONFIGURACIÓN ADICIONAL PARA DIGITALOCEAN
# ============================================================
def application_with_logging(environ, start_response):
    """
    Wrapper para agregar logging a la aplicación WSGI
    """
    try:
        return application(environ, start_response)
    except Exception as e:
        import traceback

        error_msg = f"Error en aplicación WSGI: {e}\n{traceback.format_exc()}"
        print(error_msg)

        # Respuesta de error básica
        status = "500 Internal Server Error"
        headers = [("Content-Type", "text/html")]
        start_response(status, headers)

        return [
            b"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error 500 - eGarage</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .error { background: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="error">
                <h1>Error 500 - Servidor en Mantenimiento</h1>
                <p>El sistema eGarage esta temporalmente fuera de servicio.</p>
                <p>Por favor, contacte al administrador: contacto@atlantareciclajes.cl</p>
            </div>
        </body>
        </html>
        """
        ]


# Usar el wrapper con logging en lugar de la aplicación directa
# application = application_with_logging  # Descomenta si quieres logging adicional

# ============================================================
# 📝 NOTAS IMPORTANTES PARA DIGITALOCEAN:
# ============================================================
# """
# CONFIGURACIÓN EN DIGITALOCEAN WEB APP:

# 1. WSGI configuration file:
#    - Ubicación: /var/www/atlantareciclajes_digitalocean_com_wsgi.py
#    - Copiar este contenido al archivo WSGI de DigitalOcean

# 2. Static files:
#    - URL: /static/
#    - Directory: /home/atlantareciclajes/e_garage/staticfiles/

# 3. Media files:
#    - URL: /media/
#    - Directory: /home/atlantareciclajes/e_garage/media/

# 4. Virtualenv:
#    - Path: /home/atlantareciclajes/.virtualenvs/e_garage_env

# 5. Source code:
#    - Path: /home/atlantareciclajes/e_garage

# COMANDOS POST-DESPLIEGUE:
# - python manage.py collectstatic --noinput
# - python manage.py migrate
# - python manage.py createsuperuser (si es necesario)

# VARIABLES DE ENTORNO:
# - Configurar en .bashrc o en el dashboard de DigitalOcean
# - DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DJANGO_SECRET_KEY
# """
