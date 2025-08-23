from django.urls import path
from taller.vehiculos import views_chile
from taller.autocomplete.views_autocomplete import MarcaAutocomplete, ModeloAutocomplete

app_name = "vehiculos_chile"

urlpatterns = [
    path('', views_chile.lista_vehiculos, name='lista_vehiculos'),
    path('crear/', views_chile.crear_vehiculo, name='crear_vehiculo'),
    path('autocomplete/marca/', MarcaAutocomplete.as_view(), name='autocomplete_marca'),
    path('autocomplete/modelo/', ModeloAutocomplete.as_view(), name='autocomplete_modelo'),
    # ...otros endpoints exclusivos de Chile...
]
