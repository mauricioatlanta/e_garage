from django.contrib import admin

from .models import Servicio

try:
    from core.admin import TenantAdminMixin
except Exception:

    class TenantAdminMixin:
        pass


@admin.register(Servicio)
class ServicioAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("id", "nombre", "categoria", "subcategoria")
    list_filter = ("categoria", "subcategoria")
    search_fields = ("nombre",)
    autocomplete_fields = ("categoria", "subcategoria")
    ordering = ("nombre", "id")
    list_editable = ()
