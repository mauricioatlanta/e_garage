from django.shortcuts import redirect
from django.urls import path
from django.views.generic import TemplateView

from .chile import urlpatterns as chile_urlpatterns

chile_no_root = [p for p in chile_urlpatterns if str(p.pattern) != ""]

def strip_es(request, rest=""):
    # /uy/es/...  -> /uy/...
    return redirect(f"/uy/{rest}".rstrip("/") + ("/" if rest and not rest.endswith("/") else ""))

urlpatterns = [
    path("es/", strip_es),
    path("es/<path:rest>", strip_es),

    # Home UY (usa tu template UY)
    path("", TemplateView.as_view(template_name="uy/es/onboarding/bienvenida.html")),

    *chile_no_root,
]
