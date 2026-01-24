"""
Context processors para e_garage
"""

import time

from django.conf import settings


def static_version(request):
    """
    Agrega versión para cache busting en archivos estáticos
    """
    return {"STATIC_VERSION": str(int(time.time())) if settings.DEBUG else "v1.0"}


def empresa_info(request):
    """
    Agrega información de la empresa del usuario autenticado
    """
    if request.user.is_authenticated and hasattr(request.user, "empresa"):
        return {
            "user_empresa": request.user.empresa,
            "country": request.user.empresa.pais if request.user.empresa else "CL",
            "company_settings": getattr(request.user.empresa, "configuracion", None),
        }
    return {
        "user_empresa": None,
        "country": "CL",
        "company_settings": None,
    }
