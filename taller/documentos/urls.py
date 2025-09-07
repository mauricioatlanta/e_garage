import os
import sys

from django.urls import path
from django.views.generic import RedirectView

# from .api import lista_debug  # Función no existe
from . import api_servicios, views
from . import views_moderno as views_moderno
from . import views_nuevas
from .redirect_views import redirect_documento_crear, redirect_documento_editar
from .views_cbv import DocumentoDetailView, DocumentoUpdateView
from .views_class_based import DocumentoFormView
from .views_class_based import DocumentoUpdateView as NewDocumentoUpdateView
from .views_listado import DocumentoListViewBase
from .views_migrated import DocumentoCreateView, DocumentoDeleteView
from .views_migrated import DocumentoDetailView as MigratedDetailView
from .views_migrated import DocumentoListView
from .views_migrated import DocumentoUpdateView as MigratedUpdateView

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from test_editar import fix_documento_data, test_editar_simple

app_name = "documentos"

urlpatterns = [
    # Páginas - LISTA UNIFICADA CON MIXIN PAÍS/IDIOMA
    path("", DocumentoListView.as_view(), name="lista_documentos"),
    # Pantalla unificada - VISTAS MIGRADAS CON TEMPLATE RESOLUTION
    path("form/", DocumentoCreateView.as_view(), name="documento_crear"),
    path("form/<int:pk>/", MigratedUpdateView.as_view(), name="documento_editar"),
    # Alias adicional para editar (compatibilidad con URL esperada)
    path(
        "editar/<int:pk>/", MigratedUpdateView.as_view(), name="documento_editar_alias"
    ),
    # Detalle y eliminación con template resolution
    path("ver/<int:pk>/", MigratedDetailView.as_view(), name="ver_documento"),
    path(
        "eliminar/<int:pk>/", DocumentoDeleteView.as_view(), name="eliminar_documento"
    ),
    # Compatibilidad con rutas antiguas - CON PRESERVACIÓN DE PAÍS
    path("nuevo/", redirect_documento_crear, name="crear_documento"),
    path("nuevo-editar/<int:pk>/", redirect_documento_editar, name="editar_documento"),
    path("test-editar/<int:documento_id>/", test_editar_simple, name="test_editar"),
    path("fix-data/<int:documento_id>/", fix_documento_data, name="fix_data"),
    path(
        "procesar/",
        views_moderno.procesar_documento_moderno_wrapper,
        name="procesar_documento",
    ),
    path("<int:pk>/", DocumentoDetailView.as_view(), name="ver_documento_cbv"),
    path("<int:documento_id>/", views.ver_documento, name="ver_documento"),
    # Exportar PDF
    path(
        "<int:documento_id>/exportar_pdf/",
        views.exportar_documento_pdf,
        name="exportar_documento_pdf",
    ),
    # APIs principales
    path(
        "api/buscar-repuestos/",
        views_moderno.api_buscar_repuestos,
        name="api_buscar_repuestos",
    ),
    path(
        "api/buscar-servicios/",
        api_servicios.api_buscar_servicios,
        name="api_buscar_servicios",
    ),
    path(
        "api/vehiculos-cliente/",
        views_moderno.api_vehiculos_cliente,
        name="api_vehiculos_cliente",
    ),
    path(
        "api/buscar-servicios-internos/",
        views_moderno.api_buscar_servicios_internos,
        name="api_buscar_servicios_internos",
    ),
    path(
        "api/obtener-numero-documento/",
        views_moderno.api_obtener_numero_documento,
        name="api_obtener_numero_documento",
    ),
    # APIs de autocompletado
    path(
        "api/autocomplete-servicio/",
        views.autocomplete_servicio,
        name="autocomplete_servicio",
    ),
    path(
        "api/autocomplete-otro-servicio/",
        views.autocomplete_otro_servicio,
        name="autocomplete_otro_servicio",
    ),
    path(
        "api/autocomplete-repuesto/",
        views.autocomplete_repuesto,
        name="autocomplete_repuesto",
    ),
    path("api/crear-servicio/", views.api_crear_servicio, name="api_crear_servicio"),
    # Endpoint de diagnóstico
    # path("lista-debug/", lista_debug, name="lista_debug"),  # Función no existe
]
