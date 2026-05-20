from taller.views_extra.views_subscription import cancelar_suscripcion_view
from django.urls import include, path
from django.views.generic import RedirectView

from taller.views_ingreso import (
    ingreso_buscar,
    ingreso_centro,
    panel_ingreso_vehiculo,
)

centro_trabajo = ingreso_centro
centro_trabajo_buscar = ingreso_buscar
from taller.views_extra.company_settings_views import company_settings_view
from taller.views_extra.dashboard_empresa import (
    dashboard_centro_operaciones,
    dashboard_centro_operaciones_espacial,
)
from taller.views_extra.views_suscripciones import precios
from taller.views_extra.views import dashboard
from taller.views.dashboard_bi import DashboardHomeView

app_name = "taller"

urlpatterns = [
    # ✅ Gestión de Equipo (Team Management)
    path("equipo/", include(("taller.team.urls", "team"), namespace="team")),
    path("clientes/", include(("taller.clientes.urls", "clientes"), namespace="clientes")),
    # CORREGIDO: Usar vista unificada country-aware en lugar de urls_chile
    # panel-ingreso debe ir ANTES del include vehiculos para que coincida
    path(
        "vehiculos/<int:pk>/panel-ingreso/",
        panel_ingreso_vehiculo,
        name="panel_ingreso",
    ),
    path(
        "vehiculos/",
        include(("taller.vehiculos.urls", "vehiculos"), namespace="vehiculos"),
    ),
    # Namespace unificado para tests y vistas combinadas (REDUNDANTE - eliminado)
    # path('vehiculos-core/', include(('taller.vehiculos.urls', 'vehiculos'), namespace='vehiculos')),
    path(
        "repuestos/",
        include(("taller.repuestos.urls", "repuestos"), namespace="repuestos"),
    ),
    path(
        "documentos/",
        include(("taller.documentos.urls", "documentos"), namespace="documentos"),
    ),
    path("api/", include(("taller.api.urls", "api"), namespace="api")),
    path(
        "admin-monitoring/",
        include(
            ("taller.urls_extra.admin_monitoring", "admin_monitoring"),
            namespace="admin_monitoring",
        ),
    ),
    path("emails/", include(("taller.emails.urls", "emails"), namespace="emails")),
    path(
        "business-intelligence/",
        include(
            ("taller.business_intelligence_urls", "business_intelligence"),
            namespace="business_intelligence",
        ),
    ),
    path(
        "servicios/",
        include(("taller.servicios.urls", "servicios"), namespace="servicios"),
    ),
    # Agregar el namespace de reportes para que funcione 'taller:reportes:reportes_dashboard'
    path("reportes/", include(("taller.reportes.urls", "reportes"), namespace="reportes")),
    # === RUTAS PRINCIPALES PARA COMPATIBILIDAD ===
    path("dashboard/", dashboard, name="dashboard"),  # Dashboard principal
    path("dashboard/bi/", DashboardHomeView.as_view(), name="dashboard_bi"),  # Dashboard de BI
    path("pricing/", precios, name="pricing"),
    path("precios/", precios, name="precios"),
    path("centro-operaciones/", dashboard_centro_operaciones, name="centro_operaciones"),
    path(
        "centro-operaciones-espacial/",
        dashboard_centro_operaciones_espacial,
        name="centro_operaciones_espacial",
    ),
    # Centro de Trabajo / Workspace (canonical /us/en/workspace/ y /us/es/workspace/)
    path("workspace/", centro_trabajo, name="centro_trabajo"),
    path("workspace/buscar/", centro_trabajo_buscar, name="centro_trabajo_buscar"),
    # Desarmaduría: mapa interactivo, plantillas, piezas
    path("desarme/", include(("taller.urls_desarme", "desarme"), namespace="desarme")),
    # Centro de Ingreso Vehicular
    path("ingreso/", ingreso_centro, name="ingreso_centro"),
    path("ingreso/buscar/", ingreso_buscar, name="ingreso_buscar"),
    # Alias público: redirige al Settings Center
    path(
        "configuracion/",
        RedirectView.as_view(pattern_name="taller:company_settings", permanent=False),
        name="configuracion",
    ),
    # Configuración real (dueño)
    path(
        "configuracion/empresa/",
        RedirectView.as_view(pattern_name="taller:company_settings", permanent=False),
        name="configuracion_empresa",
    ),
    # Rutas principales de taller (dashboard, settings, etc.)
    # path('', include('taller.taller_main_urls')),  # Eliminado para evitar conflicto de namespace
    # Puedes agregar aquí otras rutas globales si es necesario
    path("ajax/", include(("taller.ajax.urls", "ajax"), namespace="ajax")),
    # Company settings
    path("settings/", company_settings_view, name="company_settings"),
    # Centro de Ayuda
    path("help/", include(("taller.help.urls", "help"), namespace="help")),
    # URLs de autocomplete para los formularios (movidas a URLs específicas de país)
    # path(
    #     "autocomplete/",
    #     include(("taller.autocomplete.urls", "autocomplete"), namespace="autocomplete"),
    # ),
    # Cancelación de cuenta y portabilidad SaaS
    path("suscripcion/cancelar/", cancelar_suscripcion_view, name="cancelar_suscripcion"),
]
