"""
URLs específicas para México 🇲🇽
Patrón: /mx/ seguido de las rutas específicas
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

from taller.views_extra.mx_views import (
    MXLocalizationView,
    api_calcular_impuestos_mexico,
    api_ciudades_por_estado_mx,
    api_estados_mexico,
    api_marcas_vehiculos_mexico,
    api_modelos_por_marca_mx,
    api_traducir_servicios_mx,
    cambiar_idioma_mx,
    demo_mexico_personalization,
)

app_name = "mexico"


def mexico_login_view(request):
    """Vista de login para México"""
    from allauth.account.views import LoginView
    from django.utils.translation import activate

    request.country = "MX"
    request.country_code = "MX"
    activate("es")
    request.session["django_language"] = "es"
    return LoginView.as_view(template_name="account/login.html")(request)


def mexico_signup_view(request):
    """Vista de registro para México"""
    from allauth.account.views import SignupView
    from django.utils.translation import activate

    request.country = "MX"
    request.country_code = "MX"
    activate("es")
    request.session["django_language"] = "es"
    return SignupView.as_view(template_name="account/signup.html")(request)


def bienvenida_mexico(request):
    """Vista de bienvenida para México"""
    from django.shortcuts import render

    return render(request, "onboarding/bienvenida_mexico.html")


urlpatterns = [
    # Home y páginas específicas México
    path("", bienvenida_mexico, name="home"),
    path("dashboard/", dashboard, name="dashboard"),
    path("es/dashboard/", dashboard, name="dashboard_es_redirect"),
    # Centro de operaciones
    path("centro-operaciones/", dashboard_centro_operaciones, name="centro_operaciones"),
    path(
        "centro-operaciones-espacial/",
        dashboard_centro_operaciones_espacial,
        name="centro_operaciones_espacial",
    ),
    # Login y Signup personalizados para México
    path("login/", mexico_login_view, name="login"),
    path("accounts/login/", mexico_login_view, name="account_login"),
    path("signup/", mexico_signup_view, name="signup"),
    path("accounts/signup/", mexico_signup_view, name="account_signup"),
    # Configuración
    path("configuracion/", configuracion_empresa, name="configuracion_empresa"),
    path("configuracion/empresa/", company_settings_view, name="company_settings"),
    path(
        "configuracion/futurista/",
        futuristic_company_settings_view,
        name="futuristic_company_settings",
    ),
    path("configuracion/tecnicos/", configuracion_tecnicos, name="configuracion_tecnicos"),
    # Precios y suscripciones
    path("precios/", precios, name="pricing"),
    path("planes/", precios, name="plans"),
    path("suscripciones/", dashboard_suscripciones, name="dashboard_suscripciones"),
    path("trial/activar/", activar_trial, name="activar_trial"),
    # AJAX específicos México
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
    # APIs
    path("api/", include(("taller.api.urls", "api"), namespace="api")),
    path("api/estados/", api_estados_mexico, name="api_estados_mexico"),
    path(
        "api/ciudades/<int:estado_id>/",
        api_ciudades_por_estado_mx,
        name="api_ciudades_por_estado_mx",
    ),
    path("api/marcas/", api_marcas_vehiculos_mexico, name="api_marcas_mexico"),
    path("api/modelos/", api_modelos_por_marca_mx, name="api_modelos_mexico"),
    path(
        "api/calcular-impuestos/",
        api_calcular_impuestos_mexico,
        name="api_calcular_impuestos_mexico",
    ),
    path(
        "api/traducir-servicios/",
        api_traducir_servicios_mx,
        name="api_traducir_servicios_mx",
    ),
    # Autocomplete
    path(
        "autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="autocomplete"),
    ),
    # Módulos principales del sistema
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
    # Demos y localización
    path("demo/personalizacion/", demo_mexico_personalization, name="demo_personalization"),
    path("demo/localizacion/", MXLocalizationView.as_view(), name="localization_demo"),
    # Cambiar idioma
    path("i18n/cambiar-idioma/", cambiar_idioma_mx, name="cambiar_idioma"),
    # Analytics
    path("", include("taller.analytics.urls_suscriptor")),
    # Núcleo de taller
    path("", include(("taller.urls", "taller"), namespace="taller")),
]
