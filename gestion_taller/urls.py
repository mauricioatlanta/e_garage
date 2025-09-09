from urllib.parse import urlencode

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView
from django.views.i18n import JavaScriptCatalog  # 👈 Para catálogo JS

from taller.views.country_aware_auth import country_aware_login
from taller.views_extra.login_redirector import login_redirector
from taller.views_extra.logout_redirect_view import logout_redirect_view

# Importar vista de suscripción bloqueada
from taller.views_extra.suscripcion import suscripcion_bloqueada

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
                if request.user.empresa.pais == "CL":
                    return redirect("/cl/")
                elif request.user.empresa.pais == "US":
                    return redirect("/us/")
        except Exception:
            pass

    # Si hay contexto de país en el request (desde middleware)
    if hasattr(request, "country"):
        if request.country == "CL":
            return redirect("/cl/")
        elif request.country == "US":
            return redirect("/us/")

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


urlpatterns = [
    # Página de inicio - redirige según el usuario
    path("", redirect_to_home, name="home"),
    path("admin/", admin.site.urls),
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
    # Allauth para el resto de funcionalidades
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
    path(
        "changelog/",
        TemplateView.as_view(template_name="changelog.html"),
        name="changelog",
    ),
    # 🇺🇸 USA - Inglés
    path(
        "us/en/",
        include(("taller.urls_extra.usa", "usa"), namespace="usa"),
    ),
    # 🇺🇸 USA - Español
    path(
        "us/es/",
        include(("taller.urls_extra.usa", "usa"), namespace="usa"),
    ),
    # Redirect us/ to us/en/
    path(
        "us/",
        RedirectView.as_view(url="/us/en/", permanent=False),
        name="us_redirect",
    ),
    # 🇨🇱 Chile - Español
    path(
        "cl/es/",
        include(("taller.urls_extra.chile", "chile"), namespace="chile"),
    ),
    # Página de bienvenida específica para /cl/egarage/
    path(
        "cl/egarage/",
        TemplateView.as_view(template_name="onboarding/bienvenida_chile_simple.html"),
        name="cl_egarage_bienvenida",
    ),
    # Redirect cl/ to cl/es/ preserving the rest of the path
    path(
        "cl/",
        redirect_cl_to_es,
        name="cl_redirect",
    ),
    # Redirect cl/anything to cl/es/anything preserving the rest of the path
    path(
        "cl/<path:path>",
        redirect_cl_to_es,
        name="cl_redirect_with_path",
    ),
    # Si agregas más combinaciones, repite este patrón: un solo include por prefijo.
    # path("taller/", include(("taller.urls", "taller"), namespace="taller")),  # ELIMINADO: URLs sin prefijo de país
    # APIs globales (sin prefijo de país)
    path("api/v1/", include("taller.api.urls")),
    # Redirección de documentos sin país a Chile por defecto
    path(
        "documentos/",
        RedirectView.as_view(url="/cl/documentos/", permanent=False),
        name="documentos_redirect_root",
    ),
    # Redirecciones de compatibilidad para URLs antiguas con patrón duplicado
    path(
        "cl/documentos/cl/", RedirectView.as_view(url="/cl/documentos/", permanent=True)
    ),
    path(
        "us/documentos/us/", RedirectView.as_view(url="/us/documentos/", permanent=True)
    ),
    # URLs con prefijo de país específico - NAMESPACES ÚNICOS
    path(
        "cl/documentos/",
        include(
            ("taller.documentos.urls", "documentos_cl_es"), namespace="documentos_cl_es"
        ),
    ),
    path(
        "us/documentos/",
        include(
            ("taller.documentos.urls", "documentos_us_en"), namespace="documentos_us_en"
        ),
    ),
    path(
        "cl/reportes/",
        include(("taller.reportes.urls", "reportes_cl_es"), namespace="reportes_cl_es"),
    ),
    path(
        "us/reportes/",
        include(("taller.reportes.urls", "reportes_us_en"), namespace="reportes_us_en"),
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
    # Redirect para URLs antiguas de taller/settings
    path(
        "taller/settings/",
        RedirectView.as_view(url="/cl/settings/", permanent=False),
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
        RedirectView.as_view(url="/us/settings/", permanent=False),
        name="usa_taller_settings_redirect",
    ),
    # Diagnóstico temporal (REMOVER EN PRODUCCIÓN)
    path("debug/branding/", include("taller.views_extra.debug_urls")),
    # Suscripción bloqueada - disponible globalmente
    path("suscripcion-bloqueada/", suscripcion_bloqueada, name="suscripcion_bloqueada"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    """Redirige registro al nivel global (alias para signup)"""
