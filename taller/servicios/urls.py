# Namespace para las URLs de servicios
app_name = "servicios"
# taller/servicios/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("", views.servicios_menu, name="servicios_menu"),
    path("api/buscar/", views.buscar_servicios_api, name="buscar_servicios_api"),
    path("api/otros/buscar/", views.buscar_otros_servicios_api, name="buscar_otros_servicios_api"),
    path("api/categorias/crear/", views.crear_categoria_api, name="crear_categoria_api"),
    path("api/subcategorias/crear/", views.crear_subcategoria_api, name="crear_subcategoria_api"),
    path("crear/", views.crear_servicio, name="crear_servicio"),
    path("<int:servicio_id>/", views.ver_servicio, name="ver_servicio"),
    path("<int:servicio_id>/editar/", views.editar_servicio, name="editar_servicio"),
    # path('<int:servicio_id>/eliminar/', views.eliminar_servicio, name='eliminar_servicio'),  # Función no existe
    path("otros-servicios/", views.otros_servicios_menu, name="otros_servicios_menu"),
    path("otros-servicios/crear/", views.crear_otro_servicio, name="crear_otro_servicio"),
]
