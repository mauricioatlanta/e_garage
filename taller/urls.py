from django.urls import include, path

from taller import views as taller_views
from taller.views_extra import tecnicos_views as tv
from taller.views_extra.company_settings_views import company_settings_view
from taller.views_extra.views import dashboard
from taller.views_extra.views_configuracion import configuracion_empresa

app_name = "taller"

urlpatterns = [
    path(
        "clientes/", include(("taller.clientes.urls", "clientes"), namespace="clientes")
    ),
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
    path(
        "reportes/", include(("taller.reportes.urls", "reportes"), namespace="reportes")
    ),
    # === RUTAS PRINCIPALES PARA COMPATIBILIDAD ===
    path("dashboard/", dashboard, name="dashboard"),  # Dashboard principal
    path(
        "configuracion/", configuracion_empresa, name="configuracion"
    ),  # Configuración empresa
    # Rutas principales de taller (dashboard, settings, etc.)
    # path('', include('taller.taller_main_urls')),  # Eliminado para evitar conflicto de namespace
    # Puedes agregar aquí otras rutas globales si es necesario
    path("vehiculos/ajax/", include("taller.ajax_urls")),
    # Company settings y técnicos
    path("settings/", company_settings_view, name="company_settings"),
    path("tecnicos/", tv.tecnicos_lista, name="tecnicos_lista"),
    path("tecnicos/nuevo/", tv.tecnicos_crear, name="tecnicos_nuevo"),
    path(
        "tecnicos/<int:tecnico_id>/editar/", tv.tecnicos_editar, name="tecnicos_editar"
    ),
    path(
        "tecnicos/<int:tecnico_id>/toggle/",
        tv.tecnicos_toggle_activo,
        name="tecnicos_toggle",
    ),
    # URLs de autocomplete para los formularios
    path(
        "autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="autocomplete"),
    ),
]
