from django.urls import path
from .views import lista_clientes, crear_cliente, editar_cliente, eliminar_cliente, ver_cliente, obtener_ciudades, ajax_buscar_clientes

app_name = 'clientes'

urlpatterns = [
    path('', lista_clientes, name='lista_clientes'),
    path('crear/', crear_cliente, name='crear_cliente'),
    path('editar/<int:pk>/', editar_cliente, name='editar_cliente'),
    path('eliminar/<int:pk>/', eliminar_cliente, name='eliminar_cliente'),
    path('ver/<int:pk>/', ver_cliente, name='ver_cliente'),
    path('ajax/ciudades/', obtener_ciudades, name='obtener_ciudades'),
    path('ajax/buscar/', ajax_buscar_clientes, name='ajax_buscar_clientes'),
]