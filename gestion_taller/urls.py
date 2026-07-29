from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import login as auth_login, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

# Sobrescribir el login del admin para que NO use allauth
# Usar directamente LoginView de Django
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.backends import ModelBackend


class AdminAuthenticationForm(AuthenticationForm):
    """Formulario de autenticación para admin que permite login por username o email"""

    username = forms.CharField(
        label="Usuario o Email",
        widget=forms.TextInput(attrs={"autofocus": True, "class": "form-control"}),
    )


class AdminLoginView(DjangoLoginView):
    """Login view personalizado para el admin que NO usa allauth"""

    template_name = "admin/login.html"
    authentication_form = AdminAuthenticationForm

    def form_valid(self, form):
        """Si el login es exitoso, redirigir al admin index"""
        # Usar el backend que autenticó al usuario (puede ser ModelBackend o EmailOrPhoneBackend)
        user = form.get_user()
        # Si el usuario no tiene backend asignado, usar ModelBackend como fallback
        if not hasattr(user, "backend") or not user.backend:
            from django.contrib.auth.backends import ModelBackend

            backend = ModelBackend()
            user.backend = f"{backend.__class__.__module__}.{backend.__class__.__name__}"
        auth_login(self.request, user)

        next_url = (
            self.request.GET.get("next") or self.request.POST.get("next") or reverse("admin:index")
        )
        return redirect(next_url)

    def dispatch(self, request, *args, **kwargs):
        """Si ya está autenticado y es staff, redirigir al index"""
        if request.user.is_authenticated and request.user.is_staff:
            return redirect(reverse("admin:index"))
        return super().dispatch(request, *args, **kwargs)


# Crear el método login que llama a la vista
_admin_login_view = AdminLoginView.as_view()


def admin_login_method(request, extra_context=None):
    """Método login del admin que llama a la vista personalizada"""
    context = extra_context or {}
    return _admin_login_view(request, extra_context=context)


# Asignar el método de login personalizado al admin
admin.site.login = admin_login_method
admin.site.login_template = "admin/login.html"

from django.http import HttpResponseNotFound
from django.urls import include, path, re_path
from django.views.generic import RedirectView, TemplateView
from django.views.i18n import JavaScriptCatalog  # 👈 Para catálogo JS

from taller.views.country_aware_auth import country_aware_login
from taller.views_extra.custom_signup import CustomSignupView
from taller.views_extra.lang_switch import set_language_us
from taller.views_extra.bienvenida_usa import bienvenida_usa_en, bienvenida_usa_es
from taller.views_extra.login_redirector import login_redirector
from taller.views_extra.logout_redirect_view import logout_redirect_view
from taller.views_extra.registro_exitoso import registro_exitoso
from taller.views_extra.signup_email_verification import (
    confirm_email_and_login,
    resend_signup_confirmation,
)
from taller.views_extra.signup_redirects import signup_redirect
from taller.views_extra.pwa import dynamic_manifest, dynamic_service_worker
from taller.views_health import health_check, health_simple, healthz

try:
    from taller.views_extra.compat_redirects import compat_settings_redirect
except ModuleNotFoundError:
    # Fallback si el módulo no está desplegado (ej. deploy incompleto)
    def compat_settings_redirect(request):
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect("/cl/es/settings/#financial")


# Importar vista de suscripción bloqueada
from taller.views_extra.suscripcion import registro, suscripcion_bloqueada
from taller.views_extra.admin_suscriptores import (
    admin_suscriptores,
    actualizar_telefono_ajax,
    cambiar_plan_ajax,
    desactivar_suscripcion_ajax,
    detalle_suscriptor,
    eliminar_suscriptor_ajax,
    extender_suscripcion_ajax,
)

# Forzar importación del admin de WhatsApp (app top-level whatsapp) solo si está desplegado
# Evita el warning "No se pudieron importar los modelos de WhatsApp" cuando la app no existe en el servidor
try:
    import whatsapp.models  # noqa: F401 — comprobar que la app completa existe
    import whatsapp.admin  # noqa: F401
