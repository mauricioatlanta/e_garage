from django.urls import path

from .ajax import views as ajax_custom
from . import ajax_views

app_name = "ajax"

urlpatterns = [
    # Rutas de clientes y vehículos (desde views_extra/ajax.py)
    path("clientes/buscar/", ajax_custom.buscar_clientes, name="buscar_clientes"),
    path(
        "vehiculos-por-cliente/",
        ajax_custom.vehiculos_por_cliente,
        name="vehiculos_por_cliente",
    ),
    path("ciudades-por-region/", ajax_views.ciudades_por_region, name="ciudades_por_region"),
    # Rutas de marcas, modelos, motores y cajas (desde ajax_views.py)
    path("marcas/", ajax_views.ajax_marcas, name="ajax_marcas"),
    path("modelos/", ajax_views.ajax_modelos, name="ajax_modelos"),
    path("motores/", ajax_views.ajax_motores, name="ajax_motores"),
    path("cajas/", ajax_views.ajax_cajas, name="ajax_cajas"),
]
