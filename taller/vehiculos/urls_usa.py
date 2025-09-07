from django.urls import path

from . import views_usa

app_name = "vehiculos_usa"

urlpatterns = [
    path("", views_usa.lista_vehiculos, name="lista_vehiculos"),
    path("crear/", views_usa.crear_vehiculo, name="crear_vehiculo"),
    path("<int:pk>/", views_usa.ver_vehiculo, name="ver_vehiculo"),
    path(
        "<int:vehiculo_id>/editar/", views_usa.editar_vehiculo, name="editar_vehiculo"
    ),
]
