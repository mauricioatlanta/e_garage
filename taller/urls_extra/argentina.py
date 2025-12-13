from django.shortcuts import redirect
from django.urls import path
from django.views.generic import TemplateView

from .chile import urlpatterns as chile_urlpatterns

# Quitamos la raíz de Chile para que no nos mande a /cl/
chile_no_root = [p for p in chile_urlpatterns if str(p.pattern) != ""]

def strip_es(request, rest=""):
    # /ar/es/...  -> /ar/...
    return redirect(f"/ar/{rest}".rstrip("/") + ("/" if rest and not rest.endswith("/") else ""))

urlpatterns = [
    # Alias: /ar/es/ -> /ar/
    path("es/", strip_es),
    path("es/<path:rest>", strip_es),

    # Home AR (usa tu template AR)
    path("", TemplateView.as_view(template_name="ar/es/onboarding/bienvenida.html")),

    # Reuso completo de rutas Chile bajo /ar/...
    *chile_no_root,
]
