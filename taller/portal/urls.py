"""
URLs del Portal del Cliente
"""

from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.portal_login, name="login"),
    path("login/", views.portal_login, name="login"),
    path("logout/", views.portal_logout, name="logout"),
    path("historial/", views.portal_historial, name="historial"),
    path(
        "historial/<int:vehiculo_id>/", views.portal_historial_vehiculo, name="historial_vehiculo"
    ),
    path("historial/<int:vehiculo_id>/pdf/", views.portal_exportar_pdf, name="exportar_pdf"),
]
