from django.urls import path, include
from django.views.generic import RedirectView
from django.views.generic import TemplateView
import logging
from django.http import HttpResponseRedirect
from django.shortcuts import redirect

from taller.views_extra.views import dashboard_suscripciones
from taller.views_extra.company_settings_views import company_settings_view
from taller.views_extra.country_views import test_chile_view
from taller.views_extra.dashboard_empresa import (
    dashboard_centro_operaciones,
    dashboard_centro_operaciones_espacial,
)
from taller.views_extra.centro_trabajo import (
    centro_trabajo,
    centro_trabajo_buscar,
    vehiculo_historial,
)
from taller.views_extra.views import dashboard
from taller.views_extra.ai_lab import ai_lab_dashboard
from taller.views_extra.views_configuracion import (
    configuracion_empresa,
    configuracion_tecnicos,
)
from taller.views_extra.views_trial_activate import activar_trial
from taller.views_extra.views_suscripciones import precios
from taller.documentos import views_country_aware as views_documentos

# Configuración de logging para este módulo
logger = logging.getLogger(__name__)
logger.debug("CARGANDO taller/urls_extra/chile.py")

app_name = "chile"

urlpatterns = [
    # Vista de inicio para /cl/es/ - redirige a la página principal de Chile
    path("", lambda request: HttpResponseRedirect("/cl/"), name="chile_home"),
    # URLs principales de taller (configuración, settings, etc.)
    # Centro de Trabajo / Recepción Vehicular (nueva home post-login)
    path("workspace/", centro_trabajo, name="centro_trabajo"),
    path("workspace/buscar/", centro_trabajo_buscar, name="centro_trabajo_buscar"),
    path("vehiculos/<int:vehiculo_id>/historial/", vehiculo_historial, name="vehiculo_historial"),
    # Dashboard / Centro de Operaciones (métricas, reportes)
    path("dashboard/", dashboard, name="dashboard"),
    path("lab/", ai_lab_dashboard, name="ai_lab"),
    path("centro-operaciones/", dashboard_centro_operaciones, name="centro_operaciones"),
    path("settings/", company_settings_view, name="company_settings"),  # ⚙️ Centro de Ajustes
    # Alias público: redirige al Settings Center (evita 403)
    path(
        "configuracion/",
        RedirectView.as_view(pattern_name="chile:company_settings", permanent=False),
        name="configuracion",
    ),
    # Configuración real (dueño)
    path(
        "configuracion/empresa/",
        configuracion_empresa,
        name="configuracion_empresa",
    ),
    path(
        "configuracion/tecnicos/", configuracion_tecnicos, name="configuracion_tecnicos"
    ),  # Configuración técnicos
    # Página de bienvenida alternativa (ruta estándar)
    path(
        "bienvenida/",
        TemplateView.as_view(template_name="cl/es/onboarding/bienvenida.html"),
        name="bienvenida_chile_alt",
    ),
    # Allauth bajo /cl/es/ para que /cl/es/accounts/login/ etc. funcionen
    path("accounts/", include("allauth.urls")),
    # Signup corto /cl/es/signup/ -> /accounts/signup/?from=cl (preserva ?plan=, etc.)
    path(
        "signup/",
        lambda r: redirect(
            "/accounts/signup/?from=cl" + ("&" + r.GET.urlencode() if r.GET else "")
        ),
        name="account_signup_cl_es",
    ),
    # Login para suscriptores de Chile (redirige al login global, pero aquí puedes poner una vista personalizada si lo deseas)
    path(
        "login/",
        TemplateView.as_view(template_name="registration/login.html"),
        name="account_login",
    ),
    # Activación de trial para Chile
    path("activar-trial/", activar_trial, name="activar_trial"),
    # Precios y planes para Chile
    path("precios/", precios, name="precios"),
    # Registro para Chile (español por defecto)
    path(
        "registro/",
        include(("scripts.onboarding_urls", "onboarding"), namespace="chile_onboarding"),
    ),
    # === AJAX JERÁRQUICO - VEHÍCULOS ===
    # ❌ DESACTIVADOS: Endpoints legacy que no filtran por modelo
    # path("taller/ajax/load-modelos/", ajax_views.load_modelos, name="ajax_load_modelos"),
    # path("taller/ajax/load-motores/", ajax_views.load_motores, name="ajax_load_motores"),
    # path("taller/ajax/load-cajas/", ajax_views.load_cajas, name="ajax_load_cajas"),
    # path("taller/ajax/load-motores-cajas/", ajax_views.load_motores_cajas, name="ajax_load_motores_cajas"),
    # Módulos principales (incluir cuando estén funcionando)
    # === MÓDULOS PRINCIPALES ===
    # NOTA: Los submódulos principales (clientes, vehiculos, repuestos, servicios,
    # documentos, reportes) están incluidos en taller_main_urls.py para evitar duplicación
    # Solo incluimos aquí rutas específicas de Chile que no están en el core
    # Dashboard de suscriptor
    path("", include("taller.analytics.urls_suscriptor")),
    # Servicios y documentos con namespace bajo /cl/taller/
    path(
        "taller/servicios/",
        include(("taller.servicios.urls", "servicios"), namespace="servicios_admin"),
    ),
    # DOCUMENTOS MOVIDO A gestion_taller/urls.py para evitar duplicación
    # path('taller/documentos/', include(('taller.documentos.urls', 'documentos'), namespace='documentos')),
    path(
        "taller/reportes/",
        include(("taller.reportes.urls", "reportes"), namespace="reportes_cl"),
    ),
    # Módulos principales del sistema (disponibilidad directa bajo /cl/es/)
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
    # Documentos Chile (vistas genéricas country-aware)
    # =========================
    # Lista de documentos Chile
    path(
        "documentos/lista/",
        views_documentos.documentos_listar,
        {"country_code": "cl", "lang_code": "es"},
        name="lista_documentos_cl",
    ),
    # Crear documento Chile
    path(
        "documentos/nuevo/",
        views_documentos.documento_crear,
        {"country_code": "cl", "lang_code": "es"},
        name="crear_documento_cl",
    ),
    # Editar documento Chile
    path(
        "documentos/<int:pk>/editar/",
        views_documentos.documento_editar,
        {"country_code": "cl", "lang_code": "es"},
        name="editar_documento_cl",
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
    # Business Intelligence bajo /cl/business-intelligence/
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
    # path('api/', include('taller.api.urls')),
    path(
        "autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="autocomplete"),
    ),
    # Centro de Ingreso Pro (kiosk recepción) — solo si existe el módulo taller.ops
    # path("ops/", include(("taller.ops.urls", "ops"), namespace="ops")),
    # Crear nuevos motores, cajas y colores (usando views_create_parts)
    # path('vehiculos/crear-motor/', crear_motor, name='crear_motor'),  # ❌ Desactivado - usar vehiculos:crear_motor
    # path('vehiculos/crear-caja/', crear_caja, name='crear_caja'),    # ❌ Desactivado - usar vehiculos:crear_caja
    # path('vehiculos/crear-color/', crear_color, name='crear_color'), # ❌ Desactivado - usar vehiculos:crear_color
    # path('analytics/', include('taller.analytics.urls')),
    # path('gestion/', include('gestion_taller.urls')),
]
