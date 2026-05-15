"""
URLs para el Marketplace de eGarage
"""

from django.urls import path

from . import views
from . import webhooks
from . import views_whatsapp

app_name = "marketplace"

urlpatterns = [
    path("api/precios/", views.api_buscar_precios_por_partnumber, name="api_precios_partnumber"),
    path("api/producto/<int:producto_id>/", views.api_producto_por_id, name="api_producto_id"),
    # Webhooks de WhatsApp
    path(
        "webhooks/whatsapp/cliente/",
        webhooks.webhook_whatsapp_cliente,
        name="webhook_whatsapp_cliente",
    ),
    path(
        "webhooks/whatsapp/proveedor/",
        webhooks.webhook_whatsapp_proveedor,
        name="webhook_whatsapp_proveedor",
    ),
    # Envío de mensajes WhatsApp
    path(
        "whatsapp/cliente/<int:documento_id>/",
        views_whatsapp.enviar_whatsapp_cliente,
        name="enviar_whatsapp_cliente",
    ),
    path(
        "whatsapp/proveedor/<int:casa_repuestos_id>/<str:part_number>/",
        views_whatsapp.enviar_whatsapp_proveedor,
        name="enviar_whatsapp_proveedor",
    ),
]
