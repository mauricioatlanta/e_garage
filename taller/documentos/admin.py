from django.contrib import admin

from taller.models.lineas_documento import (
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
)

from .forms import DocumentoForm
from .models import Documento

try:
    from core.admin import TenantAdminMixin
except Exception:

    class TenantAdminMixin:  # fallback no-op
        pass


@admin.register(Documento)
class DocumentoAdmin(TenantAdminMixin, admin.ModelAdmin):
    form = DocumentoForm
    list_display = (
        "id",
        "tipo",
        "numero",
        "estado",
        "fecha_emision",
        "cliente",
        "vehiculo",
        "pagado",
        "total",
    )
    list_filter = (
        "tipo",
        "estado",
        "pagado",
        "estado_pago",
        "moneda",
        "country",
        "fecha_emision",
    )
    search_fields = (
        "numero",
        "cliente__nombre",
        "cliente__apellido",
        "vehiculo__patente",
        "vehiculo__vin",
    )
    readonly_fields = (
        "empresa",
        "numero",
        "estado",
        "neto_repuestos",
        "neto_servicios",
        "tax_rate_applied",
        "tax_amount",
        "total",
    )
    autocomplete_fields = (
        "cliente",
        "vehiculo",
    )
    ordering = ("-fecha_emision", "-id")
    list_editable = ("pagado",)


# Registrar los modelos de líneas de documento
@admin.register(LineaRepuesto)
class LineaRepuestoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "documento",
        "codigo",
        "nombre",
        "cantidad",
        "precio_unitario",
        "descuento",
        "subtotal",
    )
    list_filter = ("documento__tipo", "documento__fecha")
    search_fields = ("codigo", "nombre", "documento__numero")
    raw_id_fields = ("documento", "repuesto")


@admin.register(LineaServicio)
class LineaServicioAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "documento",
        "codigo",
        "nombre",
        "cantidad",
        "precio_unitario",
        "descuento",
        "subtotal",
    )
    list_filter = ("documento__tipo", "documento__fecha")
    search_fields = ("codigo", "nombre", "documento__numero")
    raw_id_fields = ("documento", "servicio")


@admin.register(LineaOtroServicio)
class LineaOtroServicioAdmin(admin.ModelAdmin):
    list_display = ("id", "documento", "nombre", "precio_cliente")
    list_filter = ("documento__tipo", "documento__fecha")
    search_fields = ("nombre", "documento__numero")
    raw_id_fields = ("documento",)
