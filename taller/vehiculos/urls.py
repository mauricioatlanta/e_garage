# taller/vehiculos/urls.py
"""
URLs para el módulo de vehículos - Configuración Multi-Tenant

Seguridad aplicada:
  ✅ CRUD: @login_required en todas las vistas principales
  ✅ AJAX GET: @login_required + @require_http_methods(["GET"])
  ✅ AJAX POST: @login_required + @require_http_methods(["POST"]) + CSRF (vía SessionAuth)
  ✅ Filtros: Todas las queries filtran por empresa y país del usuario

Formato de respuesta estandarizado:
  - Éxito: {"success": true, "marcas": [...], "modelos": [...], etc.}
  - Error:  {"success": false, "error": "mensaje"}

Multi-tenant:
  - Clientes: filtrados por empresa del usuario
  - Catálogos (marca/modelo/motor/caja): filtrados por country + empresa (opcional)
  - get_or_create() de nuevos ítems siempre con country/empresa

Notas:
  - api_modelos_usa: Mantener solo si DAL/autocomplete lo requiere
  - ajax_modelos_por_marca_anio: Preferido para el frontend JS
  - Trailing slash en todas las rutas ✅
"""

from django.urls import path

from taller.vehiculos import views_fbv as views
from taller.vehiculos.autocomplete_views import (
    CajaAutocomplete,
    ClienteAutocomplete,
    MotorAutocomplete,
)

app_name = "vehiculos"


def ingreso_vehiculo_foto_lazy(request, *args, **kwargs):
    """Wrapper: import diferido para no cargar views_ingreso/WhatsApp/OCR al importar URLs."""
    from taller.vehiculos.views_ingreso import ingreso_vehiculo_foto

    return ingreso_vehiculo_foto(request, *args, **kwargs)


def procesar_patente_identificada_lazy(request, *args, **kwargs):
    """Wrapper: import diferido para no cargar views_ingreso/WhatsApp/OCR al importar URLs."""
    from taller.vehiculos.views_ingreso import procesar_patente_identificada

    return procesar_patente_identificada(request, *args, **kwargs)


