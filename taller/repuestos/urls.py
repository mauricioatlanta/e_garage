from django.urls import path
from taller.repuestos.views import (
    lista_repuestos,
    editar_repuesto,
    eliminar_repuesto,
    dashboard_repuestos,
    crear_repuesto,
    validar_part_number,
    api_autocomplete_repuesto,
)

app_name = "repuestos"

urlpatterns = [
    path('repuestos/dashboard/', dashboard_repuestos, name='dashboard_repuestos'),
    path('', lista_repuestos, name='lista_repuestos'),
    path('crear/', crear_repuesto, name='crear_repuesto'),
    path('editar/<int:repuesto_id>/', editar_repuesto, name='editar_repuesto'),
    path('eliminar/<int:repuesto_id>/', eliminar_repuesto, name='eliminar_repuesto'),
    path('api/validar_part_number/', validar_part_number, name='validar_part_number'),
    path('api/autocomplete_repuesto/', api_autocomplete_repuesto, name='autocomplete_repuesto'),
]
