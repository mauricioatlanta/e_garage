from django.urls import path, include
from urllib.parse import urlencode
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView
from django.views.i18n import JavaScriptCatalog

from taller.views.country_aware_auth import country_aware_login
from taller.views_extra.signup_complete import signup_complete
from taller.views_extra.lang_switch import set_language_us
from taller.views_extra.payment_views import (
    payment_chile,
    payment_usa,
    subir_comprobante,
    payment_success,
    payment_cancel,
)
from taller.views_extra.paypal_webhook import paypal_webhook
from taller.views_extra.admin_payment_views import aprobar_pago, rechazar_pago
from taller.views_extra.login_redirector import login_redirector
from taller.views_extra.logout_redirect_view import logout_redirect_view
from taller.views_health import health_check, health_simple

# Importar vista de suscripción bloqueada
from taller.views_extra.suscripcion import registro, suscripcion_bloqueada

# Importar vistas de trial
from taller.views_extra.views_trial import registro_trial
from taller.views_extra.views_trial_activate import activar_trial


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
                elif request.user.empresa.pais == "BR":
                    return redirect("/br/")
                elif request.user.empresa.pais == "VE":
                    return redirect("/ve/")
                elif request.user.empresa.pais == "PE":
                    return redirect("/pe/")
        except Exception:
            pass

    # Si hay contexto de país en el request (desde middleware)
    if hasattr(request, "country"):
        if request.country == "CL":
            return redirect("/cl/")
        elif request.country == "US":
            return redirect("/us/")
        elif request.country == "BR":
            return redirect("/br/")
        elif request.country == "VE":
            return redirect("/ve/")
        elif request.country == "PE":
            return redirect("/pe/")

    # Fallback: redirigir al selector de país
    return redirect("/selector/")


def redirect_qs(to):
    def view(request, **kwargs):
        params = request.GET.copy()
        url = to.format(**kwargs) if kwargs else to
        if params:
            url = f"{url}?{urlencode(params, doseq=True)}"
        return redirect(url)

    return view


urlpatterns = [
    # ========================================================================
    # ADMIN
    # ========================================================================
    path("admin/", admin.site.urls),
    # ========================================================================
    # SELECTOR DE PAÍS (Página principal)
    # ========================================================================
    path("", TemplateView.as_view(template_name="public/selector_pais.html"), name="selector_pais"),
    path(
        "selector/",
        TemplateView.as_view(template_name="public/selector_pais.html"),
        name="selector_pais_explicit",
    ),
    # ========================================================================
    # 🇧🇷 BRASIL - Português
    # ========================================================================
    path(
        "br/",
        include(("taller.urls_extra.brasil", "brasil"), namespace="brasil"),
    ),
    path(
        "br/pt/",
        include(("taller.urls_extra.brasil", "brasil"), namespace="brasil_pt"),
    ),
    # ========================================================================
    # 🇻🇪 VENEZUELA - Español
    # ========================================================================
    path(
        "ve/",
        include(("taller.urls_extra.venezuela", "venezuela"), namespace="venezuela"),
    ),
    path(
        "ve/es/",
        include(("taller.urls_extra.venezuela", "venezuela"), namespace="venezuela_es"),
    ),
    # ========================================================================
    # 🇵🇪 PERÚ - Español
    # ========================================================================
    path(
        "pe/",
        include(("taller.urls_extra.peru", "peru"), namespace="peru"),
    ),
    path(
        "pe/es/",
        include(("taller.urls_extra.peru", "peru"), namespace="peru_es"),
    ),
    # ========================================================================
    # 🇺🇸 USA - English
    # ========================================================================
    path(
        "us/",
        include(("taller.urls_extra.usa", "usa"), namespace="usa"),
    ),
    path(
        "us/en/",
        include(("taller.urls_extra.usa", "usa"), namespace="usa_en"),
    ),
    # ========================================================================
    # 🇨🇱 CHILE - Español
    # ========================================================================
    path(
        "cl/",
        include(("taller.urls_extra.chile", "chile"), namespace="chile"),
    ),
    path(
        "cl/es/",
        include(("taller.urls_extra.chile", "chile"), namespace="chile_es"),
    ),
    # ========================================================================
    # API UNIFICADA DE UBICACIONES (multi-país)
    # ========================================================================
    path("api/", include(("taller.ubicacion.urls", "ubicacion_api"), namespace="ubicacion_api")),
    # ========================================================================
    # AUTENTICACIÓN GLOBAL
    # ========================================================================
    path("accounts/", include("allauth.urls")),
    path("accounts/signup/complete/", signup_complete, name="signup_complete"),
    # ========================================================================
    # PAGOS
    # ========================================================================
    path("payment/chile/", payment_chile, name="payment_chile"),
    path("payment/usa/", payment_usa, name="payment_usa"),
    path("payment/subir-comprobante/", subir_comprobante, name="subir_comprobante"),
    path("payment/success/", payment_success, name="payment_success"),
    path("payment/cancel/", payment_cancel, name="payment_cancel"),
    path("webhooks/paypal/", paypal_webhook, name="paypal_webhook"),
    path("admin/payment/aprobar/<int:pago_id>/", aprobar_pago, name="aprobar_pago"),
    path("admin/payment/rechazar/<int:pago_id>/", rechazar_pago, name="rechazar_pago"),
    # ========================================================================
    # UTILIDADES
    # ========================================================================
    path("health/", health_check, name="health_check"),
    path("health/simple/", health_simple, name="health_simple"),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("set-language-us/", set_language_us, name="set_language_us"),
    path("i18n/", include("django.conf.urls.i18n")),
    # ========================================================================
    # SUSCRIPCIÓN
    # ========================================================================
    path("registro/", registro, name="registro"),
    path("suscripcion-bloqueada/", suscripcion_bloqueada, name="suscripcion_bloqueada"),
    path("registro-trial/", registro_trial, name="registro_trial"),
    path("trial/activar/", activar_trial, name="activar_trial"),
    # ========================================================================
    # LOGIN/LOGOUT
    # ========================================================================
    path("login/", login_redirector, name="login_redirector"),
    path("logout/", logout_redirect_view, name="logout"),
]

# Archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Debug URLs (safe include)
try:
    import importlib

    importlib.import_module("taller.views_extra.debug_urls")
    from django.urls import include as _include, path as _path

    urlpatterns += [_path("debug/branding/", _include("taller.views_extra.debug_urls"))]
except Exception:
    pass
