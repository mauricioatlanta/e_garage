"""
URLs específicas para Chile (español)
    path('taller/servicios/', include(('taller.servicios.urls', 'servicios'), namespace='servicios_admin')),
    path('taller/documentos/', include(('taller.documentos.urls', 'documentos'), namespace='documentos')),
    path('taller/reportes/', include('taller.reportes.urls')),

    # Servicios también bajo /cl/servicios/ para disponibilidad global del namespace
    path('servicios/', include(('taller.servicios.urls', 'servicios'), namespace='servicios')),

    # Documentos también bajo /cl/documentos/ para disponibilidad global del namespace
    path('documentos/', include(('taller.documentos.urls', 'documentos'), namespace='documentos_global')),o: /cl/
"""

import logging

from django.urls import include, path
from django.views.generic import TemplateView

# Configuración de logging para este módulo
logger = logging.getLogger(__name__)
logger.debug("CARGANDO taller/urls_extra/chile.py")
from django.http import HttpResponseRedirect

from taller import ajax_views
from taller.taller_views import dashboard_suscripciones
from taller.views_extra.ajax import buscar_clientes, vehiculos_por_cliente
from taller.views_extra.company_settings_views import company_settings_view
from taller.views_extra.country_views import test_chile_view
from taller.views_extra.dashboard_empresa import (
    dashboard_centro_operaciones,
    dashboard_centro_operaciones_espacial,
)
from taller.views_extra.views import dashboard
from taller.views_extra.views_configuracion import (
    configuracion_empresa,
    configuracion_tecnicos,
)

app_name = "chile"

urlpatterns = [
    # Vista de inicio para /cl/es/ - redirige a la página de bienvenida
    path("", lambda request: HttpResponseRedirect("/cl/egarage/"), name="chile_home"),
    # URLs principales de taller (configuración, settings, etc.)
    # Incluir las rutas específicas que necesitamos
    path("dashboard/", dashboard, name="dashboard"),
    path(
        "centro-operaciones/", dashboard_centro_operaciones, name="centro_operaciones"
    ),
    path(
        "centro-operaciones-espacial/",
        dashboard_centro_operaciones_espacial,
        name="centro_operaciones_espacial",
    ),
    path("admin/dashboard/", dashboard_suscripciones, name="dashboard_suscripciones"),
    path("configuracion/", configuracion_empresa, name="configuracion"),
    path(
        "configuracion/tecnicos/", configuracion_tecnicos, name="configuracion_tecnicos"
    ),
    path("settings/", company_settings_view, name="company_settings"),
    # Dashboard principal Chile (requiere autenticación) - Usar el de taller_main_urls
    # path("dashboard/", dashboard_cl_view, name="dashboard"),
    # Test endpoint Chile
    path("test/", test_chile_view, name="test"),
    # Página de bienvenida para Chile
    path(
        "egarage/",
        TemplateView.as_view(template_name="onboarding/bienvenida_chile.html"),
        name="bienvenida_chile",
    ),
    # Login para suscriptores de Chile (redirige al login global, pero aquí puedes poner una vista personalizada si lo deseas)
    path(
        "login/",
        TemplateView.as_view(template_name="registration/login.html"),
        name="account_login",
    ),
    # Registro para Chile (español por defecto)
    path("registro/", include("scripts.onboarding_urls")),
    # === AJAX JERÁRQUICO - VEHÍCULOS ===
    path(
        "taller/ajax/load-modelos/", ajax_views.load_modelos, name="ajax_load_modelos"
    ),
    path(
        "taller/ajax/load-motores/", ajax_views.load_motores, name="ajax_load_motores"
    ),
    path("taller/ajax/load-cajas/", ajax_views.load_cajas, name="ajax_load_cajas"),
    path(
        "taller/ajax/load-motores-cajas/",
        ajax_views.load_motores_cajas,
        name="ajax_load_motores_cajas",
    ),
    # Módulos principales (incluir cuando estén funcionando)
    # === MÓDULOS PRINCIPALES ===
    # NOTA: Los submódulos principales (clientes, vehiculos, repuestos, servicios,
    # documentos, reportes) están incluidos en taller_main_urls.py para evitar duplicación
    # Solo incluimos aquí rutas específicas de Chile que no están en el core
    # Dashboard de suscriptor
    path("", include("taller.analytics.urls_suscriptor")),
    # Servicios y documentos con namespace bajo /cl/taller/
    path(
        "taller/servicios/",
        include(("taller.servicios.urls", "servicios"), namespace="servicios_admin"),
    ),
    # DOCUMENTOS MOVIDO A gestion_taller/urls.py para evitar duplicación
    # path('taller/documentos/', include(('taller.documentos.urls', 'documentos'), namespace='documentos')),
    path(
        "taller/reportes/",
        include(("taller.reportes.urls", "reportes"), namespace="reportes_cl"),
    ),
    # Servicios también bajo /cl/servicios/ para disponibilidad global del namespace
    path(
        "servicios/",
        include(("taller.servicios.urls", "servicios"), namespace="servicios"),
    ),
    # DOCUMENTOS MOVIDO A gestion_taller/urls.py para evitar duplicación
    # path('documentos/', include(('taller.documentos.urls', 'documentos'), namespace='documentos_global')),
    # Business Intelligence bajo /cl/business-intelligence/
    path(
        "business-intelligence/",
        include(
            ("taller.business_intelligence_urls", "business_intelligence"),
            namespace="business_intelligence",
        ),
    ),
    # === AJAX ENDPOINTS ESPECÍFICOS PARA CHILE ===
    path("ajax/clientes/buscar/", buscar_clientes, name="cl_ajax_buscar_clientes"),
    path(
        "ajax/vehiculos-por-cliente/",
        vehiculos_por_cliente,
        name="cl_ajax_vehiculos_por_cliente",
    ),
    # path('api/', include('taller.api.urls')),
    # path('autocomplete/', include('taller.autocomplete.urls')),
    # path('analytics/', include('taller.analytics.urls')),
    # path('gestion/', include('gestion_taller.urls')),
]
