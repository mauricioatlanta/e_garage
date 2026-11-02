# taller/autocomplete/urls.py
from django.urls import path

from taller.views_autocomplete import (
    ClienteAutocomplete,
    MarcaAutocomplete,
    ModeloAutocomplete,
    RepuestoAutocomplete,
    ServicioAutocomplete,
    TecnicoAutocomplete,
    VehiculoAutocomplete,
)

app_name = "autocomplete"

urlpatterns = [
    path("cliente/", ClienteAutocomplete.as_view(), name="cliente"),
    path("vehiculo/", VehiculoAutocomplete.as_view(), name="vehiculo"),
    path("tecnico/", TecnicoAutocomplete.as_view(), name="tecnico"),
    path("marca/", MarcaAutocomplete.as_view(), name="marca"),
    path("modelo/", ModeloAutocomplete.as_view(), name="modelo"),
    path("repuesto/", RepuestoAutocomplete.as_view(), name="repuesto"),
    path("servicio/", ServicioAutocomplete.as_view(), name="servicio"),
]
