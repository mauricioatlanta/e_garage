"""
URLs específicas para Brasil 🇧🇷
Patrón: /br/ seguido de las rutas específicas
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

# Importar vistas específicas de Brasil
from taller.views_extra.br_views import (
    BRLocalizationView,
    api_calcular_impuestos_brasil,
    api_ciudades_por_estado_br,
    api_estados_brasil,
    api_marcas_vehiculos_brasil,
    api_modelos_por_marca_br,
    api_traducir_servicios_br,
    cambiar_idioma_br,
    demo_brasil_personalization,
)

app_name = "brasil"


def brasil_login_view(request):
    """Vista de login para Brasil"""
    from allauth.account.views import LoginView

    request.country = "BR"
    request.country_code = "BR"
    # Usar plantilla genérica de account
    return LoginView.as_view(template_name="account/login.html")(request)


def brasil_signup_view(request):
    """Vista de registro para Brasil"""
    from allauth.account.views import SignupView

    request.country = "BR"
    request.country_code = "BR"
    # Usar plantilla específica de Brasil en portugués
    return SignupView.as_view(template_name="account/signup_brasil.html")(request)


def bienvenida_brasil(request):
    """Vista de bienvenida para Brasil"""
    from django.shortcuts import render

    return render(request, "onboarding/bienvenida_brasil.html")


urlpatterns = [
    # 1) Home y páginas específicas Brasil
    path("", bienvenida_brasil, name="home"),
    path("dashboard/", dashboard, name="dashboard"),
    path("pt/dashboard/", dashboard, name="dashboard_pt_redirect"),
    # 2) Centro de operaciones
    path("centro-operacoes/", dashboard_centro_operaciones, name="centro_operaciones"),
    path(
        "centro-operacoes-espacial/",
        dashboard_centro_operaciones_espacial,
        name="centro_operaciones_espacial",
    ),
    # 3) Login y Signup personalizados para Brasil
    path("login/", brasil_login_view, name="login"),
    path("accounts/login/", brasil_login_view, name="account_login"),
    path("signup/", brasil_signup_view, name="signup"),
    path("accounts/signup/", brasil_signup_view, name="account_signup"),
    # 4) Configuración
    path("configuracao/", configuracion_empresa, name="configuracion_empresa"),
    path(
        "configuracao/empresa/",
        company_settings_view,
        name="company_settings",
    ),
    path(
        "configuracao/futurista/",
        futuristic_company_settings_view,
        name="futuristic_company_settings",
    ),
    path("configuracao/tecnicos/", configuracion_tecnicos, name="configuracion_tecnicos"),
    # 4.5) Preços e assinaturas
    path("precos/", precios, name="pricing"),
    path("planos/", precios, name="plans"),
    path("assinaturas/", dashboard_suscripciones, name="dashboard_suscripciones"),
    path("trial/ativar/", activar_trial, name="activar_trial"),
    # 5) AJAX específicos Brasil
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
    # 6.1) APIs específicas de Brasil
    path("api/estados/", api_estados_brasil, name="api_estados_brasil"),
    path(
        "api/cidades/<int:estado_id>/",
        api_ciudades_por_estado_br,
        name="api_ciudades_por_estado_br",
    ),
    path("api/marcas/", api_marcas_vehiculos_brasil, name="api_marcas_brasil"),
    path("api/modelos/", api_modelos_por_marca_br, name="api_modelos_brasil"),
    path(
        "api/calcular-impostos/",
        api_calcular_impuestos_brasil,
        name="api_calcular_impuestos_brasil",
    ),
    path(
        "api/traduzir-servicos/",
        api_traducir_servicios_br,
        name="api_traducir_servicios_br",
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
        "veiculos/",
        include(("taller.vehiculos.urls", "vehiculos"), namespace="vehiculos"),
    ),
    path(
        "documentos/",
        include(("taller.documentos.urls", "documentos"), namespace="documentos"),
    ),
    path(
        "pecas/",
        include(("taller.repuestos.urls", "repuestos"), namespace="pecas"),
    ),
    path(
        "servicos/",
        include(("taller.servicios.urls", "servicios"), namespace="servicos"),
    ),
    path(
        "relatorios/",
        include(("taller.reportes.urls", "reportes"), namespace="relatorios"),
    ),
    path(
        "tecnicos/",
        include(("taller.tecnicos.urls", "tecnicos"), namespace="tecnicos"),
    ),
    # 9) Demo de personalización Brasil
    path("demo/personalizacao/", demo_brasil_personalization, name="demo_personalization"),
    path("demo/localizacao/", BRLocalizationView.as_view(), name="localization_demo"),
    # 10) Cambiar idioma
    path("i18n/trocar-idioma/", cambiar_idioma_br, name="cambiar_idioma"),
    # 11) Analytics (antes de taller si sus rutas son más específicas)
    path("", include("taller.analytics.urls_suscriptor")),
    # 12) Núcleo de taller (último para que no opaque lo anterior)
    path("", include(("taller.urls", "taller"), namespace="taller")),
]
