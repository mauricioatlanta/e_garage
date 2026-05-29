"""
Vista de registro exitoso - muestra mensaje después del registro
"""

from django.shortcuts import render

from taller.config.country_settings import CountrySettings
from taller.utils.country_config import build_bienvenida_url, get_country_config


def registro_exitoso(request):
    """
    Muestra página de registro exitoso.

    Requisitos:
    - Mensaje de éxito
    - Email del usuario (desde sesión)
    - Instrucciones para revisar correo
    - Botón para volver a landing del país
    """
    # Obtener email de la sesión
    email = request.session.get("registro_email", "")

    # Detectar país desde URL
    country_code = (
        CountrySettings.get_country_from_url(request.path)
        or getattr(request, "country_code", None)
        or "CL"
    )
    country_code = country_code.upper()

    # Obtener configuración del país
    country_config = get_country_config(country_code)

    # URL de bienvenida con idioma: /cl/es/bienvenida/, /us/en/bienvenida/, etc.
    bienvenida_url = build_bienvenida_url(country_code, request)

    context = {
        "email": email,
        "country_code": country_code,
        "country_config": country_config,
        "bienvenida_url": bienvenida_url,
    }

    return render(request, "taller/auth/registro_exitoso.html", context)
