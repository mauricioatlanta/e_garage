from django.urls import path

from . import autocomplete

app_name = "vehiculos_autocomplete"

urlpatterns = [
    path("marca/", autocomplete.MarcaAutocomplete.as_view(), name="marca"),
    path("modelo/", autocomplete.ModeloAutocomplete.as_view(), name="modelo"),
    path("motor/", autocomplete.MotorAutocomplete.as_view(), name="motor"),
    path("caja/", autocomplete.CajaAutocomplete.as_view(), name="caja"),
    path("cliente/", autocomplete.ClienteAutocomplete.as_view(), name="cliente"),
]
