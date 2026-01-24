"""
Admin para modelos de memoria y seguimiento
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from taller.models.memoria_seguimiento import (
    EtiquetaAsignacion,
    EtiquetaInterna,
    EvidenciaDocumento,
    NotaInterna,
    SeguimientoPublico,
)


@admin.register(NotaInterna)
class NotaInternaAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo_coloreado", "empresa", "documento", "cliente", "vehiculo", "solo_staff", "created_at")
    list_filter = ("tipo", "solo_staff", "created_at", "empresa")
    search_fields = ("contenido", "empresa__nombre_taller")
    readonly_fields = ("created_at", "updated_at")
    
    def tipo_coloreado(self, obj):
        """Muestra el tipo de nota con color: Rojo para Alerta, Amarillo para Preferencia"""
        if obj.tipo == "ALERTA":
            color = "#EF4444"  # Rojo
            icono = "⚠️"
        else:  # PREFERENCIA
            color = "#F59E0B"  # Amarillo/Naranja
            icono = "📌"
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icono,
            obj.get_tipo_display(),
        )
    tipo_coloreado.short_description = _("Tipo")
    tipo_coloreado.admin_order_field = "tipo"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Multi-tenant: filtrar por empresa del usuario
        if hasattr(request.user, "empresa"):
            return qs.filter(empresa=request.user.empresa)
        return qs.none()


@admin.register(EtiquetaInterna)
class EtiquetaInternaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "empresa", "color", "solo_staff", "created_at")
    list_filter = ("solo_staff", "empresa")
    search_fields = ("nombre", "empresa__nombre_taller")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Multi-tenant: filtrar por empresa del usuario
        if hasattr(request.user, "empresa"):
            return qs.filter(empresa=request.user.empresa)
        return qs.none()


@admin.register(EtiquetaAsignacion)
class EtiquetaAsignacionAdmin(admin.ModelAdmin):
    list_display = ("etiqueta", "documento", "cliente", "vehiculo", "empresa", "created_at")
    list_filter = ("empresa", "created_at")
    search_fields = ("etiqueta__nombre", "empresa__nombre_taller")
    readonly_fields = ("created_at",)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Multi-tenant: filtrar por empresa del usuario
        if hasattr(request.user, "empresa"):
            return qs.filter(empresa=request.user.empresa)
        return qs.none()


@admin.register(EvidenciaDocumento)
class EvidenciaDocumentoAdmin(admin.ModelAdmin):
    list_display = ("id", "documento", "tipo", "compartible", "empresa", "created_at")
    list_filter = ("tipo", "compartible", "empresa", "created_at")
    search_fields = ("documento__numero", "descripcion", "empresa__nombre_taller")
    readonly_fields = ("created_at", "updated_at")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Multi-tenant: filtrar por empresa del usuario
        if hasattr(request.user, "empresa"):
            return qs.filter(empresa=request.user.empresa)
        return qs.none()

    def has_delete_permission(self, request, obj=None):
        """
        Solo staff/admin puede borrar evidencias.
        Los técnicos no pueden borrar (para mantener respaldo).
        """
        # Superuser siempre puede
        if request.user.is_superuser:
            return True
        
        # Solo staff (Owner/Admin) puede borrar
        from taller.auth.decorators_role import is_staff_member
        return is_staff_member(request.user)


@admin.register(SeguimientoPublico)
class SeguimientoPublicoAdmin(admin.ModelAdmin):
    list_display = ("documento", "token_short", "activo", "empresa", "created_at")
    list_filter = ("activo", "empresa", "created_at")
    search_fields = ("documento__numero", "token", "empresa__nombre_taller")
    readonly_fields = ("token", "created_at", "updated_at")
    
    def token_short(self, obj):
        return f"{obj.token[:16]}..." if obj.token else "-"
    token_short.short_description = _("Token")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Multi-tenant: filtrar por empresa del usuario
        if hasattr(request.user, "empresa"):
            return qs.filter(empresa=request.user.empresa)
        return qs.none()
