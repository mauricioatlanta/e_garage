from django.urls import path
from .views_autocomplete import ClienteAutocomplete, VehiculoAutocomplete, RepuestoAutocomplete, ServicioAutocomplete

urlpatterns = [
    path('cliente/', ClienteAutocomplete.as_view(), name='autocomplete-cliente'),
    path('vehiculo/', VehiculoAutocomplete.as_view(), name='autocomplete-vehiculo'),
    path('repuesto/', RepuestoAutocomplete.as_view(), name='autocomplete-repuesto'),
    path('servicio/', ServicioAutocomplete.as_view(), name='autocomplete-servicio'),
]
