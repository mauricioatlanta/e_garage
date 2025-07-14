

from django.urls import path
from taller.documentos import views as documentos

app_name = "documentos"

urlpatterns = [
    path("", documentos.lista_documentos, name="lista_documentos"),
    path("nuevo/", documentos.crear_documento, name="crear_documento"),
    path("<int:documento_id>/", documentos.ver_documento, name="ver_documento"),
    path("vehiculos/", documentos.obtener_vehiculos_por_cliente, name="vehiculos_por_cliente"),
    path("numero/", documentos.numero_documento_auto, name="numero_documento_auto"),
    path('documentos/obtener-numero/', documentos.numero_documento_auto, name='numero_documento_auto'),
    path('documentos/obtener-vehiculos/', documentos.obtener_vehiculos_por_cliente, name='obtener_vehiculos_por_cliente'),
    path('editar/<int:documento_id>/', documentos.editar_documento, name='editar_documento'),
    path('eliminar/<int:documento_id>/', documentos.eliminar_documento, name='eliminar_documento'),
    path('autocomplete/servicio/', documentos.autocomplete_servicio, name='autocomplete_servicio'),
    path('autocomplete_repuesto/', documentos.autocomplete_repuesto, name='autocomplete_repuesto'),
    path('autocomplete_servicio_nombre/', documentos.autocomplete_servicio_nombre, name='autocomplete_servicio_nombre'),
    path('exportar_pdf/<int:documento_id>/', documentos.exportar_documento_pdf, name='exportar_documento_pdf'),

    # API AJAX para crear mecánico
    path('api/crear_mecanico/', documentos.api_crear_mecanico, name='api_crear_mecanico'),
]
