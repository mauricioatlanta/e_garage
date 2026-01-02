from urllib.parse import urlencode

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView
from django.views.i18n import JavaScriptCatalog  # 👈 Para catálogo JS

from taller.views.country_aware_auth import country_aware_login
from taller.views_extra.custom_signup import CustomSignupView
from taller.views_extra.lang_switch import set_language_us
from taller.views_extra.login_redirector import login_redirector
from taller.views_extra.logout_redirect_view import logout_redirect_view
from taller.views_extra.registro_exitoso import registro_exitoso
from taller.views_health import health_check, health_simple

# Importar vista de suscripción bloqueada
from taller.views_extra.suscripcion import registro, suscripcion_bloqueada
from taller.views_extra.admin_suscriptores import (
    admin_suscriptores,
    extender_suscripcion_ajax,
    detalle_suscriptor,
)

# Forzar importación del admin de WhatsApp para que se registre
# Capturamos cualquier excepción para que no rompa el admin si hay problemas
try:
    import whatsapp.admin  # noqa: F401
except Exception:
    # Silenciosamente ignorar errores de importación para no romper el admin
    pass

# Importar vistas de trial
from taller.views_extra.views_trial import registro_trial
from taller.views_extra.views_trial_activate import activar_trial

# gestion_taller/urls.py — archivo raíz de URLs con migración a países


def redirect_to_home(request):
    """Redirige a la página principal basada en el país del usuario"""

    # Si el usuario está autenticado, usar el país de su empresa
    if request.user.is_authenticated:
        try:
            if hasattr(request.user, "empresa") and request.user.empresa:
                pais = request.user.empresa.pais
                if pais == "CL":
                    return redirect("/cl/")
                elif pais == "US":
                    return redirect("/us/")
                elif pais == "AR":
                    return redirect("/ar/")
                elif pais == "UY":
                    return redirect("/uy/")
        except Exception:
            pass

    # Si hay contexto de país en el request (desde middleware)
    if hasattr(request, "country"):
        country = request.country
        if country == "CL":
            return redirect("/cl/")
        elif country == "US":
            return redirect("/us/")
        elif country == "AR":
            return redirect("/ar/")
        elif country == "UY":
            return redirect("/uy/")

    # Fallback: redirigir a Chile por defecto (cambiar de USA a CL)
    return redirect("/cl/")


def redirect_qs(to):
    def view(request, **kwargs):
        params = request.GET.copy()
        # Si hay kwargs (por ejemplo, uidb36, key), formatear la URL
        url = to.format(**kwargs) if kwargs else to
        if params:
            url = f"{url}?{urlencode(params, doseq=True)}"
        return redirect(url)

    return view


def redirect_cl_to_es(request, path=None):
    """Redirect /cl/... to /cl/es/... preserving the rest of the path"""
    if path:
        # If path is provided as parameter, use it
        new_path = f"/cl/es/{path}"
    else:
        # Get the path after /cl/
        path_after_cl = request.path[3:]  # Remove '/cl' from the beginning
        new_path = f"/cl/es{path_after_cl}"

    # Preserve query parameters
    if request.GET:
        query_string = request.GET.urlencode()
        new_path = f"{new_path}?{query_string}"

    return redirect(new_path)


def country_aware_clientes_redirect(request):
    """Redirect /cl/clientes/ to the correct country-specific URL based on user's company"""
    # If user is authenticated and has a company, redirect to their country
    if request.user.is_authenticated:
        try:
            if hasattr(request.user, "empresa") and request.user.empresa:
                if request.user.empresa.pais == "US":
                    return redirect("/us/clientes/")
                elif request.user.empresa.pais == "CL":
                    return redirect("/cl/es/clientes/")
        except Exception:
            pass

    # Fallback: redirect to Chile (original behavior)
    return redirect("/cl/es/clientes/")


