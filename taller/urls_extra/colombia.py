"""
URLs específicas para Colombia (español)
Prefijo: /co/
"""

import logging

from django.http import HttpResponseRedirect
from django.urls import include, path
from django.views.generic import TemplateView

# Configuración de logging para este módulo
logger = logging.getLogger(__name__)
logger.debug("CARGANDO taller/urls_extra/colombia.py")

from taller.taller_views import dashboard_suscripciones
from taller.views_extra.company_settings_views import company_settings_view
from taller.views_extra.dashboard_empresa import (
    dashboard_centro_operaciones,
    dashboard_centro_operaciones_espacial,
)
from taller.views_extra.views import dashboard
from taller.views_extra.views_configuracion import (
    configuracion_empresa,
    configuracion_tecnicos,
)
from taller.views_extra.views_trial_activate import activar_trial
from taller.views_extra.views_suscripciones import precios

app_name = "colombia"


def colombia_login_view(request):
    from allauth.account.views import LoginView

    request.country = "CO"
    request.country_code = "CO"
    return LoginView.as_view(template_name="registration/login.html")(request)


def colombia_signup_view(request):
    from allauth.account.views import SignupView

    request.country = "CO"
    request.country_code = "CO"
    return SignupView.as_view(template_name="registration/signup.html")(request)


urlpatterns = [
    # Vista de inicio para /co/es/ - redirige a la página de bienvenida
    path("", lambda request: HttpResponseRedirect("/co/egarage/"), name="colombia_home"),
    # URLs principales de taller
    path("dashboard/", dashboard, name="dashboard"),
    path("centro-operaciones/", dashboard_centro_operaciones, name="centro_operaciones"),
    path(
        "centro-operaciones-espacial/",
        dashboard_centro_operaciones_espacial,
        name="centro_operaciones_espacial",
    ),
    path("admin/dashboard/", dashboard_suscripciones, name="dashboard_suscripciones"),
    path("configuracion/", configuracion_empresa, name="configuracion"),
    path("configuracion/tecnicos/", configuracion_tecnicos, name="configuracion_tecnicos"),
    path("settings/", company_settings_view, name="company_settings"),
    # Página de bienvenida para Colombia
    path(
        "egarage/",
        TemplateView.as_view(template_name="onboarding/bienvenida_colombia.html"),
        name="bienvenida_colombia",
    ),
    # Pricing y planes para Colombia
    path("pricing/", precios, name="pricing"),
    path("precios/", precios, name="precios"),
    # Login y Signup para Colombia
    path("login/", colombia_login_view, name="account_login"),
    path("signup/", colombia_signup_view, name="account_signup"),
    # Activación de trial para Colombia
    path("activar-trial/", activar_trial, name="activar_trial"),
    # Registro para Colombia (español por defecto)
    path(
        "registro/",
        include(("scripts.onboarding_urls", "onboarding"), namespace="colombia_onboarding"),
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
    # Business Intelligence
    path(
        "business-intelligence/",
        include(
            ("taller.business_intelligence_urls", "business_intelligence"),
            namespace="business_intelligence",
        ),
    ),
    # APIs
    path("api/", include(("taller.api.urls", "api"), namespace="api")),
    # AJAX endpoints
    path("ajax/", include(("taller.ajax.urls", "ajax"), namespace="ajax")),
    # Analytics
    path("", include("taller.analytics.urls_suscriptor")),
    # Módulos principales de taller
    path("", include(("taller.urls", "taller"), namespace="taller")),
    # Autocomplete
    path(
        "autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="autocomplete"),
    ),
]
