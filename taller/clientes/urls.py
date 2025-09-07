from django.urls import path

from .views import (agregar_ciudad, ajax_buscar_clientes, cliente_delete,
                    clientes_stats, crear_cliente, editar_cliente,
                    lista_clientes, obtener_ciudades, obtener_ciudades_usa,
                    ver_cliente)

app_name = "clientes"

urlpatterns = [
    path("", lista_clientes, name="lista_clientes"),
    path("crear/", crear_cliente, name="crear_cliente"),
    path("editar/<int:pk>/", editar_cliente, name="editar_cliente"),
    # Usamos cliente_id como nombre de parámetro para compatibilidad con
    # versiones antiguas (gestion_taller) que esperan ese kwarg.
    path("eliminar/<int:cliente_id>/", cliente_delete, name="eliminar_cliente"),
    # Ruta opcional alternativa (se puede retirar luego) que acepta pk explícito
    path("eliminar/pk/<int:pk>/", cliente_delete, name="eliminar_cliente_pk"),
    path("ver/<int:pk>/", ver_cliente, name="ver_cliente"),
    path("ajax/ciudades/", obtener_ciudades, name="obtener_ciudades"),
    path("ajax/ciudades_usa/", obtener_ciudades_usa, name="obtener_ciudades_usa"),
    path("ajax/agregar_ciudad/", agregar_ciudad, name="agregar_ciudad"),
    path("ajax/buscar/", ajax_buscar_clientes, name="ajax_buscar_clientes"),
    path("stats/", clientes_stats, name="clientes_stats"),
]
