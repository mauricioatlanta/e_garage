"""
URLs específicas para Ecuador 🇪🇨
Patrón: /ec/es/ seguido de las rutas específicas
Usa TemplateView para no depender de vistas Python especiales
"""

from django.urls import path
from django.views.generic import RedirectView, TemplateView

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
    # Login Ecuador (opcional, si quieres una vista visual distinta de allauth)
    path(
        "accounts/login/",
        TemplateView.as_view(template_name="ec/es/account/login.html"),
        name="account_login_ecuador",
    ),
    # Signup Ecuador (si tienes template específico)
    path(
        "accounts/signup/",
        TemplateView.as_view(template_name="ec/es/account/signup.html"),
        name="account_signup_ecuador",
    ),
    # Lista de clientes Ecuador
    path(
        "clientes/",
        TemplateView.as_view(template_name="ec/es/clientes/lista_clientes.html"),
        name="lista_clientes_ecuador",
    ),
]
