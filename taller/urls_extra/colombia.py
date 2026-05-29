"""
URLs específicas para Colombia 🇨🇴
Patrón: /co/es/ seguido de las rutas específicas
Usa TemplateView para no depender de vistas Python especiales
"""

from django.shortcuts import redirect
from django.urls import path
from django.views.generic import RedirectView, TemplateView
from taller.views.country_aware_auth import country_aware_login

from taller.views_extra.signup_redirects import signup_redirect

app_name = "taller_colombia"

urlpatterns = [
    # Redirigir raíz a bienvenida
    path("", RedirectView.as_view(url="/co/es/bienvenida/", permanent=False), name="colombia_home"),
    # Dashboard principal de Colombia
    path(
        "dashboard/",
        TemplateView.as_view(template_name="co/es/dashboard/centro_operaciones_espacial.html"),
        name="dashboard_colombia",
    ),
    # Página de bienvenida / onboarding Colombia
    path(
        "bienvenida/",
        TemplateView.as_view(template_name="co/es/onboarding/bienvenida.html"),
        name="bienvenida_colombia",
    ),
    # Página de pago de suscripción Colombia (cuando esté lista)
    path(
        "suscripcion/pago/",
        TemplateView.as_view(template_name="co/es/suscripcion/pago.html"),
        name="pago_suscripcion_colombia",
    ),
    path(
        "accounts/login/",
        country_aware_login,
        name="account_login",
    ),
    path(
        "login/",
        lambda r: redirect("/co/es/accounts/login/" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="account_login_short",
    ),
    # Signup Colombia - redirect a signup universal con parámetro from=co
    path(
        "accounts/signup/",
        lambda r: signup_redirect(r, "co"),
        name="account_signup_colombia",
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
    # Lista de clientes Colombia
    path(
        "clientes/",
        TemplateView.as_view(template_name="co/es/clientes/lista_clientes.html"),
        name="lista_clientes_colombia",
    ),
]
