"""
URLs específicas para Venezuela 🇻🇪
Patrón: /ve/es/ seguido de las rutas específicas
Usa TemplateView para no depender de vistas Python especiales
"""

from django.shortcuts import redirect
from django.urls import path
from django.views.generic import RedirectView, TemplateView

from taller.vehiculos import views_country_aware as views_vehiculos
from taller.views.country_aware_auth import country_aware_login
from taller.views_extra.signup_redirects import signup_redirect

app_name = "taller_venezuela"

urlpatterns = [
    # Redirigir raíz a bienvenida
    path(
        "", RedirectView.as_view(url="/ve/es/bienvenida/", permanent=False), name="venezuela_home"
    ),
    # Dashboard principal de Venezuela
    path(
        "dashboard/",
        TemplateView.as_view(template_name="ve/es/dashboard/centro_operaciones_espacial.html"),
        name="dashboard_venezuela",
    ),
    # Página de bienvenida / onboarding Venezuela
    path(
        "bienvenida/",
        TemplateView.as_view(template_name="ve/es/onboarding/bienvenida.html"),
        name="bienvenida_venezuela",
    ),
    # Página de pago de suscripción Venezuela (cuando esté lista)
    path(
        "suscripcion/pago/",
        TemplateView.as_view(template_name="ve/es/suscripcion/pago.html"),
        name="pago_suscripcion_venezuela",
    ),
    # Login Venezuela: country_aware_login usa template ve/es/account/login.html y procesa el form
    path(
        "accounts/login/",
        country_aware_login,
        name="account_login",
    ),
    # Signup Venezuela - redirect a signup universal con parámetro from=ve
    path(
        "accounts/signup/",
        lambda r: signup_redirect(r, "ve"),
        name="account_signup_venezuela",
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
    # Lista de clientes Venezuela
    path(
        "clientes/",
        TemplateView.as_view(template_name="ve/es/clientes/lista_clientes.html"),
        name="lista_clientes_venezuela",
    ),
    # =========================
    # Vehículos Venezuela
    # =========================
    # Lista de vehículos Venezuela
    path(
        "vehiculos/",
        views_vehiculos.vehiculo_listar,
        {"country_code": "ve", "lang_code": "es"},
        name="lista_vehiculos_ve",
    ),
    # Crear vehículo Venezuela
    path(
        "vehiculos/crear/",
        views_vehiculos.vehiculo_crear,
        {"country_code": "ve", "lang_code": "es"},
        name="crear_vehiculo_ve",
    ),
    # Editar vehículo Venezuela
    path(
        "vehiculos/<int:pk>/editar/",
        views_vehiculos.vehiculo_editar,
        {"country_code": "ve", "lang_code": "es"},
        name="editar_vehiculo_ve",
    ),
    # Detalle vehículo Venezuela
    path(
        "vehiculos/<int:pk>/",
        views_vehiculos.vehiculo_detalle,
        {"country_code": "ve", "lang_code": "es"},
        name="detalle_vehiculo_ve",
    ),
]
