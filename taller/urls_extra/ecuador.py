"""
URLs específicas para Ecuador 🇪🇨
Patrón: /ec/es/ seguido de las rutas específicas
Usa TemplateView para no depender de vistas Python especiales
"""

from django.shortcuts import redirect
from django.urls import path
from django.views.generic import RedirectView, TemplateView

from taller.views_extra.signup_redirects import signup_redirect

app_name = "taller_ecuador"

urlpatterns = [
    # Redirigir raíz a bienvenida
    path("", RedirectView.as_view(url="/ec/es/bienvenida/", permanent=False), name="ecuador_home"),
    # Dashboard principal de Ecuador
    path(
        "dashboard/",
        TemplateView.as_view(template_name="ec/es/dashboard/centro_operaciones_espacial.html"),
        name="dashboard_ecuador",
    ),
    # Página de bienvenida / onboarding Ecuador
    path(
        "bienvenida/",
        TemplateView.as_view(template_name="ec/es/onboarding/bienvenida.html"),
        name="bienvenida_ecuador",
    ),
    # Página de pago de suscripción Ecuador (cuando esté lista)
    path(
        "suscripcion/pago/",
        TemplateView.as_view(template_name="ec/es/suscripcion/pago.html"),
        name="pago_suscripcion_ecuador",
    ),
    # Login Ecuador con template personalizado
    path(
        "accounts/login/",
        TemplateView.as_view(template_name="ec/es/account/login.html"),
        name="account_login",
    ),
    path(
        "login/",
        lambda r: redirect("/accounts/login/" + ("?" + r.GET.urlencode() if r.GET else "")),
        name="account_login_short",
    ),
    # Signup Ecuador - redirect a signup universal con parámetro from=ec
    path(
        "accounts/signup/",
        lambda r: signup_redirect(r, "ec"),
        name="account_signup_ecuador",
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
    # Lista de clientes Ecuador
    path(
        "clientes/",
        TemplateView.as_view(template_name="ec/es/clientes/lista_clientes.html"),
        name="lista_clientes_ecuador",
    ),
]
