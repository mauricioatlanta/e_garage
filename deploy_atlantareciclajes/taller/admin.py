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

from taller.models import (
    ConfiguracionEmpresa,
    Service,
    ServiceI18N,
    ServicePrice,
)

# Importar admins de catálogo I18N
try:
    from taller.admin.catalogo_admin import *  # noqa: F401, F403
except ImportError:
    pass

# Importar admin de servicios externos
try:
    from taller.admin.servicios_externos_admin import *  # noqa: F401, F403
except ImportError:
    pass


class MyAdminSite(AdminSite):
    site_header = "Panel de Administración de eGarage"
    site_title = "eGarage Admin"
    index_title = "Bienvenido al administrador"

    def has_permission(self, request):
        return request.user.is_staff and request.user.is_superuser


admin_site = MyAdminSite(name="myadmin")


@admin.register(Empresa, site=admin_site)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("nombre_taller", "user", "plan", "fecha_fin")
    list_filter = ("suscripcion_activa", "plan", "fecha_fin")
    search_fields = ("nombre_taller", "user__username", "user__email")
    readonly_fields = ("fecha_inicio",)


@admin.register(PerfilUsuario, site=admin_site)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user",)


@admin.register(Cliente, site=admin_site)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellido", "telefono", "empresa")


@admin.register(Tecnico, site=admin_site)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "empresa")


@admin.register(Service, site=admin_site)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("id",)


@admin.register(ConfiguracionEmpresa, site=admin_site)
class ConfigEmpresaAdmin(admin.ModelAdmin):
    list_display = ("empresa", "nombre_publico")
