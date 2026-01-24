# -*- coding: utf-8 -*-
"""
Admin para modelos de ubicación

Registra:
- Address (direcciones)
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Admin para Address con filtros por país y empresa"""

    list_display = [
        "id",
        "line1_short",
        "city_display",
        "state_display",
        "country_display",
        "postal_code",
        "company_link",
        "sales_tax_display",
        "created_at",
    ]

    list_filter = [
        ("city__estado__pais", admin.ChoicesFieldListFilter),  # Filtro por país
        "company",  # Filtro por empresa
        "created_at",
    ]

    search_fields = [
        "line1",
        "line2",
        "postal_code",
        "city__nombre",
        "city__estado__nombre",
        "company__nombre_taller",
    ]

    raw_id_fields = ["city", "company"]  # Usar raw_id en lugar de autocomplete

    readonly_fields = [
        "created_at",
        "updated_at",
        "full_address_display",
        "sales_tax_display",
        "coordinates_display",
    ]

    fieldsets = (
        ("Dirección", {"fields": ("line1", "line2", "city", "postal_code")}),
        (
            "Empresa",
            {
                "fields": ("company",),
                "description": "Empresa propietaria de esta dirección (opcional)",
            },
        ),
        (
            "Coordenadas (Opcional)",
            {"fields": ("latitude", "longitude", "coordinates_display"), "classes": ("collapse",)},
        ),
        (
            "Información",
            {
                "fields": ("full_address_display", "sales_tax_display", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    # Custom display methods

    @admin.display(description="Dirección")
    def line1_short(self, obj):
        """Dirección línea 1 (truncada)"""
        return obj.line1[:50] + "..." if len(obj.line1) > 50 else obj.line1

    @admin.display(
        description="Ciudad",
        ordering="city__nombre",
    )
    def city_display(self, obj):
        """Ciudad"""
        return obj.city.nombre if obj.city else "-"

    @admin.display(description="Estado")
    def state_display(self, obj):
        """Estado/Departamento"""
        if obj.city and obj.city.estado:
            return f"{obj.city.estado.nombre} ({obj.city.estado.codigo})"
        return "-"

    @admin.display(description="País")
    def country_display(self, obj):
        """País con flag"""
        flags = {
            "CL": "🇨🇱",
            "US": "🇺🇸",
            "BR": "🇧🇷",
            "PE": "🇵🇪",
            "VE": "🇻🇪",
        }
        if obj.city and obj.city.estado:
            pais = obj.city.estado.pais
            flag = flags.get(pais, "")
            return format_html("{} <strong>{}</strong>", flag, pais)
        return "-"

    @admin.display(description="Empresa")
    def company_link(self, obj):
        """Link a empresa"""
        if obj.company:
            url = f"/admin/taller/empresa/{obj.company.pk}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.company.nombre_taller[:30])
        return "-"

    @admin.display(description="Sales Tax")
    def sales_tax_display(self, obj):
        """Sales tax desde el estado (si existe)"""
        try:
            if obj.city and obj.city.estado and hasattr(obj.city.estado, "sales_tax"):
                tax = float(obj.city.estado.sales_tax)
                return format_html('<span style="color: green;">{:.2f}%</span>', tax)
        except (AttributeError, ValueError, TypeError) as e:
            # Log error en desarrollo si es necesario
            pass
        return "-"

    @admin.display(description="Dirección Completa")
    def full_address_display(self, obj):
        """Dirección completa formateada"""
        return obj.full_address

    @admin.display(description="Coordenadas")
    def coordinates_display(self, obj):
        """Coordenadas con link a Google Maps"""
        if obj.latitude and obj.longitude:
            maps_url = f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"
            return format_html(
                '<a href="{}" target="_blank">📍 {}, {} (Ver en Maps)</a>',
                maps_url,
                obj.latitude,
                obj.longitude,
            )
        return "-"
