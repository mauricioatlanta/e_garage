from django.contrib import admin

from .models import CasaRepuestos, ProductoCatalogo, WhatsAppEnvio


@admin.register(CasaRepuestos)
class CasaRepuestosAdmin(admin.ModelAdmin):
    list_display = ("nombre", "contacto", "telefono", "email", "activa", "empresa")
    list_filter = ("activa", "empresa")
    search_fields = ("nombre", "contacto", "telefono", "email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ProductoCatalogo)
class ProductoCatalogoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "part_number",
        "casa_repuestos",
        "precio_referencia",
        "disponible",
        "activo",
        "empresa",
    )
    list_filter = ("activo", "disponible", "casa_repuestos", "empresa")
    search_fields = ("nombre", "part_number", "casa_repuestos__nombre")
    readonly_fields = ("ultima_actualizacion_precio", "created_at", "updated_at")
    fieldsets = (
        (
            "Información Básica",
            {
                "fields": (
                    "empresa",
                    "casa_repuestos",
                    "part_number",
                    "nombre",
                )
            },
        ),
        (
            "Precios (No visible para cliente)",
            {
                "fields": (
                    "precio_referencia",
                    "precio_compra_minimo",
                ),
                "description": "Estos precios son solo de referencia para el taller y NO se muestran al cliente final.",
            },
        ),
        (
            "Estado",
            {
                "fields": ("activo", "disponible", "observaciones"),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "ultima_actualizacion_precio",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(WhatsAppEnvio)
class WhatsAppEnvioAdmin(admin.ModelAdmin):
    list_display = ("tipo_envio", "telefono_destino", "empresa", "fecha_envio", "exito")
    list_filter = ("tipo_envio", "exito", "fecha_envio", "empresa")
    search_fields = ("telefono_destino", "mensaje_id", "empresa__nombre_taller")
    readonly_fields = ("fecha_envio",)
    date_hierarchy = "fecha_envio"
