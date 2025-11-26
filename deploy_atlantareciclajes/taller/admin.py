from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db import models
from django.utils import timezone
from django.utils.html import format_html

from taller.models.catalogo import CatalogoModeloAuto
from taller.models.clientes import Cliente
from taller.models.color_cliente import ColorCliente
from taller.models.comprobante_pago import ComprobantePago
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.perfil_usuario import PerfilUsuario
from taller.models.precio_suscripcion import PrecioSuscripcion
from taller.models.tecnico import Tecnico
from taller.servicios.models import (
    CategoriaServicio,
    CategoriaServicioName,
    Servicio,
    ServicioName,
    SubcategoriaServicio,
    SubcategoriaServicioName,
)

from .models import ConfiguracionEmpresa

# Importar admins de catálogo I18N (se auto-registran con @admin.register)
try:
    from taller.admin.catalogo_admin import *  # noqa: F401, F403
except ImportError:
    pass  # Admin de catálogo no disponible aún

# Importar admin de servicios externos (se auto-registra con @admin.register)
try:
    from taller.admin.servicios_externos_admin import *  # noqa: F401, F403
except ImportError:
    pass  # Admin de servicios externos no disponible aún


class MyAdminSite(AdminSite):
    site_header = "Panel de Administración de eGarage"
    site_title = "eGarage Admin"
    index_title = "Bienvenido al administrador"

    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser


admin_site = MyAdminSite(name="myadmin")


@admin.register(Empresa, site=admin_site)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_taller",
        "user",
        "estado_suscripcion_display",
        "dias_restantes_display",
        "fecha_fin",
        "plan",
    )
    list_filter = ("suscripcion_activa", "plan", "fecha_fin")
    search_fields = ("nombre_taller", "user__username", "user__email")
    readonly_fields = (
        "fecha_inicio",
        "dias_restantes_display",
        "estado_suscripcion_display",
    )

    fieldsets = (
        (
            "Información Básica",
            {
                "fields": (
                    "user",
                    "nombre_taller",
                    "empresa",
                    "email",
                    "telefono",
                    "direccion",
                    "logo",
                )
            },
        ),
        (
            "Suscripción",
            {
                "fields": (
                    "plan",
                    "suscripcion_activa",
                    "fecha_inicio",
                    "fecha_fin",
                    "dias_prueba",
                    "estado_suscripcion_display",
                    "dias_restantes_display",
                )
            },
        ),
        ("Pagos", {"fields": ("ultimo_pago", "valor_mensual", "moneda")}),
        (
            "Notificaciones",
            {
                "fields": (
                    "notificacion_5_dias",
                    "notificacion_1_dia",
                    "notificacion_vencido",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["extender_30_dias", "extender_60_dias", "marcar_como_pagado"]

    @admin.display(description="Estado")
    def estado_suscripcion_display(self, obj):
        estado = obj.estado_suscripcion
        colores = {
            "activa": "green",
            "advertencia": "orange",
            "critico": "red",
            "vencida": "gray",
        }
        color = colores.get(estado, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            estado.upper(),
        )

    @admin.display(description="Días Restantes")
    def dias_restantes_display(self, obj):
        dias = obj.dias_restantes
        if dias <= 0:
            return format_html('<span style="color: red; font-weight: bold;">VENCIDO</span>')
        elif dias <= 5:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{} días</span>', dias
            )
        else:
            return format_html('<span style="color: green;">{} días</span>', dias)

    @admin.action(description="Extender 30 días")
    def extender_30_dias(self, request, queryset):
        for empresa in queryset:
            empresa.extender_suscripcion(30)
        count = queryset.count()
        self.message_user(request, f"Se extendieron {count} suscripciones por 30 días.")

    @admin.action(description="Extender 60 días")
    def extender_60_dias(self, request, queryset):
        for empresa in queryset:
            empresa.extender_suscripcion(60)
        count = queryset.count()
        self.message_user(request, f"Se extendieron {count} suscripciones por 60 días.")

    @admin.action(description="Marcar como pagado (30 días)")
    def marcar_como_pagado(self, request, queryset):
        for empresa in queryset:
            empresa.marcar_pago_recibido()
        count = queryset.count()
        self.message_user(request, f"Se marcaron {count} empresas como pagadas.")

    def has_add_permission(self, request):
        """
        Solo permitir crear empresas si no existe ya una para el usuario
        """
        if not request.user.is_superuser:
            return False
        return super().has_add_permission(request)


@admin.register(PerfilUsuario, site=admin_site)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__username",)

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
    list_display = ("nombre", "apellido", "telefono", "empresa", "color_display")
    list_filter = ("empresa", "color__country", "color")
    search_fields = (
        "nombre",
        "apellido",
        "telefono",
        "email",
        "empresa__nombre_taller",
    )

    fieldsets = (
        (
            "Información Personal",
            {"fields": ("nombre", "apellido", "telefono", "email", "direccion")},
        ),
        ("Ubicación Chile", {"fields": ("region", "ciudad"), "classes": ("collapse",)}),
        (
            "Ubicación USA",
            {
                "fields": ("estado_usa", "ciudad_usa", "zipcode"),
                "classes": ("collapse",),
            },
        ),
        ("Identificación", {"fields": ("color", "tax_id")}),
        ("Empresa", {"fields": ("empresa",)}),
    )

    @admin.display(
        description="Color",
        ordering="color__nombre",
    )
    def color_display(self, obj):
        """Mostrar el color del cliente con preview visual"""
        if obj.color:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<div style="width: 20px; height: 20px; border-radius: 50%; background-color: {}; border: 2px solid #ccc;"></div>'
                "<span>{}</span>"
                "</div>",
                obj.color.codigo_color,
                obj.color.nombre,
            )
        return "Sin color"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs.select_related(
                "empresa", "color", "region", "ciudad", "estado_usa", "ciudad_usa"
            )
        return qs.filter(empresa__usuario_admin=request.user).select_related(
            "empresa", "color", "region", "ciudad", "estado_usa", "ciudad_usa"
        )


@admin.register(ColorCliente, site=admin_site)
class ColorClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "country", "codigo_color_display", "activo", "orden")
    list_filter = ("country", "activo")
    search_fields = ("nombre", "codigo_color")
    list_editable = ("activo", "orden")
    ordering = ("country", "orden", "nombre")

    fieldsets = (
        ("Información Básica", {"fields": ("nombre", "country", "activo", "orden")}),
        ("Color", {"fields": ("codigo_color",)}),
    )

    @admin.display(
        description="Preview del Color",
        ordering="codigo_color",
    )
    def codigo_color_display(self, obj):
        """Mostrar el código de color con preview visual"""
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<div style="width: 30px; height: 30px; border-radius: 50%; background-color: {}; border: 2px solid #ccc;"></div>'
            "<span>{}</span>"
            "</div>",
            obj.codigo_color,
            obj.codigo_color,
        )

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("country", "orden", "nombre")


