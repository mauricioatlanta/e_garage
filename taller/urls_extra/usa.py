"""
URLs específicas para USA (inglés)
Prefijo: /us/
"""

from django.urls import include, path

from taller import ajax_views
from taller.views_extra.ajax import buscar_clientes, vehiculos_por_cliente
from taller.views_extra.country_views import dashboard_usa_view, test_usa_view
from taller.views_extra.landing_usa import landing_usa


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
    # Landing page profesional para USA
    path("", landing_usa, name="home"),
    path("dashboard/", dashboard_usa_view, name="dashboard"),
    # Centro de Operaciones Espacial para USA
    path(
        "centro-operaciones-espacial/",
        dashboard_usa_view,
        name="centro_operaciones_espacial",
    ),
    # Test endpoint USA
    path("test/", test_usa_view, name="test"),
    # === MÓDULOS PRINCIPALES ===
    # Vehículos - ahora manejado por el namespace vehiculos_usa en urls.py principal
    # Clientes
    path("clientes/", include("taller.clientes.urls")),
    # Repuestos
    path("repuestos/", include("taller.repuestos.urls")),
    # Servicios
    path(
        "servicios/",
        include(("taller.servicios.urls", "servicios"), namespace="servicios"),
    ),
    # Documentos
    path(
        "documentos/",
        include(("taller.documentos.urls", "documentos"), namespace="documentos"),
    ),
    # Reportes
    path(
        "reportes/",
        include(("taller.reportes.urls", "reportes"), namespace="reportes_us"),
    ),
    # === CONFIGURACIÓN Y SETTINGS ===
    # Incluir URLs principales de taller (configuración, settings, etc.)
    path("", include("taller.taller_main_urls")),
    # Incluir URLs de taller (técnicos, settings, etc.)
    path("", include("taller.urls")),
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
