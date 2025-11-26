"""
URLs específicas para Colombia 🇨🇴
Patrón: /co/es/ seguido de las rutas específicas
Usa TemplateView para no depender de vistas Python especiales
"""

from django.urls import path
from django.views.generic import RedirectView, TemplateView

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
    # Login Colombia (opcional, si quieres una vista visual distinta de allauth)
    path(
        "accounts/login/",
        TemplateView.as_view(template_name="co/es/account/login.html"),
        name="account_login_colombia",
    ),
    # Signup Colombia (si tienes template específico)
    path(
        "accounts/signup/",
        TemplateView.as_view(template_name="co/es/account/signup.html"),
        name="account_signup_colombia",
    ),
    # Lista de clientes Colombia
    path(
        "clientes/",
        TemplateView.as_view(template_name="co/es/clientes/lista_clientes.html"),
        name="lista_clientes_colombia",
    ),
]