@admin.register(Documento, site=admin_site)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tipo",
        "numero",
        "estado",
        "fecha_emision",
        "cliente",
        "vehiculo",
        "moneda",
        "total",
    )


@admin.register(Tecnico, site=admin_site)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "empresa")
    list_filter = ("empresa",)
    search_fields = ("nombre",)
    list_editable = ()


# === ADMINISTRACIÓN DE SERVICIOS MULTILENGUAJE ===


class CategoriaServicioNameInline(admin.TabularInline):
    model = CategoriaServicioName
    extra = 2
    fields = ["language", "label", "aliases", "is_default"]


@admin.register(CategoriaServicio, site=admin_site)
class CategoriaServicioAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "country", "get_label_es", "get_label_en")
    list_filter = ("country",)
    search_fields = ("code", "names__label")
    inlines = [CategoriaServicioNameInline]

    @admin.display(description="Nombre (ES)")
    def get_label_es(self, obj):
        return obj.get_label("es")

    @admin.display(description="Nombre (EN)")
    def get_label_en(self, obj):
        return obj.get_label("en")


class SubcategoriaServicioNameInline(admin.TabularInline):
    model = SubcategoriaServicioName
    extra = 2
    fields = ["language", "label", "aliases", "is_default"]


@admin.register(SubcategoriaServicio, site=admin_site)
class SubcategoriaServicioAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "country",
        "categoria",
        "get_label_es",
        "get_label_en",
    )
    list_filter = ("country", "categoria")
    search_fields = ("code", "names__label")
    inlines = [SubcategoriaServicioNameInline]

    @admin.display(description="Nombre (ES)")
    def get_label_es(self, obj):
        return obj.get_label("es")

    @admin.display(description="Nombre (EN)")
    def get_label_en(self, obj):
        return obj.get_label("en")


class ServicioNameInline(admin.TabularInline):
    model = ServicioName
    extra = 2
    fields = ["language", "label", "aliases", "is_default"]


