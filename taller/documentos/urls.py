from django.urls import path

# from .api import lista_debug  # Función no existe
from . import api, api_servicios, views
from . import views_moderno as views_moderno
from . import views_inventory  # ✅ Vistas de inventario (emitir, anular)
from . import views_pdf  # ✅ Vistas de PDF y WhatsApp
from .redirect_views import redirect_documento_crear, redirect_documento_editar
from .views_cbv import DocumentoDetailView
from .views_migrated import DocumentoCreateView, DocumentoDeleteView
from .views_migrated import DocumentoDetailView as MigratedDetailView
from .views_migrated import DocumentoListView
from .views_migrated import DocumentoUpdateView as MigratedUpdateView
from .api_repuestos import buscar_repuestos_api  # ✅ API de autocomplete para Alpine.js

# Comentado temporalmente - módulo no existe
# sys.path.append(
#     os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# )
# from test_editar import fix_documento_data, test_editar_simple

app_name = "documentos"

urlpatterns = [
    # Páginas - LISTA UNIFICADA CON MIXIN PAÍS/IDIOMA
    path("", DocumentoListView.as_view(), name="lista_documentos"),
    # Pantalla unificada - VISTAS MIGRADAS CON TEMPLATE RESOLUTION
    path("form/", DocumentoCreateView.as_view(), name="documento_crear"),
    path("form/<int:pk>/", MigratedUpdateView.as_view(), name="documento_editar"),
    # Alias adicional para editar (compatibilidad con URL esperada)
    path("editar/<int:pk>/", MigratedUpdateView.as_view(), name="documento_editar_alias"),
    # Detalle y eliminación con template resolution
    path("ver/<int:pk>/", MigratedDetailView.as_view(), name="ver_documento"),
    path("eliminar/<int:pk>/", DocumentoDeleteView.as_view(), name="eliminar_documento"),
    # Compatibilidad con rutas antiguas - CON PRESERVACIÓN DE PAÍS
    path("nuevo/", redirect_documento_crear, name="crear_documento"),
    path("nuevo-editar/<int:pk>/", redirect_documento_editar, name="editar_documento"),
    # Comentado temporalmente - funciones no existen
    # path("test-editar/<int:documento_id>/", test_editar_simple, name="test_editar"),
    # path("fix-data/<int:documento_id>/", fix_documento_data, name="fix_data"),
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
    # Enviar por WhatsApp
    path(
        "<int:documento_id>/enviar_whatsapp/",
        views.enviar_documento_whatsapp,
        name="enviar_documento_whatsapp",
    ),
    # APIs principales
    path(
        "api/buscar-repuestos/",
        views_moderno.api_buscar_repuestos,
        name="api_buscar_repuestos",
    ),
    # ✅ API de autocomplete para Alpine.js (devuelve array simple)
    path(
        "api/repuestos/buscar/",
        buscar_repuestos_api,
        name="api_repuestos_buscar",
    ),
    path(
        "api/buscar-servicios/",
        api_servicios.api_buscar_servicios,
        name="api_buscar_servicios",
    ),
    path(
        "ajax/servicios/buscar/",
        views_moderno.api_buscar_servicios_inteligente,
        name="ajax_buscar_servicios",
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
    # Alias para compatibilidad con templates
    path(
        "api/next-number/",
        views_moderno.api_obtener_numero_documento,
        name="api_next_number",
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
    path("api/create/", api.api_create, name="api_create"),
    # Autocompletado de clientes
    path("autocomplete/cliente/", views.autocomplete_cliente, name="autocomplete_cliente"),
    # Gestión de inventario (emitir, anular, validar stock)
    path("emitir/<int:documento_id>/", views_inventory.emitir_documento, name="emitir_documento"),
    path("anular/<int:documento_id>/", views_inventory.anular_documento, name="anular_documento"),
    path(
        "validar-stock/<int:documento_id>/",
        views_inventory.validar_stock_documento,
        name="validar_stock_documento",
    ),
    # Generación y descarga de PDFs
    path("<int:pk>/pdf/", views_pdf.descargar_pdf_documento, name="descargar_pdf"),
    path(
        "<int:pk>/pdf/descargar/",
        views_pdf.descargar_pdf_documento,
        name="descargar_pdf_attachment",
    ),
    # Envío por WhatsApp
    path("<int:pk>/whatsapp/", views_pdf.enviar_por_whatsapp, name="enviar_whatsapp"),
    path(
        "<int:pk>/whatsapp/enlace/",
        views_pdf.generar_enlace_whatsapp,
        name="generar_enlace_whatsapp",
    ),
    # Endpoint de diagnóstico
    # path("lista-debug/", lista_debug, name="lista_debug"),  # Función no existe
]
