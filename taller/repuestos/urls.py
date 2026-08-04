from django.urls import path

from taller.views.reabastecimiento import ReabastecimientoPanelView
from taller.repuestos.views import (
    buscar_repuestos_ajax,
    buscar_repuestos_workspace,
    crear_repuesto,
    editar_repuesto,
    eliminar_repuesto,
    lista_repuestos,
    ver_repuesto,
)

from .api import api_repuesto_por_codigo

app_name = "repuestos"

urlpatterns = [
    path("", lista_repuestos, name="lista_repuestos"),
    path(
        "reabastecimiento/",
        ReabastecimientoPanelView.as_view(),
        name="reabastecimiento",
    ),
    path("crear/", crear_repuesto, name="crear_repuesto"),
    path("<int:pk>/", ver_repuesto, name="ver_repuesto"),
    path("editar/<int:pk>/", editar_repuesto, name="editar_repuesto"),
    path("<int:pk>/eliminar/", eliminar_repuesto, name="eliminar_repuesto"),
    path("buscar/", buscar_repuestos_workspace, name="buscar_repuestos_workspace"),
    path("ajax/buscar/", buscar_repuestos_ajax, name="buscar_repuestos_ajax"),
    path(
        "api/repuesto-por-codigo/",
        api_repuesto_por_codigo,
        name="api_repuesto_por_codigo",
    ),
]
