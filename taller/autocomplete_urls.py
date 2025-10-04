# taller/autocomplete_urls.py
from django.urls import path
from .autocomplete.views import ClienteAutocomplete, VehiculoAutocomplete

app_name = "autocomplete"
urlpatterns = [
    path("cliente/", ClienteAutocomplete.as_view(), name="cliente"),
    path("vehiculo/", VehiculoAutocomplete.as_view(), name="vehiculo"),
]
