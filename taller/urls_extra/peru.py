"""
URLs específicas para Perú 🇵🇪
Patrón: /pe/es/ seguido de las rutas específicas
Usa TemplateView para no depender de vistas Python especiales
"""

from django.urls import path
from django.views.generic import RedirectView, TemplateView

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
    # Login Perú (opcional, si quieres una vista visual distinta de allauth)
    path(
        "accounts/login/",
        TemplateView.as_view(template_name="pe/es/account/login.html"),
        name="account_login_peru",
    ),
    # Signup Perú (si tienes template específico)
    path(
        "accounts/signup/",
        TemplateView.as_view(template_name="pe/es/account/signup.html"),
        name="account_signup_peru",
    ),
    # Lista de clientes Perú
    path(
        "clientes/",
        TemplateView.as_view(template_name="pe/es/clientes/lista_clientes.html"),
        name="lista_clientes_peru",
    ),
]
