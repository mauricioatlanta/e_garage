# taller/vehiculos/urls.py
from django.urls import path

from taller.vehiculos import views_fbv as views  # 👈 usar el archivo consolidado

app_name = "vehiculos"

urlpatterns = [
    # Vistas principales
    path("", views.lista_vehiculos, name="lista_vehiculos"),
    path("crear/", views.crear_vehiculo, name="crear_vehiculo"),
    path("<int:pk>/", views.ver_vehiculo, name="ver_vehiculo"),
    path("<int:vehiculo_id>/editar/", views.editar_vehiculo, name="editar_vehiculo"),
    path(
        "<int:vehiculo_id>/eliminar/", views.eliminar_vehiculo, name="eliminar_vehiculo"
    ),
    # APIs / AJAX (todas en el módulo consolidado)
    path("api/marcas/", views.api_marcas, name="api_marcas"),
    path("api/clientes/", views.api_busqueda_clientes, name="api_busqueda_clientes"),
    path("api/colores/", views.api_colores, name="api_colores"),
    path("api/modelos-usa/", views.api_modelos_usa, name="api_modelos_usa"),
    path(
        "ajax/modelos-por-marca/",
        views.ajax_modelos_por_marca,
        name="ajax_modelos_por_marca",
    ),
    path(
        "ajax/modelos-por-marca-anio/",
        views.ajax_modelos_por_marca_anio,
        name="ajax_modelos_por_marca_anio",
    ),
    path(
        "ajax/motores-por-modelo/",
        views.ajax_motores_por_modelo,
        name="ajax_motores_por_modelo",
    ),
    path(
        "ajax/cajas-por-modelo/",
        views.ajax_cajas_por_modelo,
        name="ajax_cajas_por_modelo",
    ),
    path("ajax/agregar-marca/", views.ajax_agregar_marca, name="ajax_agregar_marca"),
    path("ajax/agregar-modelo/", views.ajax_agregar_modelo, name="ajax_agregar_modelo"),
    path("ajax/agregar-motor/", views.ajax_agregar_motor, name="ajax_agregar_motor"),
    path("ajax/agregar-caja/", views.ajax_agregar_caja, name="ajax_agregar_caja"),
]
