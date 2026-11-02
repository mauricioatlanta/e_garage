# -*- coding: utf-8 -*-
"""
Admin para Catálogo de Repuestos y Servicios con I18N

Registra:
- Part, PartI18N, PartPrice
- Service, ServiceI18N, ServicePrice
- TaxPolicy
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q

from taller.models import Part, PartI18N, PartPrice, Service, ServiceI18N, ServicePrice, TaxPolicy


# === INLINES ===


class PartI18NInline(admin.TabularInline):
    """Inline para traducciones de repuestos"""

    model = PartI18N
    extra = 1
    fields = ["locale", "display_name", "synonyms"]


class PartPriceInline(admin.TabularInline):
    """Inline para precios de repuestos"""

    model = PartPrice
    extra = 1
    fields = ["company", "currency", "price", "valid_from", "valid_to", "tax_policy"]
    autocomplete_fields = ["company", "tax_policy"]


class ServiceI18NInline(admin.TabularInline):
    """Inline para traducciones de servicios"""

    model = ServiceI18N
    extra = 1
    fields = ["locale", "display_name", "synonyms"]


class ServicePriceInline(admin.TabularInline):
    """Inline para precios de servicios"""

    model = ServicePrice
    extra = 1
    fields = ["company", "currency", "price", "valid_from", "valid_to", "tax_policy"]
    autocomplete_fields = ["company", "tax_policy"]


# === ADMIN DE REPUESTOS ===


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    """Admin para Part (Repuestos)"""

    list_display = [
        "sku",
        "display_names",
        "category",
        "brand",
        "unit",
        "purchase_price_display",
        "stock_display",
        "empresa_display",
        "active",
        "created_at",
    ]

    list_filter = [
        "active",
        "category",
        "brand",
        "empresa",
        "created_at",
    ]

    search_fields = [
        "sku",
        "category",
        "brand",
        "i18n__display_name",  # Buscar en traducciones
        "i18n__synonyms",
    ]

    autocomplete_fields = ["empresa"]

    readonly_fields = ["created_at", "updated_at", "translations_count"]

    inlines = [PartI18NInline, PartPriceInline]

    fieldsets = (
        ("Identificación", {"fields": ("sku", "category", "brand", "empresa")}),
        ("Medidas", {"fields": ("unit", "weight_kg")}),
        ("Precios y Stock", {"fields": ("purchase_price", "stock_quantity", "stock_min")}),
        ("Estado", {"fields": ("active",)}),
        (
            "Metadata",
            {
                "fields": ("translations_count", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Nombres (I18N)")
    def display_names(self, obj):
        """Mostrar nombres en diferentes idiomas"""
        i18n = obj.i18n.all()[:3]  # Primeros 3
        if i18n:
            names = "<br>".join([f"<small>{i.locale}: {i.display_name[:30]}</small>" for i in i18n])
            count = obj.i18n.count()
            if count > 3:
                names += f"<br><small>... +{count - 3} más</small>"
            return format_html(names)
        return format_html('<em style="color: #999;">Sin traducciones</em>')

    @admin.display(
        description="Precio Compra",
        ordering="purchase_price",
    )
    def purchase_price_display(self, obj):
        """Precio de compra formateado"""
        if obj.purchase_price:
            return format_html("<strong>${:,.2f}</strong>", obj.purchase_price)
        return "-"

    @admin.display(
        description="Stock",
        ordering="stock_quantity",
    )
    def stock_display(self, obj):
        """Stock con alerta si está bajo"""
        if obj.stock_quantity <= obj.stock_min and obj.stock_min > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ {:.2f}</span>', obj.stock_quantity
            )
        return format_html("{:.2f}", obj.stock_quantity)

    @admin.display(description="Empresa")
    def empresa_display(self, obj):
        """Empresa o Global"""
        if obj.empresa:
            return obj.empresa.nombre_taller[:30]
        return format_html('<em style="color: #0066cc;">Global</em>')

    @admin.display(description="Traducciones")
    def translations_count(self, obj):
        """Cantidad de traducciones"""
        count = obj.i18n.count()
        return format_html("<strong>{}</strong> idiomas", count)

    def get_queryset(self, request):
        """Optimizar query con prefetch"""
        qs = super().get_queryset(request)
        return qs.prefetch_related("i18n", "prices").select_related("empresa")


@admin.register(PartI18N)
class PartI18NAdmin(admin.ModelAdmin):
    """Admin para PartI18N (Traducciones de Repuestos)"""

    list_display = ["part_sku", "locale", "display_name", "synonyms_short", "created_at"]
    list_filter = ["locale", "created_at"]
    search_fields = ["part__sku", "display_name", "synonyms"]
    autocomplete_fields = ["part"]

    @admin.display(
        description="SKU",
        ordering="part__sku",
    )
    def part_sku(self, obj):
        return obj.part.sku

    @admin.display(description="Sinónimos")
    def synonyms_short(self, obj):
        """Sinónimos (truncados)"""
        if obj.synonyms:
            return obj.synonyms[:50] + "..." if len(obj.synonyms) > 50 else obj.synonyms
        return "-"


@admin.register(PartPrice)
class PartPriceAdmin(admin.ModelAdmin):
    """Admin para PartPrice (Precios de Repuestos)"""

    list_display = [
        "part_sku",
        "company_name",
        "price_display",
        "currency",
        "valid_from",
        "valid_to",
        "is_valid_display",
        "tax_policy_display",
    ]

    list_filter = [
        "currency",
        "company",
        "valid_from",
        "tax_policy",
    ]

    search_fields = [
        "part__sku",
        "company__nombre_taller",
    ]

    autocomplete_fields = ["part", "company", "tax_policy"]

    date_hierarchy = "valid_from"

    @admin.display(
        description="SKU",
        ordering="part__sku",
    )
    def part_sku(self, obj):
        return obj.part.sku

    @admin.display(
        description="Empresa",
        ordering="company__nombre_taller",
    )
    def company_name(self, obj):
        return obj.company.nombre_taller[:30]

    @admin.display(
        description="Precio",
        ordering="price",
    )
    def price_display(self, obj):
        """Precio formateado"""
        return format_html("<strong>{:,.2f}</strong>", obj.price)

    @admin.display(description="Estado")
    def is_valid_display(self, obj):
        """Estado de validez"""
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ Vigente</span>')
        return format_html('<span style="color: red;">✗ Vencido/Futuro</span>')

    @admin.display(description="Tax Policy")
    def tax_policy_display(self, obj):
        """Política de impuestos"""
        if obj.tax_policy:
            return f"{obj.tax_policy.country} {obj.tax_policy.rate_percentage:.2f}%"
        return "-"


# === ADMIN DE SERVICIOS ===


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin para Service (Servicios de Catálogo)"""

    list_display = [
        "code",
        "display_names",
        "category",
        "std_hours",
        "empresa_display",
        "active",
        "created_at",
    ]

    list_filter = [
        "active",
        "category",
        "empresa",
        "created_at",
    ]

    search_fields = [
        "code",
        "category",
        "i18n__display_name",  # Buscar en traducciones
        "i18n__synonyms",
    ]

    autocomplete_fields = ["empresa"]

    readonly_fields = ["created_at", "updated_at", "translations_count"]

    inlines = [ServiceI18NInline, ServicePriceInline]

    fieldsets = (
        ("Identificación", {"fields": ("code", "category", "empresa")}),
        ("Configuración", {"fields": ("std_hours", "active")}),
        (
            "Metadata",
            {
                "fields": ("translations_count", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Nombres (I18N)")
    def display_names(self, obj):
        """Mostrar nombres en diferentes idiomas"""
        i18n = obj.i18n.all()[:3]
        if i18n:
            names = "<br>".join([f"<small>{i.locale}: {i.display_name[:30]}</small>" for i in i18n])
            count = obj.i18n.count()
            if count > 3:
                names += f"<br><small>... +{count - 3} más</small>"
            return format_html(names)
        return format_html('<em style="color: #999;">Sin traducciones</em>')

    @admin.display(description="Empresa")
    def empresa_display(self, obj):
        """Empresa o Global"""
        if obj.empresa:
            return obj.empresa.nombre_taller[:30]
        return format_html('<em style="color: #0066cc;">Global</em>')

    @admin.display(description="Traducciones")
    def translations_count(self, obj):
        """Cantidad de traducciones"""
        count = obj.i18n.count()
        return format_html("<strong>{}</strong> idiomas", count)

    def get_queryset(self, request):
        """Optimizar query"""
        qs = super().get_queryset(request)
        return qs.prefetch_related("i18n", "prices").select_related("empresa")


@admin.register(ServiceI18N)
class ServiceI18NAdmin(admin.ModelAdmin):
    """Admin para ServiceI18N (Traducciones de Servicios)"""

    list_display = ["service_code", "locale", "display_name", "synonyms_short", "created_at"]
    list_filter = ["locale", "created_at"]
    search_fields = ["service__code", "display_name", "synonyms"]
    autocomplete_fields = ["service"]

    @admin.display(
        description="Código",
        ordering="service__code",
    )
    def service_code(self, obj):
        return obj.service.code

    @admin.display(description="Sinónimos")
    def synonyms_short(self, obj):
        """Sinónimos (truncados)"""
        if obj.synonyms:
            return obj.synonyms[:50] + "..." if len(obj.synonyms) > 50 else obj.synonyms
        return "-"


@admin.register(ServicePrice)
class ServicePriceAdmin(admin.ModelAdmin):
    """Admin para ServicePrice (Precios de Servicios)"""

    list_display = [
        "service_code",
        "company_name",
        "price_display",
        "currency",
        "valid_from",
        "valid_to",
        "is_valid_display",
        "tax_policy_display",
    ]

    list_filter = [
        "currency",
        "company",
        "valid_from",
        "tax_policy",
    ]

    search_fields = [
        "service__code",
        "company__nombre_taller",
    ]

    autocomplete_fields = ["service", "company", "tax_policy"]

    date_hierarchy = "valid_from"

    @admin.display(
        description="Código",
        ordering="service__code",
    )
    def service_code(self, obj):
        return obj.service.code

    @admin.display(
        description="Empresa",
        ordering="company__nombre_taller",
    )
    def company_name(self, obj):
        return obj.company.nombre_taller[:30]

    @admin.display(
        description="Precio",
        ordering="price",
    )
    def price_display(self, obj):
        """Precio formateado"""
        return format_html("<strong>{:,.2f}</strong>", obj.price)

    @admin.display(description="Estado")
    def is_valid_display(self, obj):
        """Estado de validez"""
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ Vigente</span>')
        return format_html('<span style="color: red;">✗ Vencido/Futuro</span>')

    @admin.display(description="Tax Policy")
    def tax_policy_display(self, obj):
        """Política de impuestos"""
        if obj.tax_policy:
            return f"{obj.tax_policy.country} {obj.tax_policy.rate_percentage:.2f}%"
        return "-"


# === ADMIN DE TAX POLICY ===


@admin.register(TaxPolicy)
class TaxPolicyAdmin(admin.ModelAdmin):
    """Admin para TaxPolicy (Políticas de Impuestos)"""

    list_display = [
        "scope_display",
        "applies_to",
        "rate_display",
        "inclusive",
        "active",
        "usage_count",
        "created_at",
    ]

    list_filter = [
        "country",
        "applies_to",
        "inclusive",
        "active",
        "created_at",
    ]

    search_fields = [
        "country",
        "state_code",
        "city_name",
    ]

    readonly_fields = ["created_at", "updated_at", "usage_count", "rate_percentage_display"]

    fieldsets = (
        (
            "Ubicación",
            {
                "fields": ("country", "state_code", "city_name"),
                "description": "Especifica ubicación (más específico = mayor prioridad)",
            },
        ),
        (
            "Configuración",
            {"fields": ("applies_to", "rate", "rate_percentage_display", "inclusive", "active")},
        ),
        (
            "Estadísticas",
            {"fields": ("usage_count", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    @admin.display(description="Alcance")
    def scope_display(self, obj):
        """Alcance de la política"""
        flags = {
            "CL": "🇨🇱",
            "US": "🇺🇸",
            "BR": "🇧🇷",
            "PE": "🇵🇪",
            "VE": "🇻🇪",
        }

        scope = f"{flags.get(obj.country, '')} <strong>{obj.country}</strong>"

        if obj.state_code:
            scope += f" → {obj.state_code}"
        if obj.city_name:
            scope += f" → {obj.city_name}"

        return format_html(scope)

    @admin.display(
        description="Tasa",
        ordering="rate",
    )
    def rate_display(self, obj):
        """Tasa formateada"""
        percentage = obj.rate_percentage
        color = "#28a745" if obj.active else "#999"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}%</span>', color, percentage
        )

    @admin.display(description="Tasa (%)")
    def rate_percentage_display(self, obj):
        """Tasa como porcentaje (readonly)"""
        return f"{obj.rate_percentage:.4f}%"

    @admin.display(description="Uso")
    def usage_count(self, obj):
        """Cantidad de precios usando esta política"""
        part_prices = obj.partprice_set.count() if hasattr(obj, "partprice_set") else 0
        service_prices = obj.serviceprice_set.count() if hasattr(obj, "serviceprice_set") else 0
        total = part_prices + service_prices

        if total > 0:
            return format_html(
                "<strong>{}</strong> (Parts: {}, Services: {})", total, part_prices, service_prices
            )
        return format_html('<em style="color: #999;">No usado</em>')

    def get_queryset(self, request):
        """Optimizar con annotate"""
        qs = super().get_queryset(request)
        # Agregar count de uso si fuera necesario
        return qs


# === ACCIONES PERSONALIZADAS ===


@admin.action(description="Activar políticas seleccionadas")
def activar_policies(modeladmin, request, queryset):
    """Activar políticas de impuestos"""
    updated = queryset.update(active=True)
    modeladmin.message_user(request, f"{updated} política(s) activada(s)")


@admin.action(description="Desactivar políticas seleccionadas")
def desactivar_policies(modeladmin, request, queryset):
    """Desactivar políticas de impuestos"""
    updated = queryset.update(active=False)
    modeladmin.message_user(request, f"{updated} política(s) desactivada(s)")


# Agregar acciones a TaxPolicyAdmin
TaxPolicyAdmin.actions = [activar_policies, desactivar_policies]


@admin.action(description="Marcar como activo")
def activar_parts(modeladmin, request, queryset):
    """Activar repuestos"""
    updated = queryset.update(active=True)
    modeladmin.message_user(request, f"{updated} repuesto(s) activado(s)")


@admin.action(description="Marcar como inactivo")
def desactivar_parts(modeladmin, request, queryset):
    """Desactivar repuestos"""
    updated = queryset.update(active=False)
    modeladmin.message_user(request, f"{updated} repuesto(s) desactivado(s)")


# Agregar acciones a PartAdmin
PartAdmin.actions = [activar_parts, desactivar_parts]
ServiceAdmin.actions = [activar_parts, desactivar_parts]  # Reutilizar para servicios
