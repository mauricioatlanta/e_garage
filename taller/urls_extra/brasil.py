"""
URLs específicas para Brasil 🇧🇷
Patrón: /br/es/ seguido de las rutas específicas
Usa TemplateView para no depender de vistas Python especiales
Nota: Brasil puede usar 'pt-br' en el futuro, pero por ahora usamos 'es' para consistencia
"""

from django.urls import path
from django.views.generic import RedirectView, TemplateView

app_name = "taller_brasil"

urlpatterns = [
    # Redirigir raíz a bienvenida
    path("", RedirectView.as_view(url="/br/es/bienvenida/", permanent=False), name="brasil_home"),
    # Dashboard principal de Brasil
    path(
        "dashboard/",
        TemplateView.as_view(template_name="br/es/dashboard/centro_operaciones_espacial.html"),
        name="dashboard_brasil",
    ),
    # Página de bienvenida / onboarding Brasil
    path(
        "bienvenida/",
        TemplateView.as_view(template_name="br/es/onboarding/bienvenida.html"),
        name="bienvenida_brasil",
    ),
    # Página de pago de suscripción Brasil (cuando esté lista)
    path(
        "suscripcion/pago/",
        TemplateView.as_view(template_name="br/es/suscripcion/pago.html"),
        name="pago_suscripcion_brasil",
    ),
    # Login Brasil (opcional, si quieres una vista visual distinta de allauth)
    path(
        "accounts/login/",
        TemplateView.as_view(template_name="br/es/account/login.html"),
        name="account_login_brasil",
    ),
    # Signup Brasil (si tienes template específico)
    path(
        "accounts/signup/",
        TemplateView.as_view(template_name="br/es/account/signup.html"),
        name="account_signup_brasil",
    ),
    # Lista de clientes Brasil
    path(
        "clientes/",
        TemplateView.as_view(template_name="br/es/clientes/lista_clientes.html"),
        name="lista_clientes_brasil",
    ),
]
