"""
URLs específicas para Perú 🇵🇪
Patrón: /pe/es/ seguido de las rutas específicas
Usa TemplateView para no depender de vistas Python especiales
"""

from django.shortcuts import redirect
from django.urls import path
from django.views.generic import RedirectView, TemplateView
from taller.views.country_aware_auth import country_aware_login

from taller.views_extra.signup_redirects import signup_redirect

app_name = "taller_peru"

urlpatterns = [
    # Redirigir raíz a bienvenida
    path("", RedirectView.as_view(url="/pe/es/bienvenida/", permanent=False), name="peru_home"),
    # Dashboard principal de Perú
    path(
        "dashboard/",
        TemplateView.as_view(template_name="pe/es/dashboard/centro_operaciones_espacial.html"),
        name="dashboard_peru",
    ),
    # Página de bienvenida / onboarding Perú
    path(
        "bienvenida/",
        TemplateView.as_view(template_name="pe/es/onboarding/bienvenida.html"),
        name="bienvenida_peru",
    ),
    # Página de pago de suscripción Perú (cuando esté lista)
    path(
        "suscripcion/pago/",
        TemplateView.as_view(template_name="pe/es/suscripcion/pago.html"),
        name="pago_suscripcion_peru",
    ),
    path(
        "accounts/login/",
        country_aware_login,
        name="account_login",
    ),
    path(
        "login/",
        lambda r: redirect("/pe/es/accounts/login/" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="account_login_short",
    ),
    # Signup Perú - redirect a signup universal con parámetro from=pe
    path(
        "accounts/signup/",
        lambda r: signup_redirect(r, "pe"),
        name="account_signup",
    ),
    path(
        "signup/",
        lambda r: redirect("/pe/es/accounts/signup/" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="signup",
    ),
    # Redirect resto de accounts/* → /accounts/* (password reset, logout, etc.)
    path(
        "accounts/", lambda r: redirect("/accounts/" + ("?" + r.GET.urlencode() if r.GET else ""))
    ),
    path(
        "accounts/<path:rest>",
        lambda r, rest: redirect(
            "/accounts/" + rest.rstrip("/") + ("?" + r.GET.urlencode() if r.GET else "")
        ),
    ),
    # Lista de clientes Perú
    path(
        "clientes/",
        TemplateView.as_view(template_name="pe/es/clientes/lista_clientes.html"),
        name="lista_clientes_peru",
    ),
]
