"""URLs para endpoints AJAX compartidos."""

from django.urls import path

from . import views as ajax_custom
from .. import ajax_views
from ..views_extra import ajax as views_extra_ajax

app_name = "ajax"

urlpatterns = [
    # Rutas de clientes y vehículos (desde taller/ajax/views.py)
    path("clientes/buscar/", ajax_custom.buscar_clientes, name="buscar_clientes"),
    path(
        "vehiculos-por-cliente/",
        ajax_custom.vehiculos_por_cliente,
        name="vehiculos_por_cliente",
    ),
    # Rutas de ciudades (desde views_extra/ajax.py)
    path("ciudades-por-region/", views_extra_ajax.ciudades_por_region, name="ciudades_por_region"),
    # Rutas de marcas, modelos, motores y cajas (desde ajax_views.py)
    path("marcas/", ajax_views.ajax_marcas, name="ajax_marcas"),
    path("modelos/", ajax_views.ajax_modelos, name="ajax_modelos"),
    path("motores/", ajax_views.ajax_motores, name="ajax_motores"),
    path("cajas/", ajax_views.ajax_cajas, name="ajax_cajas"),
]
