"""
Vista personalizada para redirecciones que preservan el contexto de pais
"""

from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse

from taller.utils.country_routing import canonical_lang_for_country, default_lang_for_country
from taller.utils.url_strategy import build_country_lang_path


def redirect_documento_crear(request):
    """
    Redirige usando el namespace activo del request.
    """
    return redirect(reverse("documentos:documento_crear"))


def redirect_documento_editar(request, pk):
    """
    Redireccion inteligente para editar que preserva el contexto del pais.
    Canonicaliza siempre hacia rutas con pais + idioma.
    De /cl/documentos/nuevo-editar/X/ -> /cl/es/documentos/editar/X/
    De /us/documentos/nuevo-editar/X/ -> /us/en/documentos/editar/X/
    """
    country = (
        getattr(request, "country_from_host", None) or getattr(request, "country", None) or "CL"
    )
    lang = getattr(request, "LANGUAGE_CODE", None) or default_lang_for_country(country)
    lang = canonical_lang_for_country(country, lang)
    target = build_country_lang_path(request, country, lang, f"/documentos/editar/{pk}/")
    return HttpResponseRedirect(target)
