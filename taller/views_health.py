"""
Health check endpoint para monitoreo de producción
"""

from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Endpoint de health check para monitoreo
    Devuelve 200 OK si el sistema está funcionando correctamente
    """
    try:
        # Verificar conexión a base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "OK"
    except Exception as e:
        db_status = f"ERROR: {str(e)}"
    
    # Verificar configuración básica
    config_status = {
        "DEBUG": settings.DEBUG,
        "ALLOWED_HOSTS": settings.ALLOWED_HOSTS,
        "STATICFILES_STORAGE": getattr(settings, 'STATICFILES_STORAGE', 'Not configured'),
    }
    
    # Verificar archivos estáticos críticos
    import os
    static_files = {
        "documentos_form.js": os.path.exists("static/taller/common/js/documentos_form.js"),
        "staticfiles_dir": os.path.exists(getattr(settings, 'STATIC_ROOT', '')),
    }
    
    # Determinar estado general
    overall_status = "OK" if db_status == "OK" else "ERROR"
    
    response_data = {
        "status": overall_status,
        "database": db_status,
        "configuration": config_status,
        "static_files": static_files,
        "timestamp": str(timezone.now()),
    }
    
    # Devolver 200 OK o 500 ERROR según el estado
    status_code = 200 if overall_status == "OK" else 500
    
    return JsonResponse(response_data, status=status_code)


def health_simple(request):
    """
    Health check minimalista para Render/PythonAnywhere
    Devuelve solo {"status": "ok"} si todo está bien
    """
    try:
        # Verificar conexión a base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
