# URLs para vistas AJAX jerárquicas
from django.urls import path

from taller import ajax_views

ajax_urlpatterns = [
    path("ajax/load-modelos/", ajax_views.load_modelos, name="ajax_load_modelos"),
    path("ajax/load-motores/", ajax_views.load_motores, name="ajax_load_motores"),
    path("ajax/load-cajas/", ajax_views.load_cajas, name="ajax_load_cajas"),
    path(
        "ajax/load-motores-cajas/",
        ajax_views.load_motores_cajas,
        name="ajax_load_motores_cajas",
    ),
]

# Para agregar a tu urls.py principal:
# from taller.ajax_views import ajax_urlpatterns
# urlpatterns += ajax_urlpatterns
