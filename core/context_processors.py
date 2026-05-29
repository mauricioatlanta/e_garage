"""
Context processors para e_garage
"""

import time

from django.conf import settings
from taller.utils.empresa import get_user_empresa_safe


def static_version(request):
    """
    Agrega versión para cache busting en archivos estáticos
    """
    return {"STATIC_VERSION": str(int(time.time())) if settings.DEBUG else "v1.0"}


def empresa_info(request):
    """
    Agrega información de la empresa del usuario autenticado
    """
    empresa = get_user_empresa_safe(getattr(request, "user", None))
    if empresa:
        return {
            "user_empresa": empresa,
            "country": getattr(empresa, "pais", "CL") or "CL",
            "company_settings": getattr(empresa, "configuracion", None),
        }
    return {
        "user_empresa": None,
        "country": "CL",
        "company_settings": None,
    }
