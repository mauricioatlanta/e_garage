from django.shortcuts import redirect
from django.urls import path

from .chile import urlpatterns as chile_urlpatterns

chile_no_root = [p for p in chile_urlpatterns if str(p.pattern) != ""]

urlpatterns = [
    path("", lambda request: redirect("/uy/es/")),
    *chile_no_root,
]
