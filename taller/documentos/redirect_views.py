"""
Vista personalizada para redirecciones que preservan el contexto de país
"""

from django.http import HttpResponseRedirect


def redirect_documento_crear(request):
    """
    Redirección inteligente que preserva el contexto del país.
    De /cl/documentos/nuevo/ -> /cl/documentos/form/
    De /us/documentos/nuevo/ -> /us/documentos/form/
    """
    # Obtener el país desde el contexto del request
    country = getattr(request, "country", None)

    if country == "CL":
        return HttpResponseRedirect("/cl/documentos/form/")
    elif country == "US":
        return HttpResponseRedirect("/us/documentos/form/")
    else:
        # Fallback: determinar por la URL actual
        path = request.path
        if "/cl/" in path:
            return HttpResponseRedirect("/cl/documentos/form/")
        elif "/us/" in path:
            return HttpResponseRedirect("/us/documentos/form/")
        else:
            # Último fallback
            return HttpResponseRedirect("/us/documentos/form/")


def redirect_documento_editar(request, pk):
    """
    Redirección inteligente para editar que preserva el contexto del país.
    De /cl/documentos/nuevo-editar/X/ -> /cl/documentos/editar/X/
    De /us/documentos/nuevo-editar/X/ -> /us/documentos/editar/X/
    """
    # Obtener el país desde el contexto del request
    country = getattr(request, "country", None)

    if country == "CL":
        return HttpResponseRedirect(f"/cl/documentos/editar/{pk}/")
    elif country == "US":
        return HttpResponseRedirect(f"/us/documentos/editar/{pk}/")
    else:
        # Fallback: determinar por la URL actual
        path = request.path
        if "/cl/" in path:
            return HttpResponseRedirect(f"/cl/documentos/editar/{pk}/")
        elif "/us/" in path:
            return HttpResponseRedirect(f"/us/documentos/editar/{pk}/")
        else:
            # Último fallback
            return HttpResponseRedirect(f"/us/documentos/editar/{pk}/")
