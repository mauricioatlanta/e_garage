from django.urls import path

from taller.vehiculos import views_chile

app_name = "vehiculos_chile"

urlpatterns = [
    path("", views_chile.lista_vehiculos, name="lista_vehiculos"),
    path("crear/", views_chile.crear_vehiculo, name="crear_vehiculo"),
    # Las rutas de autocomplete ahora están centralizadas en taller.autocomplete.urls
    # Se acceden como: autocomplete:marca, autocomplete:modelo
    # ...otros endpoints exclusivos de Chile...
]
