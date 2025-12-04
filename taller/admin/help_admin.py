"""
Admin para el Centro de Ayuda
"""

from django.contrib import admin
from django.utils.html import format_html

from taller.models.help import HelpArticle, HelpCategory


@admin.register(HelpCategory)
class HelpCategoryAdmin(admin.ModelAdmin):
    list_display = ["nombre", "icono", "orden", "activo", "articulos_count", "creado"]
    list_filter = ["activo", "creado"]
    search_fields = ["nombre", "descripcion"]
    prepopulated_fields = {"slug": ("nombre",)}
    ordering = ["orden", "nombre"]

    @admin.display(description="Artículos Activos")
    def articulos_count(self, obj):
        """Muestra el número de artículos en la categoría"""
        count = obj.articulos.filter(activo=True).count()
        return format_html('<span style="color: #4CAF50;">{}</span>', count)


@admin.register(HelpArticle)
class HelpArticleAdmin(admin.ModelAdmin):
    list_display = ["titulo", "categoria", "orden", "activo", "visitas", "creado", "actualizado"]
    list_filter = ["categoria", "activo", "creado"]
    search_fields = ["titulo", "contenido"]
    prepopulated_fields = {"slug": ("titulo",)}
    ordering = ["categoria", "orden", "titulo"]
    raw_id_fields = ["categoria"]

    fieldsets = (
        ("Información Básica", {"fields": ("categoria", "titulo", "slug", "orden", "activo")}),
        ("Contenido", {"fields": ("contenido",)}),
        ("Estadísticas", {"fields": ("visitas",), "classes": ("collapse",)}),
        ("Fechas", {"fields": ("creado", "actualizado"), "classes": ("collapse",)}),
    )

    readonly_fields = ["creado", "actualizado", "visitas"]
