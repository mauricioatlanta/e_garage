from django.shortcuts import redirect
from django.urls import include, path

from .chile import urlpatterns as chile_urlpatterns

# Reusar rutas de Chile, pero SIN la ruta raíz ('') que redirige a /cl/
chile_no_root = [p for p in chile_urlpatterns if str(p.pattern) != ""]

urlpatterns = [
    # Canonical UY: /uy/ -> /uy/es/
    path("", lambda request: redirect("/uy/es/")),
    # Rutas reales bajo /uy/es/...
    path("es/", include((chile_no_root, "uruguay"))),
]
