
from django.urls import path
from taller.views.clientes_views import eliminar_cliente
from taller.views.vehiculos import eliminar_vehiculo
from taller.views.documentos import eliminar_documento

urlpatterns = [
    path('clientes/eliminar/<int:cliente_id>/', eliminar_cliente, name='eliminar_cliente'),
    path('vehiculos/eliminar/<int:vehiculo_id>/', eliminar_vehiculo, name='eliminar_vehiculo'),
    path('documentos/eliminar/<int:documento_id>/', eliminar_documento, name='eliminar_documento'),
]
