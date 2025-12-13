from django.shortcuts import redirect
from django.urls import include, path

from .chile import urlpatterns as chile_urlpatterns

# Reusar rutas de Chile, pero SIN la ruta raíz ('') que redirige a /cl/
chile_no_root = [p for p in chile_urlpatterns if str(p.pattern) != ""]

urlpatterns = [
    # Canonical AR: /ar/ -> /ar/es/
    path("", lambda request: redirect("/ar/es/")),
    # Rutas reales bajo /ar/es/...
    path("es/", include((chile_no_root, "argentina"))),
]
