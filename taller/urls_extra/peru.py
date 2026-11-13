"""
URLs específicas para Perú 🇵🇪
Patrón: /pe/es/ seguido de las rutas específicas
Usa TemplateView para no depender de vistas Python especiales
"""

from django.shortcuts import redirect
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from taller.views.country_aware_auth import country_aware_login

from taller.views_extra.bienvenida import bienvenida_pe
from taller.views_extra.custom_signup import CustomSignupView
from taller.views.landing_views import hub_peru

app_name = "taller_peru"

urlpatterns = [
    # TIRES - Modulo separado de Repuestos (global)
    path(
        "tires/",
        include(("taller.tires.urls", "tires"), namespace="tires"),
    ),

    # Redirigir raíz a bienvenida
    path("", hub_peru, name="peru_home"),
    # Dashboard principal de Perú
    path(
        "dashboard/",
        TemplateView.as_view(template_name="pe/es/dashboard/centro_operaciones_espacial.html"),
        name="dashboard_peru",
    ),
    # Página de bienvenida / onboarding Perú
    path("bienvenida/", bienvenida_pe, name="bienvenida_peru"),
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
    # Signup Perú - CustomSignupView (igual que Chile), sin redirect que genera loop
    path(
        "accounts/signup/",
        CustomSignupView.as_view(),
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
    
    # Reportes Perú
    path("reportes/", include(("taller.reportes.urls", "reportes"), namespace="reportes")),
    # Clientes Perú CRUD
    path("clientes/", include(("taller.clientes.urls", "clientes"), namespace="clientes")),
    path("vehiculos/", include(("taller.vehiculos.urls", "vehiculos"), namespace="vehiculos")),
]
