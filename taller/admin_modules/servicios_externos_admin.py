# -*- coding: utf-8 -*-
"""
Admin para Servicios Externos

Servicios efectuados por empresas externas que el taller subcontrata.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg, Sum

from taller.servicios.models import ServicioExterno


@admin.register(ServicioExterno)
class ServicioExternoAdmin(admin.ModelAdmin):
    """Admin para Servicios Externos (subcontratados)"""

    list_display = [
        "nombre",
        "empresa_externa_display",
        "categoria_display",
        "costo_taller_display",
        "precio_cliente_display",
        "ganancia_display",
        "margen_display",
        "activo_badge",
        "updated_at",
    ]

    list_filter = [
        "activo",
        "categoria",
        "subcategoria",
        "empresa_externa",
        "created_at",
    ]

    search_fields = [
        "nombre",
        "empresa_externa",
        "descripcion",
    ]

    readonly_fields = [
        "ganancia_display",
        "margen_display",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Información Básica",
            {"fields": ("nombre", "empresa_externa", "categoria", "subcategoria")},
        ),
        (
            "Precios",
            {
                "fields": ("costo_taller", "precio_cliente", "ganancia_display", "margen_display"),
                "description": "Costo para el taller y precio al cliente. La ganancia se calcula automáticamente.",
            },
        ),
        (
            "Detalles",
            {"fields": ("descripcion", "tiempo_estimado", "activo"), "classes": ("collapse",)},
        ),
        ("Auditoría", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    list_per_page = 50

    # === CUSTOM DISPLAY METHODS ===

    @admin.display(
        description="Empresa Externa",
        ordering="empresa_externa",
    )
    def empresa_externa_display(self, obj):
        """Empresa externa con badge"""
        return format_html(
            '<span style="background: #3b82f6; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 0.85em;">{}</span>',
            obj.empresa_externa,
        )

    @admin.display(
        description="Categoría",
        ordering="categoria__nombre",
    )
    def categoria_display(self, obj):
        """Categoría con subcategoría"""
        if obj.subcategoria:
            return f"{obj.categoria} → {obj.subcategoria}"
        return str(obj.categoria)

    @admin.display(
        description="Costo Taller",
        ordering="costo_taller",
    )
    def costo_taller_display(self, obj):
        """Costo para el taller (formateado)"""
        return format_html(
            '<span style="color: #dc2626; font-weight: 600;">${:,.0f}</span>', obj.costo_taller
        )

    @admin.display(
        description="Precio Cliente",
        ordering="precio_cliente",
    )
    def precio_cliente_display(self, obj):
        """Precio al cliente (formateado)"""
        return format_html(
            '<span style="color: #059669; font-weight: 600;">${:,.0f}</span>', obj.precio_cliente
        )

    @admin.display(description="Ganancia")
    def ganancia_display(self, obj):
        """Ganancia (calculada)"""
        ganancia = obj.ganancia
        color = "#059669" if ganancia > 0 else "#dc2626"
        return format_html(
            '<span style="color: {}; font-weight: 700; font-size: 1.1em;">${:,.0f}</span>',
            color,
            ganancia,
        )

    @admin.display(description="Margen %")
    def margen_display(self, obj):
        """Margen de ganancia en %"""
        margen = obj.margen_porcentaje

        # Color según margen
        if margen >= 30:
            color = "#059669"  # Verde
        elif margen >= 15:
            color = "#f59e0b"  # Amarillo
        else:
            color = "#dc2626"  # Rojo

        return format_html(
            '<span style="color: {}; font-weight: 600;">{:.1f}%</span>', color, margen
        )

    @admin.display(
        description="Estado",
        ordering="activo",
    )
    def activo_badge(self, obj):
        """Badge de estado activo/inactivo"""
        if obj.activo:
            return format_html(
                '<span style="background: #10b981; color: white; padding: 2px 10px; '
                'border-radius: 12px; font-size: 0.8em; font-weight: 600;">Activo</span>'
            )
        else:
            return format_html(
                '<span style="background: #6b7280; color: white; padding: 2px 10px; '
                'border-radius: 12px; font-size: 0.8em; font-weight: 600;">Inactivo</span>'
            )

    # === ACCIONES ===

    actions = ["activar_servicios", "desactivar_servicios", "calcular_estadisticas"]

    @admin.action(description="Activar servicios seleccionados")
    def activar_servicios(self, request, queryset):
        """Activar servicios seleccionados"""
        count = queryset.update(activo=True)
        self.message_user(request, f"{count} servicios activados.")

    @admin.action(description="Desactivar servicios seleccionados")
    def desactivar_servicios(self, request, queryset):
        """Desactivar servicios seleccionados"""
        count = queryset.update(activo=False)
        self.message_user(request, f"{count} servicios desactivados.")

    @admin.action(description="Calcular estadísticas")
    def calcular_estadisticas(self, request, queryset):
        """Mostrar estadísticas de servicios seleccionados"""
        stats = queryset.aggregate(
            total=Count("id"),
            avg_costo=Avg("costo_taller"),
            avg_precio=Avg("precio_cliente"),
            total_ganancia=Sum("precio_cliente") - Sum("costo_taller"),
        )

        self.message_user(
            request,
            f"Estadísticas: {stats['total']} servicios | "
            f"Costo promedio: ${stats['avg_costo']:,.0f} | "
            f"Precio promedio: ${stats['avg_precio']:,.0f}",
        )