except (ImportError, ModuleNotFoundError):
    pass

# Importar vistas de trial
from taller.views_extra.views_trial import registro_trial
from taller.views_extra.views_trial_activate import activar_trial
from taller.views_extra.views_suscripciones import (
    precios,
    subir_comprobante,
    suspension,
)
from taller.views.landing_views import landing_workshop, landing_salvage, landing_parts

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
        params.pop("country", None)  # país en path, no en GET
        # Si hay kwargs (por ejemplo, uidb36, key), formatear la URL
        url = to.format(**kwargs) if kwargs else to
        if params:
            url = f"{url}?{urlencode(params, doseq=True)}"
        return redirect(url)

    return view


def redirect_login_canonical(cc: str, lang: str):
    """Redirige rutas legacy de login a la ruta canónica por país/idioma."""

    def view(request, **kwargs):
        params = request.GET.copy()
        params.pop("country", None)
        url = f"/{cc}/{lang}/accounts/login/"
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


def country_aware_workspace_redirect(request, subpath=""):
    """Redirect /workspace/ to country workspace. USA → /us/en/workspace/, Chile → /cl/es/workspace/."""
    if request.user.is_authenticated:
        try:
            if hasattr(request.user, "empresa") and request.user.empresa:
                pais = (getattr(request.user.empresa, "pais", None) or "").strip().upper()
                if pais == "US":
                    return redirect(f"/us/en/workspace/{subpath}".rstrip("/") + "/")
                if pais == "CL":
                    return redirect(f"/cl/es/workspace/{subpath}".rstrip("/") + "/")
        except Exception:
            pass
    return redirect(f"/cl/es/workspace/{subpath}".rstrip("/") + "/")


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    # Storefront público individual por empresa
    path("tienda/", include(("taller.urls_public", "tienda"), namespace="tienda")),
    # Payment URLs globales (sin namespace para compatibilidad con templates)
    path("", include("taller.urls_payment")),
    # PWA Dinámicas (manifest y service worker por país e idioma)
    path("<str:pais>/<str:idioma>/manifest.json", dynamic_manifest, name="pwa_manifest"),
    path(
        "<str:pais>/<str:idioma>/service-worker.js",
        dynamic_service_worker,
        name="pwa_service_worker",
    ),
    # Root /workspace/ → country-aware redirect (early so it's always found)
    path("workspace/", country_aware_workspace_redirect, name="workspace_redirect_root"),
    path(
        "workspace/buscar/",
        lambda r: country_aware_workspace_redirect(r, "buscar"),
        name="workspace_buscar_redirect_root",
    ),
    path("clientes/", include(("taller.urls_clientes", "clientes"), namespace="clientes")),
    # Portal del Cliente
    path("portal/", include("taller.portal.urls")),
    # Página de inicio - Selección de país
    path("", TemplateView.as_view(template_name="landing/seleccionar_pais.html"), name="home"),
    # Landings de productos (sin prefijo de país)
    path("workshop/", landing_workshop, name="landing_workshop"),
    path("salvage/", landing_salvage, name="landing_salvage"),
    path("parts/", landing_parts, name="landing_parts"),
    # Panel de administración de suscriptores (ANTES de admin.site.urls para que no sea capturado)
    path("cl/admin/subcriptores/", include("taller.urls_admin_suscriptores")),
    path("admin/suscriptores/", admin_suscriptores, name="admin_suscriptores"),
    path(
        "admin/suscriptores/<int:empresa_id>/", detalle_suscriptor, name="admin_detalle_suscriptor"
    ),
    path(
        "admin/suscriptores/<int:empresa_id>/extender/",
        extender_suscripcion_ajax,
        name="admin_extender_suscripcion",
    ),
    path(
        "admin/suscriptores/<int:empresa_id>/cambiar-plan/",
        cambiar_plan_ajax,
        name="admin_cambiar_plan",
    ),
    path(
        "admin/suscriptores/<int:empresa_id>/desactivar/",
        desactivar_suscripcion_ajax,
        name="admin_desactivar_suscripcion",
    ),
    path(
        "admin/suscriptores/<int:empresa_id>/eliminar/",
        eliminar_suscriptor_ajax,
        name="admin_eliminar_suscriptor",
    ),
    path(
        "admin/suscriptores/<int:empresa_id>/actualizar-telefono/",
        actualizar_telefono_ajax,
        name="admin_actualizar_telefono",
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
    # Suspensión por suscripción vencida (bloqueo desde middleware)
    path("suspension/", suspension, name="suspension"),
    path("comprobante-pago/", subir_comprobante, name="subir_comprobante"),
    path("precios/", precios, name="precios"),
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
    # Reenvio de confirmacion despues del signup (sin autenticar usuario)
    path(
        "accounts/resend-confirmation/",
        resend_signup_confirmation,
        name="account_resend_signup_confirmation",
    ),
    path(
        "accounts/confirm-email/<str:key>/",
        confirm_email_and_login,
        name="account_confirm_email_country_aware",
    ),
    # Registro exitoso (con prefijos de país)
    path("auth/registro-exitoso/", registro_exitoso, name="registro_exitoso"),
    path("cl/auth/registro-exitoso/", registro_exitoso, name="registro_exitoso_cl"),
    path("us/auth/registro-exitoso/", registro_exitoso, name="registro_exitoso_us"),
    # Allauth para el resto de funcionalidades (excluyendo signup que ya está arriba)
    path("accounts/", include("allauth.urls")),
    # Confirmacion country-aware -> canonical allauth global.
    path(
        "cl/es/accounts/confirm-email/<str:key>/",
        redirect_qs("/accounts/confirm-email/{key}/"),
        name="account_confirm_email_cl_es",
    ),
    # Wrappers country-aware para login y signup
    # Canonicalizamos Chile a /cl/es/accounts/login/ para evitar CSRF por mismatch de URL.
    path("cl/accounts/login/", redirect_login_canonical("cl", "es"), name="account_login_cl"),
    path("co/accounts/login/", country_aware_login, name="account_login_co"),
    path("ec/accounts/login/", country_aware_login, name="account_login_ec"),
    path("pe/accounts/login/", country_aware_login, name="account_login_pe"),
    # Signup CL y US - redirect a signup country-aware con país + idioma
    path("cl/accounts/signup/", lambda r: signup_redirect(r, "cl"), name="account_signup_cl"),
    # Redirecciones /xx/signup/ -> /{xx}/{lang}/accounts/signup/ (preserva ?plan=, etc.) para que los
    # enlaces de onboarding/bienvenida (ej. /cl/signup/, /ar/signup/) resuelvan en todos los países
    path(
        "cl/signup/",
        lambda r: redirect("/cl/es/accounts/signup/" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="signup_redirect_cl",
    ),
    path(
        "ar/signup/",
        lambda r: redirect("/ar/es/accounts/signup/" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="signup_redirect_ar",
    ),
    path(
        "ec/signup/",
        lambda r: redirect("/ec/es/accounts/signup/" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="signup_redirect_ec",
    ),
    path(
        "co/signup/",
        lambda r: redirect("/co/es/accounts/signup/" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="signup_redirect_co",
    ),
    path(
        "pe/signup/",
        lambda r: redirect("/pe/es/accounts/signup/" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="signup_redirect_pe",
    ),
    path(
        "ve/signup/",
        lambda r: redirect("/ve/es/accounts/signup/" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="signup_redirect_ve",
    ),
    path(
        "br/signup/",
        lambda r: redirect("/br/es/accounts/signup/" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="signup_redirect_br",
    ),
    # Redirects amigables para login (siempre llevar a login canónico con idioma)
    path("cl/login/", redirect_login_canonical("cl", "es")),
    path("cl/es/login/", redirect_login_canonical("cl", "es")),
    # us/login/ lo resuelve path("us/", include(usa)) → usa_login_view (render directo)
    path("co/login/", redirect_qs("/co/accounts/login/")),
    path("co/es/login/", redirect_qs("/co/accounts/login/")),
    path("ec/login/", redirect_qs("/ec/accounts/login/")),
    path("ec/es/login/", redirect_qs("/ec/accounts/login/")),
    path("pe/login/", redirect_qs("/pe/accounts/login/"), name="pe_login_redirect"),
    path("pe/es/login/", redirect_qs("/pe/accounts/login/"), name="pe_es_login_redirect"),
    path("ve/login/", redirect_qs("/ve/es/accounts/login/")),
    path("ve/es/login/", redirect_qs("/ve/es/accounts/login/")),
    # Logout
    path("cl/accounts/logout/", redirect_qs("/accounts/logout/")),
    # Password reset (solicitud + enviado + confirm + completo)
    # Chile: rutas reales en taller.urls_extra.chile bajo /cl/es/accounts/password/* (no redirect a /accounts/).
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
    # 🇺🇾 Uruguay - Español (antes de /uy/ para resolver /uy/es/... sin depender del orden de prueba)
    path(
        "uy/es/",
        include(("taller.urls_extra.uruguay", "uruguay"), namespace="uruguay_es"),
    ),
    # 🇺🇾 Uruguay (usa rutas tipo Chile)
    path(
        "uy/",
        include(("taller.urls_extra.uruguay", "uruguay"), namespace="uruguay"),
    ),
    # 🇺🇸 USA - /us/en/accounts/* y /us/es/accounts/* redirigen al namespace usa
    path("us/en/accounts/", lambda r: redirect("/us/accounts/" + ("?" + r.GET.urlencode() if r.GET else ""))),
    path("us/en/accounts/<path:rest>", lambda r, rest: redirect(f"/us/accounts/{rest}")),
    path("us/es/accounts/", lambda r: redirect("/us/accounts/" + ("?" + r.GET.urlencode() if r.GET else ""))),
    path("us/es/accounts/<path:rest>", lambda r, rest: redirect(f"/us/accounts/{rest}")),
    # 🇺🇸 USA - Bienvenida explícita ANTES de us/en/ y us/es/ (evita 502: taller.urls no tiene bienvenida/)
    path("us/en/bienvenida/", bienvenida_usa_en, name="us_en_bienvenida"),
    path("us/es/bienvenida/", bienvenida_usa_es, name="us_es_bienvenida"),
    # 🇺🇸 USA - Redirect /us/centro-operaciones/ → /us/en/centro-operaciones/ (evita ERR_TOO_MANY_REDIRECTS)
    path(
        "us/centro-operaciones/",
        RedirectView.as_view(url="/us/en/centro-operaciones/", permanent=False),
        name="us_centro_operaciones_redirect",
    ),
    # Root /workspace/ is registered at the top of urlpatterns
    # 🇺🇸 USA - /us/workspace/ → /us/en/workspace/ (canonical con idioma; evita loop con SimpleCountryRedirectMiddleware)
    path(
        "us/workspace/",
        RedirectView.as_view(url="/us/en/workspace/", permanent=False),
        name="us_workspace_redirect",
    ),
    path(
        "us/workspace/buscar/",
        RedirectView.as_view(url="/us/en/workspace/buscar/", permanent=False),
        name="us_workspace_buscar_redirect",
    ),
    # 🇺🇸 USA - Desarme explícito para /us/en/desarme/ (ANTES se montaba con namespace us_en_desarme,
    # lo que rompe helpers que esperan us_en:desarme:...; ahora se deja solo el include normal en
    # `taller.urls` bajo el namespace us_en)
    # path(
    #     "us/en/desarme/",
    #     include(("taller.urls_desarme", "desarme"), namespace="us_en_desarme"),
    # ),
    # 🇺🇸 USA - Montes reales para /us/en/ y /us/es/ (ANTES de us/ y de RedirectViews)
    path(
        "us/en/",
        include(("taller.urls", "taller"), namespace="us_en"),
    ),
    path(
        "us/es/",
        include(("taller.urls", "taller"), namespace="us_es"),
    ),
    # 🇺🇸 USA - Unificado (contiene rutas raíz /us/ sin prefijo de idioma)
    path(
        "us/",
        include(("taller.urls_extra.usa", "usa"), namespace="usa"),
    ),
    # 🇨🇱 Chile - Español (settings resuelve vía include: chile:company_settings → /cl/es/settings/)
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
    # 🇧🇷 Brasil - Portugués (SOLO pt, /br/es/ redirige a /br/pt/)
    path(
        "br/",
        include(("taller.urls_extra.brasil", "brasil"), namespace="brasil"),
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
        "us/tecnicos/crear/",
        RedirectView.as_view(url="/us/tecnicos/nuevo/", permanent=False),
        name="us_tecnico_create_redirect",
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
        "cl/precios/",
        RedirectView.as_view(url="/cl/es/precios/", permanent=False),
        name="cl_precios_redirect",
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
    # Compatibilidad: /compat/settings/ → redirect limpio a /cl/es/settings/#financial
    # (evita que el middleware de país mande al login; ruta específica ANTES del include)
    path("compat/settings/", compat_settings_redirect, name="compat_settings_redirect"),
    # Compatibilidad: reexponer namespace 'taller' para widgets antiguos (DAL, etc.)
    path(
        "compat/",
        include(("taller.urls", "taller"), namespace="taller_compat"),
    ),
    # Analytics global (sin prefijo de país)
    path("analytics/", include(("taller.analytics.urls", "analytics"), namespace="analytics")),
    # APIs globales (sin prefijo de país)
    path(
        "api/v1/",
        include(("taller.api.urls", "api"), namespace="api_v1"),
    ),
    path(
        "<str:pais>/api/",
        include(("taller.api.urls", "api"), namespace="api"),
    ),
    # API de ubicaciones (multi-país)
    path("api/", include(("ubicacion.urls", "ubicacion"), namespace="ubicacion")),
    # Marketplace - APIs para consulta de precios
    # Habilitado mediante feature flag EGARAGE_ENABLE_MARKETPLACE
    # WhatsApp - eGarage Air
    # Comentado temporalmente si el módulo no existe en el servidor
    # path("whatsapp/", include(("whatsapp.urls", "whatsapp"), namespace="whatsapp")),
    # URLs públicas para acceso de clientes (sin autenticación, protegidas por UUID)
    # Comentado temporalmente si el módulo no existe en el servidor
    # path(
    #     "publico/",
    #     include(("taller.urls_extra.publico_urls", "publico"), namespace="publico"),
    # ),
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
        RedirectView.as_view(url="/cl/es/settings/", permanent=False),
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
        "cl/documentos/ajax/clientes/buscar/",
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
    path("", include(("taller.taller_main_urls", "taller"), namespace="taller")),
]

# Marketplace: solo se agregan URLs si el módulo existe (evita ModuleNotFoundError en servidor)
if getattr(settings, "EGARAGE_ENABLE_MARKETPLACE", False):
    try:
        urlpatterns += [
            path(
                "marketplace/",
                include(("marketplace.urls", "marketplace"), namespace="marketplace"),
            ),
        ]
    except (ImportError, ModuleNotFoundError):
        pass

# 🇦🇷 Argentina - URLs protegidas con try/except para que un error no tumbe toda la app
try:
    urlpatterns += [
        path(
            "ar/",
            include(("taller.urls_extra.argentina", "argentina"), namespace="argentina"),
        ),
        path(
            "ar/es/",
            include(("taller.urls_extra.argentina", "argentina"), namespace="argentina_es"),
        ),
    ]
except Exception as e:
    import logging

    logger = logging.getLogger(__name__)
    logger.error(f"Error al cargar URLs de Argentina: {e}", exc_info=True)
    # Continuar sin las URLs de Argentina para que el resto de la app funcione
    pass

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    """Redirige registro al nivel global (alias para signup)"""
