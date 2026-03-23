# taller/urls_desarme.py
# Carga vistas sin exigir PiezaDesarme en el import (evita 404 si el modelo falla al cargar).

from django.shortcuts import redirect, render
from django.urls import path


def _desarme_fallback_index(request):
    """Fallback cuando el módulo desarme no carga: redirige al listado según path."""
    path_str = (request.path or "").strip("/")
    if "us/" in path_str or path_str.startswith("us"):
        return redirect("/us/en/desarme/vehiculos/")
    return redirect("/cl/es/desarme/vehiculos/")


def _desarme_fallback_unavailable(request):
    """Página simple cuando el módulo desarme no está disponible (evita 404 en /desarme/vehiculos/)."""
    path_str = (request.path or "").strip("/")
    base = "/us/en/workspace/" if ("us/" in path_str or path_str.startswith("us")) else "/cl/es/workspace/"
    return render(
        request,
        "taller/desarme/unavailable.html",
        {"workspace_url": base},
    )


try:
    from taller.desarme import views
    from taller.desarme.views_inventario import (
        confirmar_venta_desde_inventario,
        crear_venta_desde_inventario,
        finalizar_venta_desde_inventario,
        inventario_inteligente,
    )

    app_name = "desarme"
    urlpatterns = [
        path("", views.index, name="index"),
        path("api/vendedores/", views.api_vendedores_buscar, name="api_vendedores_buscar"),
        path("api/vendedores/crear/", views.api_vendedor_crear, name="api_vendedor_crear"),
        path("vehiculos/", views.lista_vehiculos, name="lista_vehiculos"),
        path("vehiculos/crear/", views.crear_vehiculo, name="crear_vehiculo"),
        path("vehiculos/<int:pk>/", views.ver_vehiculo, name="ver_vehiculo"),
        path("vehiculos/<int:pk>/scanner/", views.scanner_vehiculo, name="scanner_vehiculo"),
        path("vehiculos/<int:pk>/generar-inventario/", views.generar_inventario_view, name="generar_inventario"),
        path("vehiculos/<int:pk>/editar/", views.editar_vehiculo, name="editar_vehiculo"),
        path("vehiculos/<int:pk>/inventario/", views.inventario_vehiculo, name="inventario_vehiculo"),
        path("vehiculos/<int:pk>/inventario-inteligente/", inventario_inteligente, name="inventario_inteligente"),
        path("vehiculos/<int:pk>/vender/", views.iniciar_venta_desde_inventario, name="iniciar_venta_desde_inventario"),
        path("vehiculos/<int:pk>/crear-venta-desde-inventario/", crear_venta_desde_inventario, name="crear_venta_desde_inventario"),
        path("vehiculos/<int:pk>/confirmar-venta-desde-inventario/", confirmar_venta_desde_inventario, name="confirmar_venta_desde_inventario"),
        path("vehiculos/<int:pk>/finalizar-venta-desde-inventario/", finalizar_venta_desde_inventario, name="finalizar_venta_desde_inventario"),
        path("api/piezas/<int:pk>/estado/", views.api_pieza_actualizar_estado, name="api_pieza_estado"),
        path("api/piezas/<int:pk>/precio/", views.api_pieza_actualizar_precio, name="api_pieza_precio"),
        path("api/piezas/<int:pk>/label-empresa/", views.api_pieza_label_empresa_guardar, name="api_pieza_label_empresa_guardar"),
        path("api/piezas/bulk-estado/", views.api_piezas_bulk_estado, name="api_piezas_bulk_estado"),
        path("api/piezas/bulk-precio/", views.api_piezas_bulk_precio, name="api_piezas_bulk_precio"),
        path("piezas/", views.lista_piezas, name="lista_piezas"),
        path("piezas/crear/", views.crear_pieza, name="crear_pieza"),
        path("piezas/<int:pk>/editar/", views.editar_pieza, name="editar_pieza"),
    ]
except ImportError:
    app_name = "desarme"
    urlpatterns = [
        path("", _desarme_fallback_index, name="index"),
        path("vehiculos/", _desarme_fallback_unavailable, name="lista_vehiculos"),
        path("<path:subpath>", _desarme_fallback_index, name="fallback"),
    ]
