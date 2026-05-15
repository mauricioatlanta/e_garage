"""
URLs públicas para acceso de clientes a documentos sin autenticación.
"""

from django.urls import path

from taller.views_extra.public_views import (
    aprobar_presupuesto,
    detalle_presupuesto_publico,
)

app_name = "publico"

urlpatterns = [
    path("presupuesto/<uuid:uuid>/", detalle_presupuesto_publico, name="ver_presupuesto"),
    path("presupuesto/<uuid:uuid>/aprobar/", aprobar_presupuesto, name="aprobar_presupuesto"),
]
