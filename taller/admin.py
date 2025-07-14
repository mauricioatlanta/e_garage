from django.contrib import admin
from django.contrib.admin import AdminSite
from taller.models.documento import Documento
from taller.servicios.models import CategoriaServicio, SubcategoriaServicio  # y Servicio si aún existe

class MyAdminSite(AdminSite):
    site_header = 'Panel de Administración de eGarage'
    site_title = 'eGarage Admin'
    index_title = 'Bienvenido al administrador'

    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser

admin_site = MyAdminSite(name='myadmin')

@admin.register(Documento, site=admin_site)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('tipo_documento', 'numero_documento', 'cliente', 'vehiculo', 'fecha')

@admin.register(CategoriaServicio, site=admin_site)
class CategoriaServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')

@admin.register(SubcategoriaServicio, site=admin_site)
class SubcategoriaServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'categoria')

