from django.urls import path

from taller.views_extra.admin_suscriptores import (
    admin_suscriptores,
    actualizar_telefono_ajax,
    cambiar_plan_ajax,
    desactivar_suscripcion_ajax,
    detalle_suscriptor,
    eliminar_suscriptor_ajax,
    extender_suscripcion_ajax,
    toggle_kiosko_autorizado,
)

urlpatterns = [
    path("", admin_suscriptores, name="admin_suscriptores"),
    path("<int:empresa_id>/", detalle_suscriptor, name="admin_detalle_suscriptor"),
    path(
        "<int:empresa_id>/extender/", extender_suscripcion_ajax, name="admin_extender_suscripcion"
    ),
    path(
        "<int:empresa_id>/cambiar-plan/", cambiar_plan_ajax, name="admin_cambiar_plan"
    ),
    path(
        "<int:empresa_id>/desactivar/",
        desactivar_suscripcion_ajax,
        name="admin_desactivar_suscripcion",
    ),
    path("<int:empresa_id>/eliminar/", eliminar_suscriptor_ajax, name="admin_eliminar_suscriptor"),
    path(
        "<int:empresa_id>/actualizar-telefono/",
        actualizar_telefono_ajax,
        name="admin_actualizar_telefono",
    ),
    path(
        "<int:empresa_id>/kiosko/toggle/",
        toggle_kiosko_autorizado,
        name="admin_toggle_kiosko",
    ),
]
