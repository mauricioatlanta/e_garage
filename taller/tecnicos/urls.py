# taller/tecnicos/urls.py
from django.urls import path

from ..views_extra.tecnicos_views import (
    tecnicos_crear,
    tecnicos_editar,
    tecnicos_lista,
    tecnicos_toggle_activo,
)

app_name = "tecnicos"

urlpatterns = [
    path("", tecnicos_lista, name="lista"),
    path("nuevo/", tecnicos_crear, name="nuevo"),
    path("<int:tecnico_id>/editar/", tecnicos_editar, name="editar"),
    path("<int:tecnico_id>/toggle/", tecnicos_toggle_activo, name="toggle"),
]
