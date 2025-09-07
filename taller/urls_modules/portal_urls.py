"""
🌐 URLs DEL PORTAL DE CLIENTES
=============================

URLs para el portal web de clientes
"""

from django.urls import path

from taller.views.portal_views import (ajax_detalle_documento,
                                       portal_dashboard, portal_documentos,
                                       portal_login, portal_logout,
                                       portal_mis_solicitudes,
                                       portal_solicitar_presupuesto,
                                       portal_vehiculos)

urlpatterns = [
    # Login/Logout
    path("", portal_login, name="portal_login"),
    path("login/", portal_login, name="portal_login"),
    path("logout/", portal_logout, name="portal_logout"),
    # Portal principal
    path("dashboard/", portal_dashboard, name="portal_dashboard"),
    # Documentos
    path("documentos/", portal_documentos, name="portal_documentos"),
    # Solicitudes
    path(
        "solicitar-presupuesto/",
        portal_solicitar_presupuesto,
        name="portal_solicitar_presupuesto",
    ),
    path("mis-solicitudes/", portal_mis_solicitudes, name="portal_mis_solicitudes"),
    # Vehículos
    path("vehiculos/", portal_vehiculos, name="portal_vehiculos"),
    # AJAX
    path(
        "ajax/documento/<int:documento_id>/",
        ajax_detalle_documento,
        name="ajax_detalle_documento",
    ),
]
