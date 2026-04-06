"""
Vista personalizada para redirecciones que preservan el contexto de pais
"""

from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse


def redirect_documento_crear(request):
    """
    Redireccion inteligente que preserva el contexto del pais.
    Canonicaliza siempre hacia rutas con pais + idioma.
    De /cl/documentos/nuevo/ -> /cl/es/documentos/form/
    De /us/documentos/nuevo/ -> /us/en/documentos/form/
    """
    path = request.path
    namespace_by_prefix = (
        ("/cl/es/", "chile:documentos:documento_crear"),
        ("/us/en/", "us_en:documentos:documento_crear"),
        ("/us/es/", "us_es:documentos:documento_crear"),
        ("/cl/", "chile:documentos:documento_crear"),
        ("/us/", "us_en:documentos:documento_crear"),
    )

    for prefix, route_name in namespace_by_prefix:
        if path.startswith(prefix):
            return redirect(reverse(route_name))

    country = (getattr(request, "country", None) or "").upper()
    country_fallbacks = {
        "CL": "chile:documentos:documento_crear",
        "US": "us_en:documentos:documento_crear",
    }
    return redirect(reverse(country_fallbacks.get(country, "chile:documentos:documento_crear")))


def redirect_documento_editar(request, pk):
    """
    Redireccion inteligente para editar que preserva el contexto del pais.
    Canonicaliza siempre hacia rutas con pais + idioma.
    De /cl/documentos/nuevo-editar/X/ -> /cl/es/documentos/editar/X/
    De /us/documentos/nuevo-editar/X/ -> /us/en/documentos/editar/X/
    """
    # Obtener el pais desde el contexto del request
    country = getattr(request, "country", None)

    if country == "CL":
        return HttpResponseRedirect(f"/cl/es/documentos/editar/{pk}/")
    elif country == "US":
        return HttpResponseRedirect(f"/us/en/documentos/editar/{pk}/")
    else:
        # Fallback: determinar por la URL actual
        path = request.path
        if "/cl/es/" in path or "/cl/" in path:
            return HttpResponseRedirect(f"/cl/es/documentos/editar/{pk}/")
        elif "/us/es/" in path:
            return HttpResponseRedirect(f"/us/es/documentos/editar/{pk}/")
        elif "/us/en/" in path or "/us/" in path:
            return HttpResponseRedirect(f"/us/en/documentos/editar/{pk}/")
        else:
            # Ultimo fallback
            return HttpResponseRedirect(f"/cl/es/documentos/editar/{pk}/")
