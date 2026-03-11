"""
URLs del módulo de desarmaduría.
"""

from django.urls import path

from .views_desarme import (
    demo_mapa_desarme,
    pieza_por_zona,
    resumen_json,
    vehiculo_mapa_desarme,
)
from .views_desarme.cierre import cerrar_vehiculo_desarme
from .views_desarme.dashboard_financiero import dashboard_vehiculo_desarme
from .views_desarme.plantillas import (
    plantilla_aplicar,
    plantilla_create,
    plantilla_detail,
    plantilla_edit,
    plantilla_list,
)
from .views_desarme.home import home_desarme
from .views_desarme.vehiculos import (
    lista_vehiculos_desarme,
    crear_vehiculo_desarme,
)

app_name = "desarme"

urlpatterns = [
    # Home del módulo de desarmaduría
    path("", home_desarme, name="home"),
    path("demo/", demo_mapa_desarme, name="demo"),
    # Vehículos de desarme
    path("vehiculos/", lista_vehiculos_desarme, name="vehiculos_list"),
    path("vehiculos/nuevo/", crear_vehiculo_desarme, name="crear_vehiculo_desarme"),
    path("vehiculos/<int:pk>/mapa/", vehiculo_mapa_desarme, name="mapa_piezas"),
    path("vehiculos/<int:pk>/pieza-por-zona/", pieza_por_zona, name="pieza_por_zona"),
    path("vehiculos/<int:pk>/resumen-json/", resumen_json, name="resumen_json"),
    path("vehiculos/<int:pk>/dashboard/", dashboard_vehiculo_desarme, name="dashboard_financiero"),
    path("vehiculos/<int:pk>/cerrar/", cerrar_vehiculo_desarme, name="cerrar_vehiculo"),
    path("vehiculos/<int:pk>/aplicar-plantilla/", plantilla_aplicar, name="aplicar_plantilla"),
    # Plantillas de desarmaduría
    path("plantillas/", plantilla_list, name="plantilla_list"),
    path("plantillas/nueva/", plantilla_create, name="plantilla_create"),
    path("plantillas/<int:pk>/", plantilla_detail, name="plantilla_detail"),
    path("plantillas/<int:pk>/editar/", plantilla_edit, name="plantilla_edit"),
]
