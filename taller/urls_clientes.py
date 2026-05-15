from django.http import HttpResponseNotFound
from django.urls import path

try:
    from . import views_clientes as v
except Exception:
    from . import views as v

app_name = "clientes"


def pick(cbv, fbv, *alts):
    """
    Si existe CBV -> as_view(); si no, prueba FBVs por nombre.
    Si nada existe, devuelve una vista 404 con mensaje.
    """
    if hasattr(v, cbv):
        return getattr(v, cbv).as_view()
    for name in (fbv,) + alts:
        if hasattr(v, name):
            return getattr(v, name)
    candidatos = (cbv,) + (fbv,) + alts

    def missing(request, *a, **kw):
        return HttpResponseNotFound("Vista no encontrada. Crea alguna de: " + ", ".join(candidatos))

    return missing


urlpatterns = [
    # Listado y CRUD (dos nombres para el detalle como alias)
    path(
        "",
        pick(
            "ClienteListView",
            "lista_clientes",
            "listar_clientes",
            "clientes_list",
            "cliente_list",
            "clientes",
            "index",
        ),
        name="lista_clientes",
    ),
    path(
        "nuevo/",
        pick("ClienteCreateView", "crear_cliente", "cliente_create", "nuevo_cliente"),
        name="crear_cliente",
    ),
    path(
        "<int:pk>/",
        pick("ClienteDetailView", "ver_cliente", "detalle_cliente", "cliente_detail"),
        name="ver_cliente",
    ),
    path(
        "<int:pk>/",
        pick("ClienteDetailView", "detalle_cliente", "ver_cliente", "cliente_detail"),
        name="detalle_cliente",
    ),
    path(
        "<int:pk>/editar/",
        pick(
            "ClienteUpdateView",
            "editar_cliente",
            "cliente_update",
            "actualizar_cliente",
        ),
        name="editar_cliente",
    ),
    path(
        "<int:cliente_id>/eliminar/",
        pick(
            "ClienteDeleteView",
            "eliminar_cliente",
            "cliente_delete",
            "borrar_cliente",
            "delete",
        ),
        name="eliminar_cliente",
    ),
    path(
        "delete/<int:pk>/",
        pick(
            "ClienteDeleteView",
            "delete",
            "eliminar_cliente",
            "cliente_delete",
            "borrar_cliente",
        ),
        name="delete",
    ),
    # Endpoints AJAX/REST (si faltan, responderán 404 con mensaje)
    path(
        "ajax/buscar/",
        getattr(v, "ajax_buscar_clientes", pick("X", "ajax_buscar_clientes")),
        name="ajax_buscar_clientes",
    ),
    path(
        "api/ciudades/",
        getattr(v, "obtener_ciudades", pick("X", "obtener_ciudades")),
        name="obtener_ciudades",
    ),
    path(
        "api/ciudades-usa/",
        getattr(v, "obtener_ciudades_usa", pick("X", "obtener_ciudades_usa")),
        name="obtener_ciudades_usa",
    ),
    path(
        "api/agregar-ciudad/",
        getattr(v, "agregar_ciudad", pick("X", "agregar_ciudad")),
        name="agregar_ciudad",
    ),
    path(
        "api/agregar-ciudad-usa/",
        getattr(v, "agregar_ciudad_usa", pick("X", "agregar_ciudad_usa")),
        name="agregar_ciudad_usa",
    ),
    path(
        "api/agregar-region/",
        getattr(v, "agregar_region", pick("X", "agregar_region")),
        name="agregar_region",
    ),
    path(
        "api/agregar-estado/",
        getattr(v, "agregar_estado", pick("X", "agregar_estado")),
        name="agregar_estado",
    ),
]
