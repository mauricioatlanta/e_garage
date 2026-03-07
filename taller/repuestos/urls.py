from django.urls import path

from taller.repuestos.views import (
    buscar_repuestos_ajax,
    crear_repuesto,
    editar_repuesto,
    eliminar_repuesto,
    exportar_excel_repuestos,
    lista_repuestos,
    repuesto_info,
    ver_repuesto,
)

from .api import api_repuesto_por_codigo

app_name = "repuestos"

urlpatterns = [
    path("", lista_repuestos, name="lista_repuestos"),
    path("crear/", crear_repuesto, name="crear_repuesto"),
    path("<int:pk>/", ver_repuesto, name="ver_repuesto"),
    path("editar/<int:pk>/", editar_repuesto, name="editar_repuesto"),
    path("<int:pk>/eliminar/", eliminar_repuesto, name="eliminar_repuesto"),
    path("ajax/buscar/", buscar_repuestos_ajax, name="buscar_repuestos_ajax"),
    path("ajax/repuesto-info/", repuesto_info, name="repuesto_info"),
    path("exportar/excel/", exportar_excel_repuestos, name="exportar_excel_repuestos"),
    path(
        "api/repuesto-por-codigo/",
        api_repuesto_por_codigo,
        name="api_repuesto_por_codigo",
    ),
]
