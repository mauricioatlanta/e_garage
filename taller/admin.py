from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.mecanico import Mecanico
from taller.models.empresa import Empresa
from taller.models.perfil_usuario import PerfilUsuario
from taller.models.comprobante_pago import ComprobantePago
from taller.servicios.models import CategoriaServicio, SubcategoriaServicio  # y Servicio si aún existe

class MyAdminSite(AdminSite):
    site_header = 'Panel de Administración de eGarage'
    site_title = 'eGarage Admin'
    index_title = 'Bienvenido al administrador'

    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser

admin_site = MyAdminSite(name='myadmin')


@admin.register(Empresa, site=admin_site)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre_taller', 'user', 'estado_suscripcion_display', 'dias_restantes_display', 'fecha_fin', 'plan')
    list_filter = ('suscripcion_activa', 'plan', 'fecha_fin')
    search_fields = ('nombre_taller', 'user__username', 'user__email')
    readonly_fields = ('fecha_inicio', 'dias_restantes_display', 'estado_suscripcion_display')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'nombre_taller', 'empresa', 'email', 'telefono', 'direccion', 'logo')
        }),
        ('Suscripción', {
            'fields': ('plan', 'suscripcion_activa', 'fecha_inicio', 'fecha_fin', 'dias_prueba', 'estado_suscripcion_display', 'dias_restantes_display')
        }),
        ('Pagos', {
            'fields': ('ultimo_pago', 'valor_mensual', 'moneda')
        }),
        ('Notificaciones', {
            'fields': ('notificacion_5_dias', 'notificacion_1_dia', 'notificacion_vencido'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['extender_30_dias', 'extender_60_dias', 'marcar_como_pagado']
    
    def estado_suscripcion_display(self, obj):
        estado = obj.estado_suscripcion
        colores = {
            'activa': 'green',
            'advertencia': 'orange',
            'critico': 'red',
            'vencida': 'gray'
        }
        color = colores.get(estado, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            estado.upper()
        )
    estado_suscripcion_display.short_description = 'Estado'
    
    def dias_restantes_display(self, obj):
        dias = obj.dias_restantes
        if dias <= 0:
            return format_html('<span style="color: red; font-weight: bold;">VENCIDO</span>')
        elif dias <= 5:
            return format_html('<span style="color: orange; font-weight: bold;">{} días</span>', dias)
        else:
            return format_html('<span style="color: green;">{} días</span>', dias)
    dias_restantes_display.short_description = 'Días Restantes'
    
    def extender_30_dias(self, request, queryset):
        for empresa in queryset:
            empresa.extender_suscripcion(30)
        count = queryset.count()
        self.message_user(request, f'Se extendieron {count} suscripciones por 30 días.')
    extender_30_dias.short_description = 'Extender 30 días'
    
    def extender_60_dias(self, request, queryset):
        for empresa in queryset:
            empresa.extender_suscripcion(60)
        count = queryset.count()
        self.message_user(request, f'Se extendieron {count} suscripciones por 60 días.')
    extender_60_dias.short_description = 'Extender 60 días'
    
    def marcar_como_pagado(self, request, queryset):
        for empresa in queryset:
            empresa.marcar_pago_recibido()
        count = queryset.count()
        self.message_user(request, f'Se marcaron {count} empresas como pagadas.')
    marcar_como_pagado.short_description = 'Marcar como pagado (30 días)'
    
    def has_add_permission(self, request):
        """
        Solo permitir crear empresas si no existe ya una para el usuario
        """
        if not request.user.is_superuser:
            return False
        return super().has_add_permission(request)


@admin.register(PerfilUsuario, site=admin_site)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)
    
    def has_add_permission(self, request):
        """
        BLOQUEAR la creación de nuevos perfiles de usuario
        Mantener solo para visualización de datos existentes
        """
        return False
    
    def has_change_permission(self, request, obj=None):
        """
        Solo permitir ver, no editar
        """
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """
        Solo superusuarios pueden eliminar perfiles
        """
        return request.user.is_superuser


@admin.register(Cliente, site=admin_site)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'telefono', 'empresa')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa__usuario_admin=request.user)

@admin.register(Documento, site=admin_site)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('tipo_documento', 'numero_documento', 'cliente', 'vehiculo', 'fecha')

@admin.register(Mecanico, site=admin_site)
class MecanicoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'activo')
    list_filter = ('activo', 'empresa')
    search_fields = ('nombre',)
    list_editable = ('activo',)

@admin.register(CategoriaServicio, site=admin_site)
class CategoriaServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')

@admin.register(SubcategoriaServicio, site=admin_site)
class SubcategoriaServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'categoria')


@admin.register(ComprobantePago, site=admin_site)
class ComprobantePagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'empresa', 'monto_display', 'estado_display', 'fecha_subida', 'plan_solicitado')
    list_filter = ('estado', 'metodo_pago', 'plan_solicitado', 'fecha_subida')
    search_fields = ('empresa__nombre_taller', 'numero_transaccion', 'banco_origen')
    readonly_fields = ('fecha_subida',)
    
    fieldsets = (
        ('Información del Pago', {
            'fields': ('empresa', 'monto', 'moneda', 'plan_solicitado', 'metodo_pago')
        }),
        ('Detalles de la Transacción', {
            'fields': ('numero_transaccion', 'comprobante', 'descripcion')
        }),
        ('Estado y Revisión', {
            'fields': ('estado', 'fecha_procesado', 'procesado_por', 'notas_admin')
        }),
        ('Sistema', {
            'fields': ('fecha_subida',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['aprobar_comprobantes', 'rechazar_comprobantes']
    
    def monto_display(self, obj):
        return f"${obj.monto:,.0f} {obj.moneda}"
    monto_display.short_description = 'Monto'
    
    def estado_display(self, obj):
        colores = {
            'pendiente': 'orange',
            'aprobado': 'green',
            'rechazado': 'red'
        }
        color = colores.get(obj.estado, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'
    
    def aprobar_comprobantes(self, request, queryset):
        count = 0
        for comprobante in queryset.filter(estado='pendiente'):
            comprobante.estado = 'aprobado'
            comprobante.fecha_procesado = timezone.now()
            comprobante.procesado_por = request.user.username
            comprobante.save()
            
            # Extender suscripción
            comprobante.empresa.marcar_pago_recibido(monto=comprobante.monto)
            count += 1
        self.message_user(request, f'Se aprobaron {count} comprobantes.')
    
    def rechazar_comprobantes(self, request, queryset):
        count = 0
        for comprobante in queryset.filter(estado='pendiente'):
            comprobante.estado = 'rechazado'
            comprobante.fecha_procesado = timezone.now()
            comprobante.procesado_por = request.user.username
            comprobante.notas_admin = "Rechazado desde admin"
            comprobante.save()
            count += 1
        self.message_user(request, f'Se rechazaron {count} comprobantes.')

