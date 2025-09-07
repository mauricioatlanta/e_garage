from django.urls import path

from taller.api import views

app_name = "api"

urlpatterns = [
    path("status/", views.api_status, name="api_status"),
    path("tiendas/crear/", views.crear_tienda_api, name="crear_tienda_api"),
    path("clientes/", views.buscar_clientes_api, name="buscar_clientes_api"),
    path(
        "vehiculos/<int:cliente_id>/",
        views.vehiculos_cliente_api,
        name="vehiculos_cliente_api",
    ),
    path("repuestos/by-code", views.repuesto_by_code_api, name="repuesto_by_code_api"),
    path("repuestos/", views.buscar_repuestos_api, name="buscar_repuestos_api"),
    path("servicios/", views.buscar_servicios_api, name="buscar_servicios_api"),
    path(
        "otros-servicios/",
        views.buscar_otros_servicios_api,
        name="buscar_otros_servicios_api",
    ),
    path("modelos/", views.buscar_modelos_api, name="buscar_modelos_api"),
    path("motores/", views.buscar_motores_api, name="buscar_motores_api"),
    path("cajas/", views.buscar_cajas_api, name="buscar_cajas_api"),
    path("ops-metrics/", views.ops_metrics_api, name="ops_metrics"),
]
