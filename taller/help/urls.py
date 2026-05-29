"""
URLs del Centro de Ayuda
"""

from django.urls import path

from .views import (
    HelpArticuloView,
    HelpCategoriaView,
    HelpHomeView,
    api_faqs,
    api_panel_ayuda_config,
    api_pasos_recomendados,
    help_buscar,
)

app_name = "help"

urlpatterns = [
    path("", HelpHomeView.as_view(), name="home"),
    path("categoria/<slug:slug>/", HelpCategoriaView.as_view(), name="categoria"),
    path("articulo/<slug:slug>/", HelpArticuloView.as_view(), name="articulo"),
    path("buscar/", help_buscar, name="buscar"),
    # APIs para contenido extensible
    path("api/faqs/", api_faqs, name="api_faqs"),
    path("api/faqs/<str:modulo>/", api_faqs, name="api_faqs_modulo"),
    path("api/pasos/", api_pasos_recomendados, name="api_pasos"),
    path("api/pasos/<str:modulo>/", api_pasos_recomendados, name="api_pasos_modulo"),
    path("api/config/", api_panel_ayuda_config, name="api_panel_config"),
]
