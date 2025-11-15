"""
URLs específicas para Perú 🇵🇪
Patrón: /pe/ seguido de las rutas específicas
"""

from django.urls import include, path

from taller import ajax_views
from taller.taller_views import dashboard_suscripciones
from taller.views_extra.company_settings_views import company_settings_view
from taller.views_extra.dashboard_empresa import (
    dashboard_centro_operaciones,
    dashboard_centro_operaciones_espacial,
)
from taller.views_extra.futuristic_company_settings_views import (
    futuristic_company_settings_view,
)
from taller.views_extra.views import dashboard
from taller.views_extra.views_configuracion import (
    configuracion_empresa,
    configuracion_tecnicos,
)
from taller.views_extra.views_suscripciones import precios
from taller.views_extra.views_trial_activate import activar_trial

# Importar vistas específicas de Perú
from taller.views_extra.pe_views import (
    PELocalizationView,
    api_calcular_impuestos_peru,
    api_ciudades_por_estado_pe,
    api_estados_peru,
    api_marcas_vehiculos_peru,
    api_modelos_por_marca_pe,
    api_traducir_servicios_pe,
    cambiar_idioma_pe,
    demo_peru_personalization,
)

app_name = "peru"


def peru_login_view(request):
    """Vista de login para Perú"""
    from allauth.account.views import LoginView
    from django.utils.translation import activate

    request.country = "PE"
    request.country_code = "PE"
    # Activar español
    activate("es")
    request.session["django_language"] = "es"
    return LoginView.as_view(template_name="account/login_peru.html")(request)


def peru_signup_view(request):
    """Vista de registro para Perú"""
    from allauth.account.views import SignupView
    from django.utils.translation import activate

    request.country = "PE"
    request.country_code = "PE"
    # Activar español
    activate("es")
    request.session["django_language"] = "es"
    return SignupView.as_view(template_name="account/signup_peru.html")(request)


def bienvenida_peru(request):
    """Vista de bienvenida para Perú"""
    from django.shortcuts import render

    return render(request, "onboarding/bienvenida_peru.html")


urlpatterns = [
    # 1) Home y páginas específicas Perú
    path("", bienvenida_peru, name="home"),
    path("dashboard/", dashboard, name="dashboard"),
    path("es/dashboard/", dashboard, name="dashboard_es_redirect"),
    # 2) Centro de operaciones
    path("centro-operaciones/", dashboard_centro_operaciones, name="centro_operaciones"),
    path(
        "centro-operaciones-espacial/",
        dashboard_centro_operaciones_espacial,
        name="centro_operaciones_espacial",
    ),
    # 3) Login y Signup personalizados para Perú
    path("login/", peru_login_view, name="login"),
    path("accounts/login/", peru_login_view, name="account_login"),
    path("signup/", peru_signup_view, name="signup"),
    path("accounts/signup/", peru_signup_view, name="account_signup"),
    # 4) Configuración
    path("configuracion/", configuracion_empresa, name="configuracion_empresa"),
    path(
        "configuracion/empresa/",
        company_settings_view,
        name="company_settings",
    ),
    path(
        "configuracion/futurista/",
        futuristic_company_settings_view,
        name="futuristic_company_settings",
    ),
    path("configuracion/tecnicos/", configuracion_tecnicos, name="configuracion_tecnicos"),
    # 4.5) Precios y suscripciones
    path("precios/", precios, name="pricing"),
    path("planes/", precios, name="plans"),
    path("suscripciones/", dashboard_suscripciones, name="dashboard_suscripciones"),
    path("trial/activar/", activar_trial, name="activar_trial"),
    # 5) AJAX específicos Perú
    path("ajax/load-modelos/", ajax_views.load_modelos, name="ajax_load_modelos"),
    path("ajax/load-motores/", ajax_views.load_motores, name="ajax_load_motores"),
    path("ajax/load-cajas/", ajax_views.load_cajas, name="ajax_load_cajas"),
    path(
        "ajax/load-motores-cajas/",
        ajax_views.load_motores_cajas,
        name="ajax_load_motores_cajas",
    ),
    # AJAX endpoints compartidos (clientes, vehículos, marcas, modelos, etc.)
    path("ajax/", include(("taller.ajax.urls", "ajax"), namespace="ajax")),
    # 6) APIs
    path("api/", include(("taller.api.urls", "api"), namespace="api")),
    # 6.1) APIs específicas de Perú
    path("api/estados/", api_estados_peru, name="api_estados_peru"),
    path(
        "api/ciudades/<int:estado_id>/",
        api_ciudades_por_estado_pe,
        name="api_ciudades_por_estado_pe",
    ),
    path("api/marcas/", api_marcas_vehiculos_peru, name="api_marcas_peru"),
    path("api/modelos/", api_modelos_por_marca_pe, name="api_modelos_peru"),
    path(
        "api/calcular-impuestos/",
        api_calcular_impuestos_peru,
        name="api_calcular_impuestos_peru",
    ),
    path(
        "api/traducir-servicios/",
        api_traducir_servicios_pe,
        name="api_traducir_servicios_pe",
    ),
    # 7) Autocomplete
    path(
        "autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="autocomplete"),
    ),
    # 8) Módulos principales del sistema
    path(
        "clientes/",
        include(("taller.clientes.urls", "clientes"), namespace="clientes"),
    ),
    path(
        "vehiculos/",
        include(("taller.vehiculos.urls", "vehiculos"), namespace="vehiculos"),
    ),
    path(
        "documentos/",
        include(("taller.documentos.urls", "documentos"), namespace="documentos"),
    ),
    path(
        "repuestos/",
        include(("taller.repuestos.urls", "repuestos"), namespace="repuestos"),
    ),
    path(
        "servicios/",
        include(("taller.servicios.urls", "servicios"), namespace="servicios"),
    ),
    path(
        "reportes/",
        include(("taller.reportes.urls", "reportes"), namespace="reportes"),
    ),
    path(
        "tecnicos/",
        include(("taller.tecnicos.urls", "tecnicos"), namespace="tecnicos"),
    ),
    # 9) Demo de personalización Perú
    path("demo/personalizacion/", demo_peru_personalization, name="demo_personalization"),
    path("demo/localizacion/", PELocalizationView.as_view(), name="localization_demo"),
    # 10) Cambiar idioma
    path("i18n/cambiar-idioma/", cambiar_idioma_pe, name="cambiar_idioma"),
    # 11) Analytics (antes de taller si sus rutas son más específicas)
    path("", include("taller.analytics.urls_suscriptor")),
    # 12) Núcleo de taller (último para que no opaque lo anterior)
    path("", include(("taller.urls", "taller"), namespace="taller")),
]
