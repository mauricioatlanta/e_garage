from django.urls import include, path

from taller import ajax_views
from taller.taller_views import dashboard_suscripciones
from taller.views_extra.ajax import buscar_clientes, vehiculos_por_cliente
from taller.views_extra.bienvenida_usa import bienvenida_usa
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
from taller.views_extra.views_trial_activate import activar_trial

# from taller.views_extra.crear_motor_caja import crear_motor, crear_caja, crear_color  # ❌ Desactivado - usando views_create_parts

app_name = "usa"


def usa_login_view(request):
    from allauth.account.views import LoginView

    request.country = "US"
    request.country_code = "US"
    return LoginView.as_view(template_name="taller/us/en/auth/login.html")(request)


def usa_signup_view(request):
    from allauth.account.views import SignupView

    request.country = "US"
    request.country_code = "US"
    return SignupView.as_view(template_name="taller/us/en/auth/signup.html")(request)


urlpatterns = [
    # 1) Home y páginas específicas USA
    path("", bienvenida_usa, name="home"),
    path(
        "dashboard/", dashboard, name="dashboard"
    ),  # si existe en taller, este gana por orden
    path("en/dashboard/", dashboard, name="dashboard_en_redirect"),
    path(
        "centro-operaciones/", dashboard_centro_operaciones, name="centro_operaciones"
    ),
    path(
        "centro-operaciones-espacial/",
        dashboard_centro_operaciones_espacial,
        name="centro_operaciones_espacial",
    ),
    path("admin/dashboard/", dashboard_suscripciones, name="dashboard_suscripciones"),
    # 2) Configuración
    path("configuracion/", configuracion_empresa, name="configuracion"),
    path(
        "configuracion/tecnicos/", configuracion_tecnicos, name="configuracion_tecnicos"
    ),
    path("settings/", company_settings_view, name="company_settings"),
    path(
        "en/settings/",
        futuristic_company_settings_view,
        name="futuristic_company_settings",
    ),
    # 3) Auth Allauth para USA (nombres globales a propósito)
    path("login/", usa_login_view, name="account_login"),
    path("signup/", usa_signup_view, name="account_signup"),
    # 4) Trial y onboarding
    path("activar-trial/", activar_trial, name="activar_trial"),
    path(
        "registro/",
        include(("scripts.onboarding_urls", "onboarding"), namespace="usa_onboarding"),
    ),
    # 5) AJAX específicos USA
    path("ajax/load-modelos/", ajax_views.load_modelos, name="ajax_load_modelos"),
    path("ajax/load-motores/", ajax_views.load_motores, name="ajax_load_motores"),
    path("ajax/load-cajas/", ajax_views.load_cajas, name="ajax_load_cajas"),
    path(
        "ajax/load-motores-cajas/",
        ajax_views.load_motores_cajas,
        name="ajax_load_motores_cajas",
    ),
    path("ajax/clientes/buscar/", buscar_clientes, name="us_ajax_buscar_clientes"),
    path(
        "ajax/vehiculos-por-cliente/",
        vehiculos_por_cliente,
        name="us_ajax_vehiculos_por_cliente",
    ),
    # 6) Autocomplete y creadores rápidos (verifica que no se dupliquen en taller.urls)
    path(
        "autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="autocomplete"),
    ),
    # path("vehiculos/crear-motor/", crear_motor, name="crear_motor"),  # ❌ Desactivado - usar vehiculos:crear_motor
    # path("vehiculos/crear-caja/", crear_caja, name="crear_caja"),    # ❌ Desactivado - usar vehiculos:crear_caja
    # path("vehiculos/crear-color/", crear_color, name="crear_color"), # ❌ Desactivado - usar vehiculos:crear_color
    # 7) Analytics (antes de taller si sus rutas son más específicas)
    path("", include("taller.analytics.urls_suscriptor")),
    # 8) Núcleo de taller (último para que no opaque lo anterior)
    path("", include(("taller.urls", "taller"), namespace="taller")),
]
