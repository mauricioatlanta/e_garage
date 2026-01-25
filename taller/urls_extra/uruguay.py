"""
URLs específicas para Uruguay (español)
Prefijo: /uy/es/
"""


def _render_first_existing(request, candidates, context=None):
    context = context or {}
    for tname in candidates:
        try:
            loader.get_template(tname)
            return render(request, tname, context)
        except TemplateDoesNotExist:
            continue
    from django.http import HttpResponse

    return HttpResponse("Template de bienvenida no encontrado.", status=500)


import logging

from django.http import HttpResponseRedirect
from django.urls import include, path
from django.shortcuts import redirect, render
from django.template import loader, TemplateDoesNotExist
from django.views.generic import TemplateView


def uruguay_home(request):
    # Canonicaliza /uy/ -> /uy/es/
    if request.path == "/uy/":
        return redirect("/uy/es/", permanent=False)
    return _render_first_existing(
        request,
        [
            "uy/es/onboarding/bienvenida.html",
            "uy/onboarding/bienvenida.html",
            "onboarding/bienvenida_uruguay.html",
            "onboarding/bienvenida.html",
        ],
    )


from taller.views_extra.views import dashboard_suscripciones
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
from taller.documentos import views_country_aware as views_documentos

# Configuración de logging para este módulo
logger = logging.getLogger(__name__)
logger.debug("CARGANDO taller/urls_extra/uruguay.py")

app_name = "uruguay"

urlpatterns = [
    # Vista de inicio para /uy/es/ - redirige a la página principal de Uruguay
    path("", uruguay_home, name="uruguay_home"),
    # URLs principales de taller (configuración, settings, etc.)
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
    # Test endpoint Uruguay
    path("test/", lambda request: HttpResponseRedirect("/uy/"), name="test"),
    # Página de bienvenida para Uruguay
    path(
        "egarage/",
        TemplateView.as_view(template_name="uy/es/onboarding/bienvenida.html"),
        name="bienvenida_uruguay",
    ),
    # Página de bienvenida alternativa (ruta estándar)
    path(
        "bienvenida/",
        TemplateView.as_view(template_name="uy/es/onboarding/bienvenida.html"),
        name="bienvenida_uruguay_alt",
    ),
    # Allauth bajo /uy/ y /uy/es/ para que /uy/es/accounts/login/ etc. funcionen
    path("accounts/", include("allauth.urls")),
    # Login para Uruguay: redirige a /accounts/login/?from=uy (registration/login.html no existe)
    path(
        "login/",
        lambda r: redirect("/accounts/login/?from=uy" + ("&" + r.GET.urlencode() if r.GET else "")),
        name="account_login",
    ),
    # Signup para Uruguay: redirige a /accounts/signup/?from=uy (preserva ?plan=, etc.)
    path(
        "signup/",
        lambda r: redirect(
            "/accounts/signup/?from=uy" + ("&" + r.GET.urlencode() if r.GET else "")
        ),
        name="account_signup_uy",
    ),
    # Activación de trial para Uruguay
    path("activar-trial/", activar_trial, name="activar_trial"),
    # Registro para Uruguay (español por defecto)
    path(
        "registro/",
        include(("scripts.onboarding_urls", "onboarding"), namespace="uruguay_onboarding"),
    ),
    # Dashboard de suscriptor
    path("", include("taller.analytics.urls_suscriptor")),
    # Servicios y documentos con namespace bajo /uy/taller/
    path(
        "taller/servicios/",
        include(("taller.servicios.urls", "servicios"), namespace="servicios_admin"),
    ),
    path(
        "taller/reportes/",
        include(("taller.reportes.urls", "reportes"), namespace="reportes_uy"),
    ),
    # Módulos principales del sistema (disponibilidad directa bajo /uy/es/)
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
    # Crear documento Uruguay
    path(
        "documentos/nuevo/",
        views_documentos.documento_crear,
        {"country_code": "uy", "lang_code": "es"},
        name="crear_documento_uy",
    ),
    # Editar documento Uruguay
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
    # Business Intelligence bajo /uy/business-intelligence/
    path(
        "business-intelligence/",
        include(
            ("taller.business_intelligence_urls", "business_intelligence"),
            namespace="business_intelligence",
        ),
    ),
    # === APIs ===
    path("api/", include(("taller.api.urls", "api"), namespace="api")),
    # === AJAX ENDPOINTS ===
    path("ajax/", include(("taller.ajax.urls", "ajax"), namespace="ajax")),
    # === MÓDULOS PRINCIPALES ===
    # Incluir URLs principales de taller (clientes, vehiculos, repuestos, etc.)
    path("", include(("taller.urls", "taller"), namespace="taller")),
    path(
        "autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="autocomplete"),
    ),
]
