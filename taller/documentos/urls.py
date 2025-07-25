

from django.urls import path
from taller.documentos import views as documentos
from taller.documentos.views_nuevas import ver_documento_nuevo, editar_documento_nuevo, test_documento_datos
from taller.documentos.api_servicios import api_servicios_por_categoria, api_buscar_servicios, api_crear_servicio_rapido
from taller.documentos.views_export import (
    exportar_documento_pdf, exportar_rentabilidad_excel, enviar_documento_whatsapp,
    enviar_documento_email, vista_impresion_documento, exportar_dashboard_imagen
)

app_name = "documentos"

urlpatterns = [
    path("", documentos.lista_documentos, name="lista_documentos"),
    path("nuevo/", documentos.crear_documento, name="crear_documento"),
    
    # NUEVAS VIEWS MEJORADAS
    path("nuevo-ver/<int:documento_id>/", ver_documento_nuevo, name="ver_documento_nuevo"),
    path("nuevo-editar/<int:documento_id>/", editar_documento_nuevo, name="editar_documento_nuevo"),
    path("test-datos/<int:documento_id>/", test_documento_datos, name="test_documento_datos"),
    
    # 🚀 NUEVAS FUNCIONALIDADES DE EXPORTACIÓN
    path("<int:documento_id>/pdf/", exportar_documento_pdf, name="exportar_pdf"),
    path("<int:documento_id>/whatsapp/", enviar_documento_whatsapp, name="enviar_whatsapp"),
    path("<int:documento_id>/email/", enviar_documento_email, name="enviar_email"),
    path("<int:documento_id>/imprimir/", vista_impresion_documento, name="vista_impresion"),
    path("exportar-rentabilidad-excel/", exportar_rentabilidad_excel, name="exportar_rentabilidad_excel"),
    path("exportar-dashboard-imagen/", exportar_dashboard_imagen, name="exportar_dashboard_imagen"),
    
    # Views originales (mantener para compatibilidad)
    path("<int:documento_id>/", documentos.ver_documento, name="ver_documento"),
    path('editar/<int:documento_id>/', documentos.editar_documento, name='editar_documento'),
    
    # Resto de URLs
    path("vehiculos/", documentos.obtener_vehiculos_por_cliente, name="vehiculos_por_cliente"),
    path("numero/", documentos.numero_documento_auto, name="numero_documento_auto"),
    path('documentos/obtener-numero/', documentos.numero_documento_auto, name='numero_documento_auto'),
    path('documentos/obtener-vehiculos/', documentos.obtener_vehiculos_por_cliente, name='obtener_vehiculos_por_cliente'),
    path('editar/<int:documento_id>/', documentos.editar_documento, name='editar_documento'),
    path('eliminar/<int:documento_id>/', documentos.eliminar_documento, name='eliminar_documento'),
    path('autocomplete/cliente/', documentos.autocomplete_cliente, name='autocomplete_cliente'),
    path('autocomplete/vehiculo/', documentos.obtener_vehiculos_por_cliente, name='autocomplete_vehiculo'),
    path('autocomplete/servicio/', documentos.autocomplete_servicio, name='autocomplete_servicio'),
    path('autocomplete_repuesto/', documentos.autocomplete_repuesto, name='autocomplete_repuesto'),
    
    # APIs para servicios organizados por categorías
    path('api/servicios-categorias/', api_servicios_por_categoria, name='api_servicios_categorias'),
    path('api/buscar-servicios/', api_buscar_servicios, name='api_buscar_servicios'),
    path('api/crear-servicio/', api_crear_servicio_rapido, name='api_crear_servicio'),
    path('autocomplete_servicio_nombre/', documentos.autocomplete_servicio_nombre, name='autocomplete_servicio_nombre'),
    path('exportar_pdf/<int:documento_id>/', documentos.exportar_documento_pdf, name='exportar_documento_pdf'),

    # API AJAX para crear mecánico
    path('api/crear_mecanico/', documentos.api_crear_mecanico, name='api_crear_mecanico'),
]
