from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from taller.models import CompanySettings, CompanySettingsHistory


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    """Administración de configuraciones de empresa"""

    list_display = [
        "user",
        "company_name",
        "display_logo",
        "has_custom_colors",
        "currency",
        "updated_at",
        "is_complete",
    ]

    list_filter = [
        "currency",
        "created_at",
        "updated_at",
    ]

    search_fields = ["user__username", "user__email", "company_name", "email", "tax_id"]

    readonly_fields = [
        "created_at",
        "updated_at",
        "display_logo_large",
        "color_preview",
    ]

    fieldsets = (
        ("Usuario", {"fields": ("user",)}),
        ("Información Básica", {"fields": ("company_name", "tagline")}),
        (
            "Branding Visual",
            {
                "fields": (
                    "logo",
                    "display_logo_large",
                    "primary_color",
                    "secondary_color",
                    "color_preview",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Datos de Contacto",
            {
                "fields": ("address", "phone", "email", "website"),
                "classes": ("collapse",),
            },
        ),
        (
            "Información Fiscal",
            {
                "fields": ("tax_id", "business_license", "currency"),
                "classes": ("collapse",),
            },
        ),
        (
            "Configuración de Documentos",
            {
                "fields": ("invoice_prefix", "quote_prefix", "work_order_prefix"),
                "classes": ("collapse",),
            },
        ),
        (
            "Información Adicional",
            {
                "fields": ("about_text", "terms_and_conditions"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    @admin.display(description="Logo")
    def display_logo(self, obj):
        """Muestra miniatura del logo en la lista"""
        if obj.logo:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; object-fit: contain; border-radius: 4px;" />',
                obj.logo.url,
            )
        return format_html('<span style="color: #999;">Sin logo</span>')

    @admin.display(description="Vista previa del logo")
    def display_logo_large(self, obj):
        """Muestra logo grande en el detalle"""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 100px; object-fit: contain; border: 1px solid #ddd; border-radius: 8px;" />',
                obj.logo.url,
            )
        return format_html('<span style="color: #999;">Sin logo cargado</span>')

    @admin.display(description="Colores")
    def color_preview(self, obj):
        """Muestra preview de los colores"""
        primary = obj.primary_color or "#0d6efd"
        secondary = obj.secondary_color or "#6c757d"

        return format_html(
            '<div style="display: flex; gap: 10px;">'
            '<div style="width: 40px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 4px;" title="Color primario: {}"></div>'
            '<div style="width: 40px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 4px;" title="Color secundario: {}"></div>'
            "</div>",
            primary,
            primary,
            secondary,
            secondary,
        )

    @admin.display(description="Colores")
    def has_custom_colors(self, obj):
        """Indica si tiene colores personalizados"""
        default_primary = "#0d6efd"
        default_secondary = "#6c757d"

        has_custom = (
            obj.primary_color != default_primary
            or obj.secondary_color != default_secondary
        )

        if has_custom:
            return format_html('<span style="color: green;">✓ Personalizado</span>')
        return format_html('<span style="color: #999;">Predeterminado</span>')

    @admin.display(description="Completitud")
    def is_complete(self, obj):
        """Indica si la configuración está completa"""
        score = 0
        total = 6

        if obj.company_name and obj.company_name != "eGarage":
            score += 1
        if obj.logo:
            score += 1
        if obj.address:
            score += 1
        if obj.phone:
            score += 1
        if obj.email:
            score += 1
        if obj.tax_id:
            score += 1

        percentage = (score / total) * 100

        if percentage >= 80:
            color = "green"
            icon = "✓"
        elif percentage >= 50:
            color = "orange"
            icon = "⚠"
        else:
            color = "red"
            icon = "✗"

        return format_html(
            '<span style="color: {};">{} {}%</span>', color, icon, int(percentage)
        )

    def get_queryset(self, request):
        """Optimiza consultas"""
        return super().get_queryset(request).select_related("user")

    actions = ["reset_to_defaults", "export_settings"]

    @admin.action(description="Resetear a valores por defecto")
    def reset_to_defaults(self, request, queryset):
        """Acción para resetear configuraciones"""
        for obj in queryset:
            obj.company_name = "eGarage"
            obj.primary_color = "#0d6efd"
            obj.secondary_color = "#6c757d"
            obj.tagline = ""
            if obj.logo:
                obj.logo.delete(save=False)
            obj.save()

        self.message_user(
            request, f"{queryset.count()} configuraciones reseteadas exitosamente."
        )

    @admin.action(description="Exportar configuraciones")
    def export_settings(self, request, queryset):
        """Acción para exportar configuraciones"""
        # Esta sería una funcionalidad más avanzada para exportar
        self.message_user(request, f"Exportando {queryset.count()} configuraciones...")


@admin.register(CompanySettingsHistory)
class CompanySettingsHistoryAdmin(admin.ModelAdmin):
    """Administración del historial de cambios"""

    list_display = [
        "company_settings",
        "field_changed",
        "changed_by",
        "changed_at",
        "preview_change",
    ]

    list_filter = ["field_changed", "changed_at", "company_settings__user"]

    search_fields = [
        "company_settings__company_name",
        "company_settings__user__username",
        "field_changed",
        "changed_by__username",
    ]

    readonly_fields = [
        "company_settings",
        "changed_by",
        "changed_at",
        "field_changed",
        "old_value",
        "new_value",
    ]

    date_hierarchy = "changed_at"

    @admin.display(description="Cambio")
    def preview_change(self, obj):
        """Muestra preview del cambio"""
        old_val = (
            obj.old_value[:30] + "..." if len(obj.old_value) > 30 else obj.old_value
        )
        new_val = (
            obj.new_value[:30] + "..." if len(obj.new_value) > 30 else obj.new_value
        )

        return format_html(
            '<span style="color: red;">{}</span> → <span style="color: green;">{}</span>',
            old_val or "(vacío)",
            new_val or "(vacío)",
        )

    def has_add_permission(self, request):
        """No permitir crear historiales manualmente"""
        return False

    def has_change_permission(self, request, obj=None):
        """Solo lectura para historiales"""
        return False

    def get_queryset(self, request):
        """Optimizar consultas"""
        return (
            super()
            .get_queryset(request)
            .select_related("company_settings__user", "changed_by")
        )