urlpatterns = [
    # =========================
    # CRUD Principales
    # =========================
    # Todas requieren @login_required y filtran por empresa
    path("", views.lista_vehiculos, name="lista_vehiculos"),
    path("crear/", views.crear_vehiculo, name="crear_vehiculo"),
    # Ingreso de vehículo por foto de patente (lazy: no carga WhatsApp/OCR al importar URLs)
    path("ingreso-foto/", ingreso_vehiculo_foto_lazy, name="ingreso_foto"),
    path(
        "patente-identificada/",
        procesar_patente_identificada_lazy,
        name="patente_identificada",
    ),
    path("<int:vehiculo_id>/", views.ver_vehiculo, name="ver_vehiculo"),
    path("<int:vehiculo_id>/editar/", views.editar_vehiculo, name="editar_vehiculo"),
    path(
        "<int:vehiculo_id>/eliminar/",
        views.eliminar_vehiculo,
        name="eliminar_vehiculo",
    ),
    # =========================
    # APIs de Lectura (GET)
    # =========================
    # Seguridad: @login_required + @require_GET
    # Multi-tenant: Filtran por país y empresa del usuario
    # Marcas disponibles para el país del usuario
    path("api/marcas/", views.api_marcas, name="api_marcas"),
    # Búsqueda de clientes (solo de la empresa del usuario)
    path(
        "api/clientes/",
        views.api_busqueda_clientes,
        name="api_busqueda_clientes",
    ),
    # Autocompletado de clientes (DAL Select2)
    path(
        "autocomplete/cliente/",
        ClienteAutocomplete.as_view(),
        name="cliente_autocomplete",
    ),
    # Autocompletado de motores (DAL Select2Tag - permite crear nuevos)
    path(
        "autocomplete/motor/",
        MotorAutocomplete.as_view(),
        name="motor-autocomplete",
    ),
    # Autocompletado de cajas (DAL Select2Tag - permite crear nuevas)
    path(
        "autocomplete/caja/",
        CajaAutocomplete.as_view(),
        name="caja-autocomplete",
    ),
    # Colores disponibles para el país del usuario
    path("api/colores/", views.api_colores, name="api_colores"),
    # Modelos USA desde catálogo (legacy - mantener solo si DAL lo usa)
    # Considera deprecar si ajax_modelos_por_marca_anio cubre el caso
    path("api/modelos-usa/", views.api_modelos_usa, name="api_modelos_usa"),
    # Marcas por año (USA, catálogo con anio_desde/anio_hasta)
    path(
        "api/marcas-por-anio/",
        views.api_marcas_por_anio,
        name="api_marcas_por_anio",
    ),
    # Modelos por marca y año (USA)
    path(
        "api/modelos-por-marca-anio-usa/",
        views.api_modelos_por_marca_anio_usa,
        name="api_modelos_por_marca_anio_usa",
    ),
    # =========================
    # AJAX Dinámico (GET)
    # =========================
    # Usado por formulario_jerarquico.js
    # Formato: {success: true, modelos: [{id, nombre}]}
    # Modelos por marca (sin año)
    path(
        "ajax/modelos-por-marca/",
        views.ajax_modelos_por_marca,
        name="ajax_modelos_por_marca",
    ),
    # Modelos por marca + año (★ PREFERIDO por el frontend)
    path(
        "ajax/modelos-por-marca-anio/",
        views.ajax_modelos_por_marca_anio,
        name="ajax_modelos_por_marca_anio",
    ),
    # API para modelos por marca y año (formato JSON simple)
    path(
        "api/modelos-por-marca/",
        views.modelos_por_marca_api,
        name="modelos_por_marca_api",
    ),
    # Motores filtrados por modelo
    path(
        "ajax/motores-por-modelo/",
        views.ajax_motores_por_modelo,
        name="ajax_motores_por_modelo",
    ),
    # Cajas filtradas por modelo
    path(
        "ajax/cajas-por-modelo/",
        views.ajax_cajas_por_modelo,
        name="ajax_cajas_por_modelo",
    ),
    # =========================
    # AJAX Escritura (POST)
    # =========================
    # Seguridad: @login_required + @require_POST + CSRF automático (SessionAuth)
    # Permiso: Considera agregar @user_passes_test(is_staff) para catálogo
    # Multi-tenant: Crea con country y empresa del usuario
    # Agregar nueva marca
    path(
        "ajax/agregar-marca/",
        views.ajax_agregar_marca,
        name="ajax_agregar_marca",
    ),
    # Agregar nuevo modelo
    path(
        "ajax/agregar-modelo/",
        views.ajax_agregar_modelo,
        name="ajax_agregar_modelo",
    ),
    # Agregar nuevo motor
    path(
        "ajax/agregar-motor/",
        views.ajax_agregar_motor,
        name="ajax_agregar_motor",
    ),
    # Agregar nueva caja
    path(
        "ajax/agregar-caja/",
        views.ajax_agregar_caja,
        name="ajax_agregar_caja",
    ),
    # Agregar nuevo color
    path(
        "ajax/agregar-color/",
        views.ajax_agregar_color,
        name="ajax_agregar_color",
    ),
]

# =========================
# Checklist de Seguridad
# =========================
# ✅ Todas las vistas CRUD tienen @login_required
# ✅ Todas las vistas AJAX GET tienen @require_GET + @login_required
# ✅ Todas las vistas AJAX POST tienen @require_POST + @login_required
# ⚠️  TODO: Agregar @user_passes_test(can_manage_catalog) a ajax_agregar_* si necesitas permisos
# ✅ Queries filtran por empresa.id y country
# ✅ get_or_create() incluye country (y empresa si aplica)
# ✅ Formato de respuesta estandarizado: {success, data|error}
# ✅ Trailing slash en todas las rutas

# =========================
# Testing Rápido
# =========================
# from django.urls import reverse, resolve
#
# # Verificar resolución
# assert resolve("/cl/es/vehiculos/crear/").url_name == "crear_vehiculo"
# assert reverse("vehiculos:ajax_modelos_por_marca_anio").endswith("/ajax/modelos-por-marca-anio/")
#
# # Test AJAX (con pytest-django)
# def test_ajax_modelos_requiere_login(client):
#     url = reverse("vehiculos:ajax_modelos_por_marca_anio")
#     resp = client.get(url)
#     assert resp.status_code == 302  # Redirect a login
#
# def test_ajax_modelos_retorna_json(client, user):
#     client.force_login(user)
#     url = reverse("vehiculos:ajax_modelos_por_marca_anio")
#     resp = client.get(url, {"marca_id": "1", "anio": "2020"})
#     assert resp.status_code == 200
#     data = resp.json()
#     assert "results" in data or "success" in data
