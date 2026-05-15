from django.urls import path

from .views import ciudades_por_estado, registro_ubicacion, zip_code_por_ciudad

urlpatterns = [
    path("registro/", registro_ubicacion, name="registro_ubicacion"),
    path("api/ciudades/<int:estado_id>/", ciudades_por_estado, name="ciudades_por_estado"),
    path(
        "api/zip-code/<str:ciudad_nombre>/",
        zip_code_por_ciudad,
        name="zip_code_por_ciudad",
    ),
]
