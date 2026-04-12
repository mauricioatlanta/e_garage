from django.urls import path

# from .api import lista_debug  # Función no existe
from . import api, api_servicios, views
from . import views_moderno as views_moderno
from . import views_inventory  # ✅ Vistas de inventario (emitir, anular)
from . import views_pdf  # ✅ Vistas de PDF y WhatsApp
from . import views_export_sii  # ✅ Vistas de exportación SII
from .redirect_views import redirect_documento_crear, redirect_documento_editar
from .views_cbv import DocumentoDetailView
from .views_migrated import DocumentoCreateView, DocumentoDeleteView, DocumentoDuplicateView
from .views_migrated import DocumentoDetailView as MigratedDetailView
from .views_migrated import DocumentoListView
from .views_migrated import DocumentoUpdateView as MigratedUpdateView
from .api_repuestos import buscar_repuestos_api  # ✅ API de autocomplete para Alpine.js
from . import views_seguimiento  # ✅ Vistas de seguimiento y memoria

try:
    from taller.desarme.views_pdf import (
        compartir_documento_whatsapp,
        descargar_documento_pdf,
        enviar_documento_email,
        imprimir_documento,
        ver_documento_publico,
    )
except ImportError:
    descargar_documento_pdf = None
    imprimir_documento = None
    ver_documento_publico = None
    compartir_documento_whatsapp = None
    enviar_documento_email = None

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
    path("duplicar/<int:pk>/", DocumentoDuplicateView.as_view(), name="documento_duplicar"),
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
    # Panel documento (imprimir, PDF, WhatsApp, email, público) — rutas antes de pk/pdf para prioridad
]
if descargar_documento_pdf is not None:
    urlpatterns.extend(
        [
            path(
                "<int:documento_id>/pdf/", descargar_documento_pdf, name="descargar_documento_pdf"
            ),
            path("<int:documento_id>/imprimir/", imprimir_documento, name="imprimir_documento"),
            path(
                "<int:documento_id>/whatsapp/",
                compartir_documento_whatsapp,
                name="compartir_documento_whatsapp",
            ),
            path(
                "<int:documento_id>/email/", enviar_documento_email, name="enviar_documento_email"
            ),
            path("p/<str:token>/", ver_documento_publico, name="ver_documento_publico"),
        ]
    )
urlpatterns += [
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
    # Exportación CSV SII
    path(
        "<int:documento_id>/exportar-sii/",
        views_export_sii.exportar_csv_sii,
        name="exportar_csv_sii",
    ),
    path(
        "<int:documento_id>/verificar-facturacion/",
        views_export_sii.verificar_facturacion_documento,
        name="verificar_facturacion_documento",
    ),
    # Seguimiento público y memoria
    path(
        "seguimiento/<str:token>/",
        views_seguimiento.seguimiento_publico,
        name="seguimiento_publico",
    ),
    path(
        "<int:documento_id>/memoria/",
        views_seguimiento.gestionar_memoria_documento,
        name="gestionar_memoria",
    ),
    path(
        "<int:documento_id>/crear-seguimiento/",
        views_seguimiento.crear_seguimiento_publico,
        name="crear_seguimiento_publico",
    ),
]
