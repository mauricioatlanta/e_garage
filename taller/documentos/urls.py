from django.urls import path
from django.views.generic import RedirectView
from . import views_moderno as views_moderno
from . import views
from . import api_servicios
from .views_listado import DocumentoListViewBase
from .views_cbv import DocumentoUpdateView, DocumentoDetailView
from .api import lista_debug
from . import views_nuevas
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from test_editar import test_editar_simple, fix_documento_data


app_name = "documentos"

urlpatterns = [
    # Páginas - LISTA UNIFICADA CON SUBQUERY
    path("", DocumentoListViewBase.as_view(), name="lista_documentos"),
    
    # Pantalla unificada
    path("form/", views_moderno.documento_form, name="documento_crear"),
    path("form/<int:pk>/", views_moderno.documento_form, name="documento_editar"),
    
    # Compatibilidad con rutas antiguas
    path("nuevo/", RedirectView.as_view(pattern_name="documentos:documento_crear", permanent=False), name="crear_documento"),
    path("nuevo-editar/<int:pk>/", RedirectView.as_view(pattern_name="documentos:documento_editar", permanent=False), name="editar_documento"),
    
    path("test-editar/<int:documento_id>/", test_editar_simple, name="test_editar"),
    path("fix-data/<int:documento_id>/", fix_documento_data, name="fix_data"),
    path("procesar/", views_moderno.procesar_documento_moderno_wrapper, name="procesar_documento"),
    path("<int:pk>/", DocumentoDetailView.as_view(), name="ver_documento_cbv"),
    path("<int:documento_id>/", views.ver_documento, name="ver_documento"),

    # Exportar PDF
    path("<int:documento_id>/exportar_pdf/", views.exportar_documento_pdf, name="exportar_documento_pdf"),

    # APIs principales
    path("api/buscar-repuestos/", views_moderno.api_buscar_repuestos, name="api_buscar_repuestos"),
    path("api/buscar-servicios/", api_servicios.api_buscar_servicios, name="api_buscar_servicios"),
    path("api/vehiculos-cliente/", views_moderno.api_vehiculos_cliente, name="api_vehiculos_cliente"),
    path("api/buscar-servicios-internos/", views_moderno.api_buscar_servicios_internos, name="api_buscar_servicios_internos"),
    path("api/obtener-numero-documento/", views_moderno.api_obtener_numero_documento, name="api_obtener_numero_documento"),
    
    # APIs de autocompletado
    path("api/autocomplete-servicio/", views.autocomplete_servicio, name="autocomplete_servicio"),
    path("api/autocomplete-otro-servicio/", views.autocomplete_otro_servicio, name="autocomplete_otro_servicio"),
    path("api/autocomplete-repuesto/", views.autocomplete_repuesto, name="autocomplete_repuesto"),
    path("api/crear-servicio/", views.api_crear_servicio, name="api_crear_servicio"),
    
    # Endpoint de diagnóstico
    path("lista-debug/", lista_debug, name="lista_debug"),
]
