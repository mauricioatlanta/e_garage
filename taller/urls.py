from django.urls import include, path

from taller.views_extra.company_settings_views import company_settings_view
from taller.views_extra.dashboard_empresa import (
    dashboard_centro_operaciones,
    dashboard_centro_operaciones_espacial,
)
from taller.views_extra.views import dashboard
from taller.views_extra.views_configuracion import configuracion_empresa

app_name = "taller"

urlpatterns = [
    path("clientes/", include(("taller.clientes.urls", "clientes"), namespace="clientes")),
    # CORREGIDO: Usar vista unificada country-aware en lugar de urls_chile
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
            ("taller.urls_modules.admin_monitoring", "admin_monitoring"),
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
    path("centro-operaciones/", dashboard_centro_operaciones, name="centro_operaciones"),
    path(
        "centro-operaciones-espacial/",
        dashboard_centro_operaciones_espacial,
        name="centro_operaciones_espacial",
    ),
    path("configuracion/", configuracion_empresa, name="configuracion"),  # Configuración empresa
    # Rutas principales de taller (dashboard, settings, etc.)
    # path('', include('taller.taller_main_urls')),  # Eliminado para evitar conflicto de namespace
    # Puedes agregar aquí otras rutas globales si es necesario
    path("ajax/", include("taller.ajax_urls")),
    # Company settings
    path("settings/", company_settings_view, name="company_settings"),
    # URLs de autocomplete para los formularios (movidas a URLs específicas de país)
    # path(
    #     "autocomplete/",
    #     include(("taller.autocomplete.urls", "autocomplete"), namespace="autocomplete"),
    # ),
]
