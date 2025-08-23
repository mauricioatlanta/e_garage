from django.urls import path
from taller.vehiculos import views_usa
from taller.vehiculos.views_autocomplete_marca_usa import MarcaVehiculoUSA_Autocomplete
from taller.vehiculos.views_autocomplete_modelo_usa import ModeloVehiculoUSA_Autocomplete
from taller.autocomplete.views_autocomplete import ClienteAutocomplete

app_name = "vehiculos_usa"

urlpatterns = [
    path('', views_usa.lista_vehiculos, name='lista_vehiculos'),
    path('crear/', views_usa.crear_vehiculo, name='crear_vehiculo'),
    path('autocomplete/cliente/', ClienteAutocomplete.as_view(), name='autocomplete_cliente'),
    path('autocomplete/marca_usa/', MarcaVehiculoUSA_Autocomplete.as_view(), name='autocomplete_marca_usa'),
    path('autocomplete/modelo_usa/', ModeloVehiculoUSA_Autocomplete.as_view(), name='autocomplete_modelo_usa'),
    # ...otros endpoints exclusivos de USA...
]
