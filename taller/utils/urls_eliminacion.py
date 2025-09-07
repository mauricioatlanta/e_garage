from django.urls import path

# Import actualizado al módulo unificado de clientes
from taller.clientes.views import eliminar_cliente
from taller.documentos.views import eliminar_documento
from taller.viewsautocomplete.views import eliminar_vehiculo  # legacy

urlpatterns = [
    # Mantiene cliente_id por compatibilidad; la vista acepta cliente_id o pk
    path(
        "clientes/eliminar/<int:cliente_id>/", eliminar_cliente, name="eliminar_cliente"
    ),
    path(
        "vehiculos/eliminar/<int:vehiculo_id>/",
        eliminar_vehiculo,
        name="eliminar_vehiculo",
    ),
    path(
        "documentos/eliminar/<int:documento_id>/",
        eliminar_documento,
        name="eliminar_documento",
    ),
]
