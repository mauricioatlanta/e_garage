"""
URLs específicas para Argentina (español)
Prefijo: /ar/es/
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


def argentina_home(request):
    # Canonicaliza /ar/ -> /ar/es/
    if request.path == "/ar/":
        return redirect("/ar/es/", permanent=False)
    return _render_first_existing(
        request,
        [
            "ar/es/onboarding/bienvenida.html",
            "ar/onboarding/bienvenida.html",
            "onboarding/bienvenida_argentina.html",
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
logger.debug("CARGANDO taller/urls_extra/argentina.py")

app_name = "argentina"

urlpatterns = [
    # Vista de inicio para /ar/es/ - redirige a la página principal de Argentina
    path("", argentina_home, name="argentina_home"),
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
    # Test endpoint Argentina
    path("test/", lambda request: HttpResponseRedirect("/ar/"), name="test"),
    # Página de bienvenida para Argentina
    path(
        "egarage/",
        TemplateView.as_view(template_name="onboarding/bienvenida_argentina.html"),
        name="bienvenida_argentina",
    ),
    # Página de bienvenida alternativa (ruta estándar)
    path(
        "bienvenida/",
        TemplateView.as_view(template_name="ar/es/onboarding/bienvenida.html"),
        name="bienvenida_argentina_alt",
    ),
    # Login para suscriptores de Argentina
    path(
        "login/",
        TemplateView.as_view(template_name="registration/login.html"),
        name="account_login",
    ),
    # Activación de trial para Argentina
    path("activar-trial/", activar_trial, name="activar_trial"),
    # Registro para Argentina (español por defecto)
    path(
        "registro/",
        include(("scripts.onboarding_urls", "onboarding"), namespace="argentina_onboarding"),
    ),
    # Dashboard de suscriptor
    path("", include("taller.analytics.urls_suscriptor")),
    # Servicios y documentos con namespace bajo /ar/taller/
    path(
        "taller/servicios/",
        include(("taller.servicios.urls", "servicios"), namespace="servicios_admin"),
    ),
    path(
        "taller/reportes/",
        include(("taller.reportes.urls", "reportes"), namespace="reportes_ar"),
    ),
    # Módulos principales del sistema (disponibilidad directa bajo /ar/es/)
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
    # Documentos Argentina (vistas genéricas country-aware)
    path(
        "documentos/lista/",
        views_documentos.documentos_listar,
        {"country_code": "ar", "lang_code": "es"},
        name="lista_documentos_ar",
    ),
    # Crear documento Argentina
    path(
        "documentos/nuevo/",
        views_documentos.documento_crear,
        {"country_code": "ar", "lang_code": "es"},
        name="crear_documento_ar",
    ),
    # Editar documento Argentina
    path(
        "documentos/<int:pk>/editar/",
        views_documentos.documento_editar,
        {"country_code": "ar", "lang_code": "es"},
        name="editar_documento_ar",
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
    # Business Intelligence bajo /ar/business-intelligence/
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
