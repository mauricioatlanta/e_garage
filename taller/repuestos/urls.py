from django.urls import path
from taller.repuestos.views import (
    lista_repuestos,
    ver_repuesto,
    editar_repuesto,
    crear_repuesto,
)

app_name = "repuestos"

urlpatterns = [
    path('', lista_repuestos, name='lista_repuestos'),
    path('crear/', crear_repuesto, name='crear_repuesto'),
    path('<int:pk>/', ver_repuesto, name='ver_repuesto'),
    path('editar/<int:pk>/', editar_repuesto, name='editar_repuesto'),
]