@admin.register(Servicio, site=admin_site)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "categoria", "subcategoria")
    list_filter = ("categoria", "subcategoria")
    search_fields = ("nombre",)
    autocomplete_fields = ("categoria", "subcategoria")
    ordering = ("nombre", "id")
    list_editable = ()
    inlines = [ServicioNameInline]


@admin.register(ComprobantePago, site=admin_site)
class ComprobantePagoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "empresa",
        "monto_display",
        "estado_display",
        "fecha_subida",
        "plan_solicitado",
    )
    list_filter = ("estado", "metodo_pago", "plan_solicitado", "fecha_subida")
    search_fields = ("empresa__nombre_taller", "numero_transaccion", "banco_origen")
    readonly_fields = ("fecha_subida",)

    fieldsets = (
        (
            "Información del Pago",
            {
                "fields": (
                    "empresa",
                    "monto",
                    "moneda",
                    "plan_solicitado",
                    "metodo_pago",
                )
            },
        ),
        (
            "Detalles de la Transacción",
            {"fields": ("numero_transaccion", "comprobante", "descripcion")},
        ),
        (
            "Estado y Revisión",
            {"fields": ("estado", "fecha_procesado", "procesado_por", "notas_admin")},
        ),
        ("Sistema", {"fields": ("fecha_subida",), "classes": ("collapse",)}),
    )

    actions = ["aprobar_comprobantes", "rechazar_comprobantes"]

    @admin.display(description="Monto")
    def monto_display(self, obj):
        return f"${obj.monto:,.0f} {obj.moneda}"

    @admin.display(description="Estado")
    def estado_display(self, obj):
        colores = {"pendiente": "orange", "aprobado": "green", "rechazado": "red"}
        color = colores.get(obj.estado, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display(),
        )

    def aprobar_comprobantes(self, request, queryset):
        count = 0
        for comprobante in queryset.filter(estado="pendiente"):
            comprobante.estado = "aprobado"
            comprobante.fecha_procesado = timezone.now()
            comprobante.procesado_por = request.user.username
            comprobante.save()

            # Extender suscripción
            comprobante.empresa.marcar_pago_recibido(monto=comprobante.monto)
            count += 1
        self.message_user(request, f"Se aprobaron {count} comprobantes.")

    def rechazar_comprobantes(self, request, queryset):
        count = 0
        for comprobante in queryset.filter(estado="pendiente"):
            comprobante.estado = "rechazado"
            comprobante.fecha_procesado = timezone.now()
            comprobante.procesado_por = request.user.username
            comprobante.notas_admin = "Rechazado desde admin"
            comprobante.save()
            count += 1
        self.message_user(request, f"Se rechazaron {count} comprobantes.")


@admin.register(PrecioSuscripcion, site=admin_site)
class PrecioSuscripcionAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_plan",
        "tipo_plan",
        "pais_display",
        "precio_formateado",
        "activo",
        "caracteristicas_preview",
    )
    list_filter = ("pais", "tipo_plan", "activo", "moneda")
    search_fields = ("nombre_plan", "descripcion")
    ordering = ("pais", "tipo_plan")

    fieldsets = (
        (
            "Información Básica",
            {
                "fields": (
                    "nombre_plan",
                    "tipo_plan",
                    "pais",
                    "precio",
                    "moneda",
                    "activo",
                )
            },
        ),
        ("Descripción", {"fields": ("descripcion",)}),
        (
            "Características del Plan",
            {
                "fields": (
                    "documentos_ilimitados",
                    "usuarios_incluidos",
                    "soporte_prioritario",
                    "reportes_avanzados",
                    "diagnostico_ia",
                    "api_incluida",
                    "multisucursal",
                ),
                "classes": ("wide",),
            },
        ),
    )

    @admin.display(description="País")
    def pais_display(self, obj):
        flag = "🇨🇱" if obj.pais == "CL" else "🇺🇸"
        return f"{flag} {obj.get_pais_display()}"

    @admin.display(description="Características")
    def caracteristicas_preview(self, obj):
        caracteristicas = obj.caracteristicas_list()
        if len(caracteristicas) > 3:
            return f"{', '.join(caracteristicas[:3])}... (+{len(caracteristicas)-3} más)"
        return ", ".join(caracteristicas)

    actions = ["duplicar_para_otro_pais"]

    @admin.action(description="Duplicar para otro país")
    def duplicar_para_otro_pais(self, request, queryset):
        """Duplica precios para el otro país"""
        for precio in queryset:
            nuevo_pais = "US" if precio.pais == "CL" else "CL"
            # Calcular precio convertido (aproximado)
            if precio.pais == "CL" and nuevo_pais == "US":
                nuevo_precio = precio.precio / 1000  # Conversión aproximada CLP a USD
            else:
                nuevo_precio = precio.precio * 1000  # Conversión aproximada USD a CLP

            nueva_moneda = "USD" if nuevo_pais == "US" else "CLP"
            nuevo_nombre = precio.nombre_plan.replace(
                "Plan", "Monthly Plan" if nuevo_pais == "US" else "Plan"
            )

            PrecioSuscripcion.objects.get_or_create(
                tipo_plan=precio.tipo_plan,
                pais=nuevo_pais,
                defaults={
                    "precio": nuevo_precio,
                    "moneda": nueva_moneda,
                    "nombre_plan": nuevo_nombre,
                    "descripcion": precio.descripcion,
                    "documentos_ilimitados": precio.documentos_ilimitados,
                    "usuarios_incluidos": precio.usuarios_incluidos,
                    "soporte_prioritario": precio.soporte_prioritario,
                    "reportes_avanzados": precio.reportes_avanzados,
                    "diagnostico_ia": precio.diagnostico_ia,
                    "api_incluida": precio.api_incluida,
                    "multisucursal": precio.multisucursal,
                },
            )
        self.message_user(request, f"Duplicados {len(queryset)} precios para el otro país.")


