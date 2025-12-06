"""
Vistas del Centro de Ayuda
"""

from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView

from taller.models.help import HelpArticle, HelpCategory


class HelpHomeView(ListView):
    """Página principal del Centro de Ayuda - Lista todas las categorías"""

    model = HelpCategory
    template_name = "help/home.html"
    context_object_name = "categorias"

    def get_queryset(self):
        return HelpCategory.objects.filter(activo=True).prefetch_related("articulos")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Artículos más visitados
        context["articulos_populares"] = HelpArticle.objects.filter(activo=True).order_by(
            "-visitas"
        )[:5]
        return context


class HelpCategoriaView(DetailView):
    """Vista de una categoría específica con sus artículos"""

    model = HelpCategory
    template_name = "help/categoria.html"
    context_object_name = "categoria"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return HelpCategory.objects.filter(activo=True).prefetch_related("articulos")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Artículos de la categoría ordenados
        context["articulos"] = self.object.articulos.filter(activo=True).order_by("orden", "titulo")
        return context


class HelpArticuloView(DetailView):
    """Vista de un artículo individual"""

    model = HelpArticle
    template_name = "help/articulo.html"
    context_object_name = "articulo"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return HelpArticle.objects.filter(activo=True).select_related("categoria")

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Incrementar contador de visitas
        self.object.incrementar_visitas()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Artículos relacionados de la misma categoría
        context["articulos_relacionados"] = (
            HelpArticle.objects.filter(categoria=self.object.categoria, activo=True)
            .exclude(pk=self.object.pk)
            .order_by("orden", "titulo")[:5]
        )
        return context


def help_buscar(request):
    """Buscador de artículos"""
    query = request.GET.get("q", "").strip()
    resultados = []

    if query:
        # Buscar en título y contenido
        resultados = (
            HelpArticle.objects.filter(
                Q(titulo__icontains=query) | Q(contenido__icontains=query), activo=True
            )
            .select_related("categoria")
            .order_by("-visitas", "titulo")
        )

    context = {
        "query": query,
        "resultados": resultados,
        "total": resultados.count() if query else 0,
    }

    return render(request, "help/buscar.html", context)



