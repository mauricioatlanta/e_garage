from django.urls import path, include
from django.views.generic import TemplateView
import logging
from django.http import HttpResponseRedirect

from taller.taller_views import dashboard_suscripciones
from taller.views_extra.company_settings_views import company_settings_view
from taller.views_extra.country_views import test_chile_view
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
from taller.documentos import views_country_aware as views_documentos

# Configuración de logging para este módulo
logger = logging.getLogger(__name__)
logger.debug("CARGANDO taller/urls_extra/uruguay.py")

app_name = "uruguay"


def strip_es(request, rest=""):
    # /uy/es/...  -> /uy/...
    return HttpResponseRedirect(
        f"/uy/{rest}".rstrip("/") + ("/" if rest and not rest.endswith("/") else "")
    )


urlpatterns = [
    # Alias: /uy/es/ -> /uy/
    path("es/", strip_es),
    path("es/<path:rest>", strip_es),
    # Home UY - NO redirige a /cl/
    path(
        "",
        TemplateView.as_view(template_name="uy/es/onboarding/bienvenida.html"),
        name="uruguay_home",
    ),
    # URLs principales de taller
    path("dashboard/", dashboard, name="dashboard"),
    path("centro-operaciones/", dashboard_centro_operaciones, name="centro_operaciones"),
    # Página de bienvenida
    path(
        "bienvenida/",
        TemplateView.as_view(template_name="uy/es/onboarding/bienvenida.html"),
        name="bienvenida_uruguay_alt",
    ),
    # Login
    path(
        "login/",
        TemplateView.as_view(template_name="registration/login.html"),
        name="account_login",
    ),
    # Activación de trial
    path("activar-trial/", activar_trial, name="activar_trial"),
    # Registro
    path(
        "registro/",
        include(("scripts.onboarding_urls", "onboarding"), namespace="uruguay_onboarding"),
    ),
    # Dashboard de suscriptor
    path("", include("taller.analytics.urls_suscriptor")),
    # Servicios y documentos
    path(
        "taller/servicios/",
        include(("taller.servicios.urls", "servicios"), namespace="servicios_admin"),
    ),
    path(
        "taller/reportes/",
        include(("taller.reportes.urls", "reportes"), namespace="reportes_uy"),
    ),
    # Módulos principales del sistema (con country_code="uy")
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
    # Documentos Uruguay (vistas genéricas country-aware)
    path(
        "documentos/lista/",
        views_documentos.documentos_listar,
        {"country_code": "uy", "lang_code": "es"},
        name="lista_documentos_uy",
    ),
    path(
        "documentos/nuevo/",
        views_documentos.documento_crear,
        {"country_code": "uy", "lang_code": "es"},
        name="crear_documento_uy",
    ),
    path(
        "documentos/<int:pk>/editar/",
        views_documentos.documento_editar,
        {"country_code": "uy", "lang_code": "es"},
        name="editar_documento_uy",
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
    path("ajax/", include(("taller.ajax.urls", "ajax"), namespace="ajax")),
    # URLs principales de taller
    path("", include(("taller.urls", "taller"), namespace="taller")),
    path(
        "autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="autocomplete"),
    ),
]
