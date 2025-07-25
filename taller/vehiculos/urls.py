from django.urls import path
from taller.vehiculos import views
from taller.autocomplete.views_autocomplete import ClienteAutocomplete, MarcaAutocomplete, ModeloAutocomplete
from taller.vehiculos.views_autocomplete import VehiculoAutocomplete
from taller.vehiculos.views_autocomplete_color import ColorVehiculoAutocomplete
from taller.vehiculos.views_autocomplete_motor import MotorVehiculoAutocomplete
from taller.vehiculos.views_autocomplete_caja import CajaVehiculoAutocomplete
from taller.vehiculos.api import obtener_modelos


app_name = "vehiculos"

urlpatterns = [
    path('', views.lista_vehiculos, name='lista_vehiculos'),
    path('crear/', views.crear_vehiculo, name='crear_vehiculo'),
    path('api/modelos/', obtener_modelos, name='obtener_modelos'),
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
]