urlpatterns = [
    path("clientes/", include(("taller.urls_clientes", "clientes"), namespace="clientes")),
    # Portal del Cliente
    path("portal/", include("taller.portal.urls")),
    # Página de inicio - Selección de país
    path("", TemplateView.as_view(template_name="landing/seleccionar_pais.html"), name="home"),
    # Panel de administración de suscriptores (ANTES de admin.site.urls para que no sea capturado)
    path("admin/suscriptores/", admin_suscriptores, name="admin_suscriptores"),
    path(
        "admin/suscriptores/<int:empresa_id>/", detalle_suscriptor, name="admin_detalle_suscriptor"
    ),
    path(
        "admin/suscriptores/<int:empresa_id>/extender/",
        extender_suscripcion_ajax,
        name="admin_extender_suscripcion",
    ),
    # Admin de Django (después de las rutas personalizadas)
    path("admin/", admin.site.urls),
    # Health check para monitoreo
    path("health/", health_check, name="health_check"),
    path("health-simple/", health_simple, name="health_simple"),
    # Vista temporal para verificar documentos
    path(
        "verificar-docs/",
        lambda request: __import__("verificar_docs_view").verificar_documentos(request),
        name="verificar_docs",
    ),
    # URLs de Trial - Sistema de 30 días
    path("registro-trial/", registro_trial, name="registro_trial"),
    path("activar-trial/", activar_trial, name="activar_trial"),
    path("activar/", activar_trial, name="activar_trial_short"),
    # URL de registro general
    path("registro/", registro, name="registro"),
    # Contacto de ventas
    path(
        "contacto-ventas/",
        lambda request: redirect(
            "https://wa.me/56912345678?text=Hola%20quiero%20información%20sobre%20el%20plan%20empresarial%20de%20eGarage"
        ),
        name="contacto_ventas",
    ),
    # Páginas de bienvenida por país
    path(
        "bienvenida/cl/",
        TemplateView.as_view(template_name="taller/bienvenida_chile.html"),
        name="bienvenida_chile",
    ),
    # Login personalizado con contexto de país
    path("accounts/login/", country_aware_login, name="account_login"),
    # Signup personalizado con CustomSignupView (ANTES de allauth.urls para que tenga prioridad)
    path("accounts/signup/", CustomSignupView.as_view(), name="account_signup"),
    # Registro exitoso (con prefijos de país)
    path("auth/registro-exitoso/", registro_exitoso, name="registro_exitoso"),
    path("cl/auth/registro-exitoso/", registro_exitoso, name="registro_exitoso_cl"),
    path("us/auth/registro-exitoso/", registro_exitoso, name="registro_exitoso_us"),
    # Allauth para el resto de funcionalidades (excluyendo signup que ya está arriba)
    path("accounts/", include("allauth.urls")),
    # Wrappers country-aware para login y signup
    path("cl/accounts/login/", redirect_qs("/accounts/login/")),
    path("us/accounts/login/", redirect_qs("/accounts/login/")),
    path("cl/accounts/signup/", redirect_qs("/accounts/signup/")),
    path("us/accounts/signup/", redirect_qs("/accounts/signup/")),
    # Redirects amigables para login
    path("cl/login/", redirect_qs("/cl/accounts/login/")),
    path("cl/es/login/", redirect_qs("/cl/accounts/login/")),
    path("us/login/", redirect_qs("/us/accounts/login/")),
    # Logout
    path("cl/accounts/logout/", redirect_qs("/accounts/logout/")),
    path("us/accounts/logout/", redirect_qs("/accounts/logout/")),
    # Password reset (solicitud + enviado + confirm + completo)
    path("cl/accounts/password/reset/", redirect_qs("/accounts/password/reset/")),
    path("us/accounts/password/reset/", redirect_qs("/accounts/password/reset/")),
    path(
        "cl/accounts/password/reset/done/",
        redirect_qs("/accounts/password/reset/done/"),
    ),
    path(
        "us/accounts/password/reset/done/",
        redirect_qs("/accounts/password/reset/done/"),
    ),
    path(
        "cl/accounts/password/reset/key/<uidb36>/<key>/",
        redirect_qs("/accounts/password/reset/key/{uidb36}/{key}/"),
    ),
    path(
        "us/accounts/password/reset/key/<uidb36>/<key>/",
        redirect_qs("/accounts/password/reset/key/{uidb36}/{key}/"),
    ),
    path(
        "cl/accounts/password/reset/key/done/",
        redirect_qs("/accounts/password/reset/key/done/"),
    ),
    path(
        "us/accounts/password/reset/key/done/",
        redirect_qs("/accounts/password/reset/key/done/"),
    ),
    # Password change
    path("cl/accounts/password/change/", redirect_qs("/accounts/password/change/")),
    path("us/accounts/password/change/", redirect_qs("/accounts/password/change/")),
    path(
        "cl/accounts/password/change/done/",
        redirect_qs("/accounts/password/change/done/"),
    ),
    path(
        "us/accounts/password/change/done/",
        redirect_qs("/accounts/password/change/done/"),
    ),
    path("i18n/", include("django.conf.urls.i18n")),  # Selector de idioma
    path(
        "jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"
    ),  # 👈 Catálogo JS para gettext
    # Cambio de idioma para USA
    path("lang/set/", set_language_us, name="set_language_us"),
    path(
        "changelog/",
        TemplateView.as_view(template_name="changelog.html"),
        name="changelog",
    ),
    path(
        "legal/",
        TemplateView.as_view(template_name="legal.html"),
        name="legal",
    ),
    # 🇦🇷 Argentina (usa rutas tipo Chile)
    path(
        "ar/",
        include(("taller.urls_extra.argentina", "argentina"), namespace="argentina"),
    ),
    # 🇺🇾 Uruguay (usa rutas tipo Chile)
    path(
        "uy/",
        include(("taller.urls_extra.uruguay", "uruguay"), namespace="uruguay"),
    ),
    # 🇺🇸 USA - Unificado (inglés y español)
    path(
        "us/",
        include(("taller.urls_extra.usa", "usa"), namespace="usa"),
    ),
    # 🇺🇸 USA - Inglés específico
    path(
        "us/en/",
        include(("taller.urls_extra.usa", "usa"), namespace="usa_en"),
    ),
    # 🇺🇸 USA - Español específico
    path(
        "us/es/",
        include(("taller.urls_extra.usa", "usa"), namespace="usa_es"),
    ),
    # 🇨🇱 Chile - Español
    path(
        "cl/es/",
        include(("taller.urls_extra.chile", "chile"), namespace="chile"),
    ),
    # 🇵🇪 Perú - Español
    path(
        "pe/es/",
        include(("taller.urls_extra.peru", "peru"), namespace="peru"),
    ),
    # 🇨🇴 Colombia - Español
    path(
        "co/es/",
        include(("taller.urls_extra.colombia", "colombia"), namespace="colombia"),
    ),
    # 🇪🇨 Ecuador - Español
    path(
        "ec/es/",
        include(("taller.urls_extra.ecuador", "ecuador"), namespace="ecuador"),
    ),
    # 🇻🇪 Venezuela - Español
    path(
        "ve/es/",
        include(("taller.urls_extra.venezuela", "venezuela"), namespace="venezuela"),
    ),
    # 🇲🇽 México - Español
    path(
        "mx/es/",
        include(("taller.urls_extra.mexico", "mexico"), namespace="mexico"),
    ),
    # 🇧🇷 Brasil - Español (puede cambiar a pt-br en el futuro)
    path(
        "br/es/",
        include(("taller.urls_extra.brasil", "brasil"), namespace="brasil"),
    ),
    # 🇦🇷 Argentina - Español
    path(
        "ar/es/",
        include(("taller.urls_extra.argentina", "argentina"), namespace="argentina_es"),
    ),
    # 🇺🇾 Uruguay - Español
    path(
        "uy/es/",
        include(("taller.urls_extra.uruguay", "uruguay"), namespace="uruguay_es"),
    ),
    # Chile - Specific routes before general redirect
    path(
        "cl/vehiculos/",
        RedirectView.as_view(url="/cl/es/vehiculos/", permanent=False),
        name="cl_vehiculos_redirect",
    ),
    # USA - Specific routes before general redirect
    path(
        "us/vehiculos/",
        RedirectView.as_view(url="/us/en/vehiculos/", permanent=False),
        name="us_vehiculos_redirect",
    ),
    path(
        "us/vehiculos/<int:pk>/",
        RedirectView.as_view(url="/us/en/vehiculos/%(pk)s/", permanent=False),
        name="us_vehiculo_detail_redirect",
    ),
    path(
        "us/vehiculos/crear/",
        RedirectView.as_view(url="/us/en/vehiculos/crear/", permanent=False),
        name="us_vehiculo_create_redirect",
    ),
    path(
        "us/vehiculos/<int:vehiculo_id>/editar/",
        RedirectView.as_view(url="/us/en/vehiculos/%(vehiculo_id)s/editar/", permanent=False),
        name="us_vehiculo_edit_redirect",
    ),
    path(
        "us/vehiculos/<int:vehiculo_id>/eliminar/",
        RedirectView.as_view(url="/us/en/vehiculos/%(vehiculo_id)s/eliminar/", permanent=False),
        name="us_vehiculo_eliminar_redirect",
    ),
    path(
        "cl/vehiculos/<int:pk>/",
        RedirectView.as_view(url="/cl/es/vehiculos/%(pk)s/", permanent=False),
        name="cl_vehiculo_detail_redirect",
    ),
    path(
        "cl/vehiculos/crear/",
        RedirectView.as_view(url="/cl/es/vehiculos/crear/", permanent=False),
        name="cl_vehiculo_create_redirect",
    ),
    path(
        "cl/vehiculos/<int:vehiculo_id>/editar/",
        RedirectView.as_view(url="/cl/es/vehiculos/%(vehiculo_id)s/editar/", permanent=False),
        name="cl_vehiculo_edit_redirect",
    ),
    path(
        "cl/clientes/",
        country_aware_clientes_redirect,
        name="cl_clientes_redirect",
    ),
    path(
        "cl/servicios/",
        RedirectView.as_view(url="/cl/es/servicios/", permanent=False),
        name="cl_servicios_redirect",
    ),
    path(
        "cl/configuracion/",
        RedirectView.as_view(url="/cl/es/configuracion/", permanent=False),
        name="cl_configuracion_redirect",
    ),
    path(
        "cl/centro-operaciones-espacial/",
        RedirectView.as_view(url="/cl/es/centro-operaciones-espacial/", permanent=False),
        name="cl_centro_operaciones_redirect",
    ),
    # Redirigir /cl/ a /cl/es/bienvenida/
    path(
        "cl/",
        RedirectView.as_view(url="/cl/es/bienvenida/", permanent=False),
        name="cl_home_welcome",
    ),
    # Página de bienvenida para Argentina - /ar/ directamente
    path(
        "ar/",
        TemplateView.as_view(template_name="landing_inicio.html"),
        name="ar_home_welcome",
    ),
    # Página de bienvenida para Uruguay - /uy/ directamente
    path(
        "uy/",
        TemplateView.as_view(template_name="landing_inicio.html"),
        name="uy_home_welcome",
    ),
    # Redirect cl/ to cl/es/ preserving the rest of the path - DESHABILITADO - Causa bucles infinitos
    # path(
    #     "cl/",
    #     redirect_cl_to_es,
    #     name="cl_redirect",
    # ),
    # Redirect cl/anything to cl/es/anything preserving the rest of the path - DESHABILITADO - Causa bucles infinitos
    # path(
    #     "cl/<path:path>",
    #     redirect_cl_to_es,
    #     name="cl_redirect_with_path",
    # ),
    # Si agregas más combinaciones, repite este patrón: un solo include por prefijo.
    # path("taller/", include(("taller.urls", "taller"), namespace="taller")),  # ELIMINADO: URLs sin prefijo de país
    # Compatibilidad: reexponer namespace 'taller' para widgets antiguos (DAL, etc.)
    path(
        "compat/",
        include(("taller.urls", "taller"), namespace="taller"),
    ),
    # APIs globales (sin prefijo de país)
    path("api/v1/", include("taller.api.urls")),
    # API de ubicaciones (multi-país)
    path("api/", include(("ubicacion.urls", "ubicacion"), namespace="ubicacion")),
    # Marketplace - APIs para consulta de precios
    path("marketplace/", include(("marketplace.urls", "marketplace"), namespace="marketplace")),
    # WhatsApp - eGarage Air
    path("whatsapp/", include(("whatsapp.urls", "whatsapp"), namespace="whatsapp")),
    # URLs públicas para acceso de clientes (sin autenticación, protegidas por UUID)
    path(
        "publico/",
        include(("taller.urls_modules.publico_urls", "publico"), namespace="publico"),
    ),
    # Redirección de documentos sin país a Chile por defecto
    path(
        "documentos/",
        RedirectView.as_view(url="/cl/documentos/", permanent=False),
        name="documentos_redirect_root",
    ),
    # Redirecciones de compatibilidad para URLs antiguas con patrón duplicado
    path("cl/documentos/cl/", RedirectView.as_view(url="/cl/documentos/", permanent=True)),
    path("us/documentos/us/", RedirectView.as_view(url="/us/documentos/", permanent=True)),
    # Redirect de /cl/es/documentos/ a /cl/documentos/ (consistencia con otras rutas)
    path(
        "cl/es/documentos/",
        RedirectView.as_view(url="/cl/documentos/", permanent=False),
        name="cl_es_documentos_redirect",
    ),
    path(
        "cl/es/documentos/<path:path>",
        RedirectView.as_view(url="/cl/documentos/%(path)s", permanent=False),
        name="cl_es_documentos_path_redirect",
    ),
    # URLs con prefijo de país específico - NAMESPACES ÚNICOS
    path(
        "cl/documentos/",
        include(("taller.documentos.urls", "documentos_cl_es"), namespace="documentos_cl_es"),
    ),
    path(
        "us/documentos/",
        include(("taller.documentos.urls", "documentos_us_en"), namespace="documentos_us_en"),
    ),
    # Autocomplete URLs por país
    path(
        "cl/autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="cl_autocomplete"),
    ),
    path(
        "us/autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="usa_autocomplete"),
    ),
    path(
        "cl/reportes/",
        include(("taller.reportes.urls", "reportes_cl_es"), namespace="reportes_cl_es"),
    ),
    path(
        "us/reportes/",
        include(("taller.reportes.urls", "reportes_us_en"), namespace="reportes_us_en"),
    ),
    path(
        "ar/documentos/",
        include(("taller.documentos.urls", "documentos_ar_es"), namespace="documentos_ar_es"),
    ),
    path(
        "uy/documentos/",
        include(("taller.documentos.urls", "documentos_uy_es"), namespace="documentos_uy_es"),
    ),
    # Autocomplete URLs por país
    path(
        "ar/autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="ar_autocomplete"),
    ),
    path(
        "uy/autocomplete/",
        include(("taller.autocomplete.urls", "autocomplete"), namespace="uy_autocomplete"),
    ),
    path(
        "ar/reportes/",
        include(("taller.reportes.urls", "reportes_ar_es"), namespace="reportes_ar_es"),
    ),
    path(
        "uy/reportes/",
        include(("taller.reportes.urls", "reportes_uy_es"), namespace="reportes_uy_es"),
    ),
    # Ruta de seguridad para /login/ global
    path("login/", login_redirector, name="login_redirector"),
    # Vista personalizada de logout redirect
    path("logout-redirect/", logout_redirect_view, name="logout_redirect"),
    # Redirect para compatibilidad con URLs antiguas de vehiculos
    path(
        "taller/vehiculos/",
        RedirectView.as_view(url="/cl/vehiculos/", permanent=False),
        name="vehiculos_redirect_legacy",
    ),
    # Redirect específico para eliminación de vehículos
    path(
        "taller/vehiculos/<int:pk>/eliminar/",
        RedirectView.as_view(url="/cl/es/vehiculos/%(pk)s/eliminar/", permanent=False),
        name="vehiculo_eliminar_redirect_legacy",
    ),
    # Redirect para URLs antiguas de taller/settings
    path(
        "taller/settings/",
        RedirectView.as_view(url="/cl/configuracion/", permanent=False),
        name="taller_settings_redirect_legacy",
    ),
    # Redirect para URLs antiguas de taller/centro-operaciones-espacial
    path(
        "taller/centro-operaciones-espacial/",
        RedirectView.as_view(url="/cl/centro-operaciones-espacial/", permanent=False),
        name="centro_operaciones_espacial_redirect_legacy",
    ),
    # Redirect para URLs antiguas de common/centro-operaciones-espacial
    path(
        "common/centro-operaciones-espacial/",
        RedirectView.as_view(url="/cl/centro-operaciones-espacial/", permanent=False),
        name="common_centro_operaciones_espacial_redirect_legacy",
    ),
    # Redirect específico para USA
    path(
        "us/taller/settings/",
        RedirectView.as_view(url="/us/configuracion/", permanent=False),
        name="usa_taller_settings_redirect",
    ),
    # Diagnóstico temporal (REMOVER EN PRODUCCIÓN)
    # path("debug/branding/", include("taller.views_extra.debug_urls")),  # ❌ Desactivado - módulo no existe
    # Suscripción bloqueada - disponible globalmente
    path("suscripcion-bloqueada/", suscripcion_bloqueada, name="suscripcion_bloqueada"),
    # === REDIRECCIONES PARA ENDPOINTS AJAX HARDCODEADOS ===
    # Plan B: redirecciones suaves para cualquier hardcode viejo
    path(
        "cl/ajax/clientes/buscar/",
        RedirectView.as_view(url="/cl/es/ajax/clientes/buscar/", permanent=False),
    ),
    path(
        "cl/ajax/vehiculos-por-cliente/",
        RedirectView.as_view(url="/cl/es/ajax/vehiculos-por-cliente/", permanent=False),
    ),
    path(
        "cl/repuestos/api/repuesto-por-codigo/",
        RedirectView.as_view(url="/cl/es/repuestos/api/repuesto-por-codigo/", permanent=False),
    ),
    path(
        "cl/documentos/api/obtener-numero-documento/",
        RedirectView.as_view(
            url="/cl/es/documentos/api/obtener-numero-documento/", permanent=False
        ),
    ),
    # Redirecciones para USA (si las necesitas)
    path(
        "us/ajax/clientes/buscar/",
        RedirectView.as_view(url="/us/en/ajax/clientes/buscar/", permanent=False),
    ),
    path(
        "us/ajax/vehiculos-por-cliente/",
        RedirectView.as_view(url="/us/en/ajax/vehiculos-por-cliente/", permanent=False),
    ),
    path(
        "us/repuestos/api/repuesto-por-codigo/",
        RedirectView.as_view(url="/us/en/repuestos/api/repuesto-por-codigo/", permanent=False),
    ),
    path(
        "us/documentos/api/obtener-numero-documento/",
        RedirectView.as_view(
            url="/us/en/documentos/api/obtener-numero-documento/", permanent=False
        ),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    """Redirige registro al nivel global (alias para signup)"""
