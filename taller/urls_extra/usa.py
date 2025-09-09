"""
URLs específicas para USA (inglés)
Prefijo: /us/
"""

from django.urls import include, path

from taller import ajax_views
from taller.views_extra.ajax import buscar_clientes, vehiculos_por_cliente
from taller.views_extra.country_views import dashboard_usa_view, test_usa_view
from taller.views_extra.views import dashboard
from taller.views_extra.dashboard_empresa import dashboard_centro_operaciones, dashboard_centro_operaciones_espacial
from taller.taller_views import dashboard_suscripciones
from taller.views_extra.views_configuracion import configuracion_empresa, configuracion_tecnicos
from taller.views_extra.company_settings_views import company_settings_view
from taller.views_extra.futuristic_company_settings_views import (
    futuristic_company_settings_view,
    api_technician_toggle,
    api_technician_delete
)


def usa_login_view(request):
    """Vista personalizada de login para USA que no redirige automáticamente"""
    from allauth.account.views import LoginView

    # Configurar el contexto de país para USA
    request.country = "US"
    request.country_code = "US"

    # Usar la vista de allauth pero con template específico para USA
    view = LoginView.as_view(template_name="taller/us/en/auth/login.html")
    return view(request)


def usa_signup_view(request):
    """Vista personalizada de signup para USA"""
    from allauth.account.views import SignupView

    # Configurar el contexto de país para USA
    request.country = "US"
    request.country_code = "US"

    # Usar la vista de allauth pero con template específico para USA
    view = SignupView.as_view(template_name="taller/us/en/auth/signup.html")
    return view(request)


app_name = "usa"

urlpatterns = [
    # === CONFIGURACIÓN Y SETTINGS ===
    # URL raíz para USA - redirige al dashboard
    path("", dashboard, name="home"),
    # Incluir las rutas específicas que necesitamos
    path("dashboard/", dashboard, name="dashboard"),
    path("centro-operaciones/", dashboard_centro_operaciones, name="centro_operaciones"),
    path("centro-operaciones-espacial/", dashboard_centro_operaciones_espacial, name="centro_operaciones_espacial"),
    path("admin/dashboard/", dashboard_suscripciones, name="dashboard_suscripciones"),
    path("configuracion/", configuracion_empresa, name="configuracion"),
    path("configuracion/tecnicos/", configuracion_tecnicos, name="configuracion_tecnicos"),
    path("settings/", company_settings_view, name="company_settings"),
    path("en/settings/", futuristic_company_settings_view, name="futuristic_company_settings"),
    # API endpoints for technician management
    path("api/technician/toggle/", api_technician_toggle, name="api_technician_toggle"),
    path("api/technician/delete/", api_technician_delete, name="api_technician_delete"),
    # Test endpoint USA
    path("test/", test_usa_view, name="test"),
    # === MÓDULOS PRINCIPALES ===
    # NOTA: Los submódulos principales (clientes, vehiculos, repuestos, servicios, 
    # documentos, reportes) están incluidos en taller_main_urls.py para evitar duplicación
    # Solo incluimos aquí rutas específicas de USA que no están en el core
    # === AJAX ENDPOINTS ===
    # AJAX jerárquico para vehículos
    path("ajax/load-modelos/", ajax_views.load_modelos, name="ajax_load_modelos"),
    path("ajax/load-motores/", ajax_views.load_motores, name="ajax_load_motores"),
    path("ajax/load-cajas/", ajax_views.load_cajas, name="ajax_load_cajas"),
    path(
        "ajax/load-motores-cajas/",
        ajax_views.load_motores_cajas,
        name="ajax_load_motores_cajas",
    ),
    # AJAX específicos para USA
    path("ajax/clientes/buscar/", buscar_clientes, name="us_ajax_buscar_clientes"),
    path(
        "ajax/vehiculos-por-cliente/",
        vehiculos_por_cliente,
        name="us_ajax_vehiculos_por_cliente",
    ),
    # === AUTHENTICATION ===
    # Login para USA
    path("login/", usa_login_view, name="account_login"),
    # Signup para USA
    path("signup/", usa_signup_view, name="account_signup"),
    # Registro para USA
    path("registro/", include("scripts.onboarding_urls")),
    # === DASHBOARD DE SUSCRIPTOR ===
    path("", include("taller.analytics.urls_suscriptor")),
]
