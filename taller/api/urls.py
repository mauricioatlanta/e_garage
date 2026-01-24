from django.urls import path

from taller.api import views

app_name = "api"

urlpatterns = [
    path("status/", views.api_status, name="api_status"),
    path("tiendas/crear/", views.crear_tienda_api, name="crear_tienda_api"),
    path("clientes/", views.api_listar_clientes, name="listar_clientes"),
    path("clientes/buscar/", views.buscar_clientes_api, name="buscar_clientes_api"),
    path("clientes/<int:cliente_id>/", views.info_cliente_api, name="info_cliente_api"),
    path("clientes/<int:cliente_id>/verificar-facturacion/", views.api_verificar_facturacion_cliente, name="verificar_facturacion_cliente"),
    path("clientes/<int:cliente_id>/completar-facturacion/", views.api_completar_datos_facturacion, name="completar_facturacion_cliente"),
    path(
        "vehiculos/<int:cliente_id>/",
        views.vehiculos_cliente_api,
        name="vehiculos_cliente_api",
    ),
    path("repuestos/by-code", views.repuesto_by_code_api, name="repuesto_by_code_api"),
    path("repuestos/", views.buscar_repuestos_api, name="buscar_repuestos_api"),
    path("repuestos/crear/", views.crear_repuesto_api, name="crear_repuesto_api"),
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
    # Onboarding APIs
    path("clientes/crear/", views.api_crear_cliente_onboarding, name="crear_cliente_onboarding"),
    path("vehiculos/crear/", views.api_crear_vehiculo_onboarding, name="crear_vehiculo_onboarding"),
    # API para procesar foto de patente
    path("vehiculos/procesar-foto-patente/", views.api_procesar_foto_patente, name="procesar_foto_patente"),
]
