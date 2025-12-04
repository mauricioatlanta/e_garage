"""
URLs del Centro de Ayuda
"""

from django.urls import path

from .views import HelpArticuloView, HelpCategoriaView, HelpHomeView, help_buscar

app_name = "help"

urlpatterns = [
    path("", HelpHomeView.as_view(), name="home"),
    path("categoria/<slug:slug>/", HelpCategoriaView.as_view(), name="categoria"),
    path("articulo/<slug:slug>/", HelpArticuloView.as_view(), name="articulo"),
    path("buscar/", help_buscar, name="buscar"),
]
