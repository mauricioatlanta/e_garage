from django.urls import path


from taller.autocomplete.views_autocomplete import ClienteAutocomplete, VehiculoAutocomplete, TecnicoAutocomplete, MarcaAutocomplete, ModeloAutocomplete
from taller.views_extra.views_autocomplete import ServicioAutocomplete

app_name = "autocomplete" 



urlpatterns = [
    path('cliente/', ClienteAutocomplete.as_view(), name='autocomplete_cliente'),
    path('marca/', MarcaAutocomplete.as_view(), name='autocomplete_marca'),
    path('modelo/', ModeloAutocomplete.as_view(), name='autocomplete_modelo'),
    # path('color/', ColorAutocomplete.as_view(), name='autocomplete_color'),
    # path('motor/', MotorAutocomplete.as_view(), name='autocomplete_motor'),
    # path('caja/', CajaAutocomplete.as_view(), name='autocomplete_caja'),
    path('vehiculo/', VehiculoAutocomplete.as_view(), name='autocomplete_vehiculo'),
    path('tecnico/', TecnicoAutocomplete.as_view(), name='autocomplete_tecnico'),
    path('servicio/', ServicioAutocomplete.as_view(), name='autocomplete_servicio'),
]