@admin.register(CatalogoModeloAuto, site=admin_site)
class CatalogoModeloAutoAdmin(admin.ModelAdmin):
    """Administración del catálogo de marcas y modelos"""

    list_display = ("marca", "modelo", "activo", "fecha_creacion")
    list_filter = ("activo", "marca", "fecha_creacion")
    search_fields = ("marca", "modelo")
    list_editable = ("activo",)
    list_per_page = 50
    ordering = ("marca", "modelo")

    # Agrupación por marca en el formulario
    fieldsets = (
        ("Información del Vehículo", {"fields": ("marca", "modelo")}),
        ("Control", {"fields": ("activo",), "classes": ("collapse",)}),
    )

    # Filtros por sidebar
    list_filter = ("activo", "fecha_creacion")

    # Acciones personalizadas
    actions = [
        "activar_seleccionados",
        "desactivar_seleccionados",
        "estadisticas_marcas",
    ]

    @admin.action(description="Activar modelos seleccionados")
    def activar_seleccionados(self, request, queryset):
        count = queryset.update(activo=True)
        self.message_user(request, f"{count} modelos activados.")

    @admin.action(description="Desactivar modelos seleccionados")
    def desactivar_seleccionados(self, request, queryset):
        count = queryset.update(activo=False)
        self.message_user(request, f"{count} modelos desactivados.")

    @admin.action(description="Ver estadísticas de marcas")
    def estadisticas_marcas(self, request, queryset):
        from django.db.models import Count

        stats = (
            CatalogoModeloAuto.objects.values("marca")
            .annotate(total=Count("id"), activos=Count("id", filter=models.Q(activo=True)))
            .order_by("-total")[:10]
        )

        mensaje = "Top 10 marcas:\n" + "\n".join(
            [f"• {s['marca']}: {s['activos']}/{s['total']}" for s in stats]
        )
        self.message_user(request, mensaje)


@admin.register(ConfiguracionEmpresa, site=admin_site)
class ConfigEmpresaAdmin(admin.ModelAdmin):
    list_display = (
        "empresa",
        "nombre_publico",
        "moneda",
        "tasa_impuesto",
        "aplicar_impuesto_por_defecto",
        "dividir_por_tecnico",
    )
    list_filter = ("moneda", "aplicar_impuesto_por_defecto", "dividir_por_tecnico")
    search_fields = ("empresa__nombre", "nombre_publico")

    fieldsets = (
        (
            "Información Básica",
            {"fields": ("empresa", "nombre_publico", "tagline", "logo")},
        ),
        (
            "Información de Contacto",
            {"fields": ("direccion", "telefono", "email_contacto", "sitio_web")},
        ),
        (
            "Configuración Financiera",
            {"fields": ("moneda", "tasa_impuesto", "aplicar_impuesto_por_defecto")},
        ),
        ("Configuración Visual", {"fields": ("brand_color", "dividir_por_tecnico")}),
        (
            "Técnico por Defecto",
            {"fields": ("tecnico_por_defecto",), "classes": ("collapse",)},
        ),
    )

    def has_add_permission(self, request):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff
