from django.urls import path
from taller.vehiculos import views
from taller.autocomplete.views_autocomplete import ClienteAutocomplete, MarcaAutocomplete, ModeloAutocomplete
from taller.vehiculos.views_autocomplete import VehiculoAutocomplete
from taller.vehiculos.views_autocomplete_modelo_usa import ModeloVehiculoUSA_Autocomplete
from taller.vehiculos.views_autocomplete_marca_usa import MarcaVehiculoUSA_Autocomplete
from taller.vehiculos.views_autocomplete_color import ColorVehiculoAutocomplete
from taller.vehiculos.views_autocomplete_motor import MotorVehiculoAutocomplete
from taller.vehiculos.views_autocomplete_caja import CajaVehiculoAutocomplete
from taller.vehiculos.api import obtener_modelos, api_modelos_usa, crear_modelo, api_motores_por_modelo, api_cajas_por_modelo


app_name = "vehiculos"

urlpatterns = [
    path('', views.lista_vehiculos, name='lista_vehiculos'),
    path('crear/', views.crear_vehiculo, name='crear_vehiculo'),
    # Autocomplete Chile (namespace unificado)
    path('autocomplete/marca/', MarcaAutocomplete.as_view(), name='autocomplete_marca'),
    path('autocomplete/modelo/', ModeloAutocomplete.as_view(), name='autocomplete_modelo'),
    path('api/modelos/', obtener_modelos, name='obtener_modelos'),
    path('api/modelos/crear/', crear_modelo, name='crear_modelo'),
    path('api/modelos-usa/', api_modelos_usa, name='api_modelos_usa'),
    path('api/motores/', api_motores_por_modelo, name='api_motores_por_modelo'),
    path('api/cajas/', api_cajas_por_modelo, name='api_cajas_por_modelo'),
    path('api/clientes/', views.api_busqueda_clientes, name='api_busqueda_clientes'),
    path('api/marcas/', views.api_marcas, name='api_marcas'),
    # Vista detalle de vehículo
    path('<int:pk>/', views.ver_vehiculo, name='ver_vehiculo'),
    path('<int:vehiculo_id>/editar/', views.editar_vehiculo, name='editar_vehiculo'),
    path('<int:vehiculo_id>/eliminar/', views.eliminar_vehiculo, name='eliminar_vehiculo'),
    path('autocomplete/cliente/', ClienteAutocomplete.as_view(), name='autocomplete_cliente'),
    path('autocomplete/vehiculo/', VehiculoAutocomplete.as_view(), name='autocomplete_vehiculo'),
    path('autocomplete/color/', ColorVehiculoAutocomplete.as_view(), name='autocomplete_color'),
    path('autocomplete/motor/', MotorVehiculoAutocomplete.as_view(), name='autocomplete_motor'),
    path('autocomplete/caja/', CajaVehiculoAutocomplete.as_view(), name='autocomplete_caja'),
    path('autocomplete/modelo_usa/', ModeloVehiculoUSA_Autocomplete.as_view(), name='autocomplete_modelo_usa'),
    path('autocomplete/marca_usa/', MarcaVehiculoUSA_Autocomplete.as_view(), name='autocomplete_marca_usa'),
]
