from django.urls import include, path
from django.views.generic import TemplateView

from taller import ajax_views
from taller.views_extra.views import dashboard_suscripciones
from taller.views_extra.bienvenida_usa import bienvenida_usa
from taller.views_extra.company_settings_views import company_settings_view
from taller.views_extra.dashboard_empresa import (
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
from taller.documentos import views_country_aware as views_documentos

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
    # Página de bienvenida USA ES
    path(
        "es/bienvenida/",
        TemplateView.as_view(template_name="us/es/onboarding/bienvenida.html"),
        name="bienvenida_usa_es",
    ),
    # Página de bienvenida USA EN
    path(
        "en/bienvenida/",
        TemplateView.as_view(template_name="us/en/onboarding/bienvenida.html"),
        name="bienvenida_usa_en",
    ),
    path("dashboard/", dashboard, name="dashboard"),  # si existe en taller, este gana por orden
    path("en/dashboard/", dashboard, name="dashboard_en_redirect"),
    path("es/dashboard/", dashboard, name="dashboard_es_redirect"),
    # Redirigir centro-operaciones a la versión espacial fusionada
    path(
        "centro-operaciones/",
        dashboard_centro_operaciones_espacial,
        name="centro_operaciones",
    ),
    path(
        "centro-operaciones-espacial/",
        dashboard_centro_operaciones_espacial,
        name="centro_operaciones_espacial",
    ),
    # Rutas con prefijo de idioma para compatibilidad
    path(
        "es/centro-operaciones/",
        dashboard_centro_operaciones_espacial,
        name="centro_operaciones_es",
    ),
    path(
        "es/centro-operaciones-espacial/",
        dashboard_centro_operaciones_espacial,
        name="centro_operaciones_espacial_es",
    ),
    path("admin/dashboard/", dashboard_suscripciones, name="dashboard_suscripciones"),
    # 2) Configuración
    path("configuracion/", configuracion_empresa, name="configuracion"),
    path("configuracion/tecnicos/", configuracion_tecnicos, name="configuracion_tecnicos"),
    path("settings/", company_settings_view, name="company_settings"),
    path(
        "en/settings/",
        company_settings_view,  # Usar la misma vista que /us/settings/
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
    # 4.5) Pricing and subscription
    path("pricing/", precios, name="pricing"),
    path("plans/", precios, name="plans"),
    # 5) AJAX específicos USA
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
    # 6.1) Autocomplete y creadores rápidos (verifica que no se dupliquen en taller.urls)
    path(
        "autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="autocomplete"),
    ),
    # path("vehiculos/crear-motor/", crear_motor, name="crear_motor"),  # ❌ Desactivado - usar vehiculos:crear_motor
    # path("vehiculos/crear-caja/", crear_caja, name="crear_caja"),    # ❌ Desactivado - usar vehiculos:crear_caja
    # path("vehiculos/crear-color/", crear_color, name="crear_color"), # ❌ Desactivado - usar vehiculos:crear_color
    # 6) Módulos principales del sistema (antes de taller.urls)
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
    # =========================
    # Documentos USA EN (vistas genéricas country-aware)
    # =========================
    # Lista de documentos USA EN
    path(
        "en/documentos/",
        views_documentos.documentos_listar,
        {"country_code": "us", "lang_code": "en"},
        name="lista_documentos_us",
    ),
    # Crear documento USA EN
    path(
        "en/documentos/new/",
        views_documentos.documento_crear,
        {"country_code": "us", "lang_code": "en"},
        name="crear_documento_us",
    ),
    # Editar documento USA EN
    path(
        "en/documentos/<int:pk>/edit/",
        views_documentos.documento_editar,
        {"country_code": "us", "lang_code": "en"},
        name="editar_documento_us",
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
    # 7) Analytics (antes de taller si sus rutas son más específicas)
    path("", include("taller.analytics.urls_suscriptor")),
    # 8) Núcleo de taller (último para que no opaque lo anterior)
    path("", include(("taller.urls", "taller"), namespace="taller")),
]
