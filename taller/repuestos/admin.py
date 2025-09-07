from django.contrib import admin

from .models import Repuesto

try:
    from core.admin import TenantAdminMixin
except Exception:

    class TenantAdminMixin:
        pass


@admin.register(Repuesto)
class RepuestoAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("id", "part_number", "nombre", "categoria")
    list_filter = ("categoria",)
    search_fields = ("part_number", "nombre")
    autocomplete_fields = ("categoria",)
    ordering = ("nombre", "id")
    list_editable = ()
