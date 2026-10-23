from django.urls import path

from . import views

app_name = "gruas"

urlpatterns = [
    path("", views.dispatch_board, name="dispatch_board"),
    path("ordenes/nueva/", views.order_create, name="order_create"),
    path("ordenes/<int:order_id>/", views.order_detail, name="order_detail"),
    path("unidades/", views.units, name="units"),
    path("conductores/", views.units, name="drivers"),
    path("conductor/", views.driver_home, name="driver_home"),
    path("conductor/ordenes/<int:order_id>/estado/", views.driver_update, name="driver_update"),
    path("conductor/ordenes/<int:order_id>/evidencias/", views.driver_evidence_upload, name="driver_evidence_upload"),
    path("evidencias/<int:evidence_id>/descargar/", views.evidence_download, name="evidence_download"),
]
