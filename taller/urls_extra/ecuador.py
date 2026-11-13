"""
URLs específicas para Ecuador 🇪🇨
Patrón: /ec/es/ seguido de las rutas específicas
Usa TemplateView para no depender de vistas Python especiales
"""

from django.shortcuts import redirect
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from taller.views.country_aware_auth import country_aware_login

from taller.views_extra.bienvenida import bienvenida_ec
from taller.views_extra.signup_redirects import signup_redirect

app_name = "taller_ecuador"

urlpatterns = [
    # TIRES - Modulo separado de Repuestos (global)
    path(
        "tires/",
        include(("taller.tires.urls", "tires"), namespace="tires"),
    ),

    # Redirigir raíz a bienvenida
    path("", RedirectView.as_view(url="/ec/es/bienvenida/", permanent=False), name="ecuador_home"),
    # Dashboard principal de Ecuador
    path(
        "dashboard/",
        TemplateView.as_view(template_name="ec/es/dashboard/centro_operaciones_espacial.html"),
        name="dashboard_ecuador",
    ),
    # Página de bienvenida / onboarding Ecuador
    path("bienvenida/", bienvenida_ec, name="bienvenida_ecuador"),
    # Página de pago de suscripción Ecuador (cuando esté lista)
    path(
        "suscripcion/pago/",
        TemplateView.as_view(template_name="ec/es/suscripcion/pago.html"),
        name="pago_suscripcion_ecuador",
    ),
    path(
        "accounts/login/",
        country_aware_login,
        name="account_login",
    ),
    path(
        "login/",
        lambda r: redirect("/ec/es/accounts/login/" + ("?" + r.GET.urlencode() if r.GET else "")),
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
    
    # Reportes Ecuador
    path("reportes/", include(("taller.reportes.urls", "reportes"), namespace="reportes")),
    # Clientes Ecuador CRUD
    path("clientes/", include(("taller.clientes.urls", "clientes"), namespace="clientes")),
    path("vehiculos/", include(("taller.vehiculos.urls", "vehiculos"), namespace="vehiculos")),
]
