"""
URLs específicas para México 🇲🇽
Patrón: /mx/es/ seguido de las rutas específicas
Usa TemplateView para no depender de vistas Python especiales
"""

from django.urls import path
from django.views.generic import RedirectView, TemplateView

from taller.vehiculos import views_country_aware as views_vehiculos

app_name = "taller_mexico"

urlpatterns = [
    # Redirigir raíz a bienvenida
    path("", RedirectView.as_view(url="/mx/es/bienvenida/", permanent=False), name="mexico_home"),
    # Dashboard principal de México
    path(
        "dashboard/",
        TemplateView.as_view(template_name="mx/es/dashboard/centro_operaciones_espacial.html"),
        name="dashboard_mexico",
    ),
    # Página de bienvenida / onboarding México
    path(
        "bienvenida/",
        TemplateView.as_view(template_name="mx/es/onboarding/bienvenida.html"),
        name="bienvenida_mexico",
    ),
    # Página de pago de suscripción México (cuando esté lista)
    path(
        "suscripcion/pago/",
        TemplateView.as_view(template_name="mx/es/suscripcion/pago.html"),
        name="pago_suscripcion_mexico",
    ),
    # Login México (opcional, si quieres una vista visual distinta de allauth)
    path(
        "accounts/login/",
        TemplateView.as_view(template_name="mx/es/account/login.html"),
        name="account_login_mexico",
    ),
    # Signup México (si tienes template específico)
    path(
        "accounts/signup/",
        TemplateView.as_view(template_name="mx/es/account/signup.html"),
        name="account_signup_mexico",
    ),
    # *** Primera vista real de módulo: lista de clientes México ***
    path(
        "clientes/",
        TemplateView.as_view(template_name="mx/es/clientes/lista_clientes.html"),
        name="lista_clientes_mexico",
    ),
    # =========================
    # Vehículos México
    # =========================
    # Lista de vehículos México
    path(
        "vehiculos/",
        views_vehiculos.vehiculo_listar,
        {"country_code": "mx", "lang_code": "es"},
        name="lista_vehiculos_mx",
    ),
    # Crear vehículo México
    path(
        "vehiculos/crear/",
        views_vehiculos.vehiculo_crear,
        {"country_code": "mx", "lang_code": "es"},
        name="crear_vehiculo_mx",
    ),
    # Editar vehículo México
    path(
        "vehiculos/<int:pk>/editar/",
        views_vehiculos.vehiculo_editar,
        {"country_code": "mx", "lang_code": "es"},
        name="editar_vehiculo_mx",
    ),
    # Detalle vehículo México
    path(
        "vehiculos/<int:pk>/",
        views_vehiculos.vehiculo_detalle,
        {"country_code": "mx", "lang_code": "es"},
        name="detalle_vehiculo_mx",
    ),
]
