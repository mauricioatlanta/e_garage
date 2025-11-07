from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from taller.models.pago import PagoPendiente


@admin.register(PagoPendiente)
class PagoPendienteAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'empresa_link',
        'plan_badge',
        'monto_formateado',
        'estado_badge',
        'fecha_subida',
        'comprobante_preview',
        'acciones',
    ]
    
    list_filter = ['estado', 'plan', 'fecha_subida', 'metodo_pago']
    search_fields = ['empresa__nombre_taller', 'empresa__email', 'referencia']
    readonly_fields = ['fecha_subida', 'comprobante_preview_large']
    
    fieldsets = (
        ('Información del Pago', {
            'fields': ('empresa', 'plan', 'monto', 'metodo_pago', 'referencia')
        }),
        ('Comprobante', {
            'fields': ('comprobante', 'comprobante_preview_large')
        }),
        ('Estado', {
            'fields': ('estado', 'notas', 'fecha_subida', 'fecha_verificacion', 'verificado_por')
        }),
    )
    
    def empresa_link(self, obj):
        url = reverse('admin:taller_empresa_change', args=[obj.empresa.id])
        return format_html(
            '<a href="{}">{}</a><br><small>{}</small>',
            url,
            obj.empresa.nombre_taller,
            obj.empresa.email
        )
    empresa_link.short_description = 'Empresa'
    
    def plan_badge(self, obj):
        colors = {
            'mensual': '#3b82f6',
            'semestral': '#10b981',
            'anual': '#8b5cf6',
        }
        color = colors.get(obj.plan, '#64748b')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-size: 12px; font-weight: 600;">{}</span>',
            color,
            obj.plan.upper()
        )
    plan_badge.short_description = 'Plan'
    
    def monto_formateado(self, obj):
        moneda = 'CLP' if obj.empresa.pais == 'CL' else 'USD'
        return format_html(
            '<strong style="font-size: 16px; color: #1a202c;">${:,.0f}</strong><br>'
            '<small style="color: #64748b;">{}</small>',
            obj.monto,
            moneda
        )
    monto_formateado.short_description = 'Monto'
    
    def estado_badge(self, obj):
        colors = {
            'pendiente': '#f59e0b',
            'verificado': '#3b82f6',
            'rechazado': '#ef4444',
            'procesado': '#10b981',
        }
        color = colors.get(obj.estado, '#64748b')
        
        icons = {
            'pendiente': '⏳',
            'verificado': '✓',
            'rechazado': '✗',
            'procesado': '✓✓',
        }
        icon = icons.get(obj.estado, '?')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 6px 12px; '
            'border-radius: 12px; font-size: 12px; font-weight: 600;">'
            '{} {}</span>',
            color,
            icon,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def comprobante_preview(self, obj):
        if obj.comprobante:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; '
                'border-radius: 8px; border: 2px solid #e2e8f0;"></a>',
                obj.comprobante.url,
                obj.comprobante.url
            )
        return '-'
    comprobante_preview.short_description = 'Vista Previa'
    
    def comprobante_preview_large(self, obj):
        if obj.comprobante:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width: 100%; max-height: 500px; '
                'border-radius: 12px; border: 2px solid #e2e8f0;"></a>',
                obj.comprobante.url,
                obj.comprobante.url
            )
        return '-'
    comprobante_preview_large.short_description = 'Comprobante'
    
    def acciones(self, obj):
        if obj.estado == 'pendiente':
            return format_html(
                '<a href="/admin/aprobar-pago/{}/" class="button" '
                'style="background: #10b981; color: white; padding: 8px 16px; '
                'border-radius: 6px; text-decoration: none; font-size: 12px; '
                'font-weight: 600;">✓ Aprobar</a> '
                '<a href="/admin/rechazar-pago/{}/" class="button" '
                'style="background: #ef4444; color: white; padding: 8px 16px; '
                'border-radius: 6px; text-decoration: none; font-size: 12px; '
                'font-weight: 600; margin-left: 8px;">✗ Rechazar</a>',
                obj.id,
                obj.id
            )
        return '-'
    acciones.short_description = 'Acciones Rápidas'
    
    def has_delete_permission(self, request, obj=None):
        # Solo superusuarios pueden eliminar
        return request.user.is_superuser

