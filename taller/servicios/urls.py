# Namespace para las URLs de servicios
app_name = "servicios"
# taller/servicios/urls.py
from django.urls import path

from . import views
from . import api_servicios_moderno

urlpatterns = [
    path("", views.servicios_menu, name="servicios_menu"),
    path("api/buscar/", views.buscar_servicios_api, name="buscar_servicios_api"),
    # Nuevos endpoints modernos
    path(
        "api/servicios/buscar/",
        api_servicios_moderno.api_buscar_servicios,
        name="api_servicios_buscar",
    ),
    path(
        "api/servicios/crear_rapido/",
        api_servicios_moderno.api_crear_servicio_rapido,
        name="api_servicios_crear_rapido",
    ),
    path(
        "api/categorias-subcategorias/",
        api_servicios_moderno.api_categorias_subcategorias,
        name="api_categorias_subcategorias",
    ),
    path("api/otros/buscar/", views.buscar_otros_servicios_api, name="buscar_otros_servicios_api"),
    path("api/categorias/crear/", views.crear_categoria_api, name="crear_categoria_api"),
    path("api/subcategorias/crear/", views.crear_subcategoria_api, name="crear_subcategoria_api"),
    path("crear/", views.crear_servicio, name="crear_servicio"),
    path("<int:pk>/", views.ver_servicio, name="ver_servicio"),
    path("<int:pk>/editar/", views.editar_servicio, name="editar_servicio"),
    path("<int:pk>/eliminar/", views.eliminar_servicio, name="eliminar_servicio"),
    path("otros-servicios/", views.otros_servicios_menu, name="otros_servicios_menu"),
    path("otros-servicios/crear/", views.crear_otro_servicio, name="crear_otro_servicio"),
    path("otros-servicios/<int:pk>/editar/", views.editar_otro_servicio, name="editar_otro_servicio"),
    path("otros-servicios/<int:pk>/eliminar/", views.eliminar_otro_servicio, name="eliminar_otro_servicio"),
]
