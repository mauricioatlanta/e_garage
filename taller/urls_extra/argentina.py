from django.shortcuts import redirect
from django.urls import path

from .chile import urlpatterns as chile_urlpatterns

# Chile ya define 'es/' dentro de sus urlpatterns, así que NO lo agregamos otra vez.
chile_no_root = [p for p in chile_urlpatterns if str(p.pattern) != ""]

urlpatterns = [
    path("", lambda request: redirect("/ar/es/")),
    *chile_no_root,
]
