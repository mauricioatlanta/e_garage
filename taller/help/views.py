"""
Vistas del Centro de Ayuda
"""

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView
from rest_framework.decorators import api_view
from rest_framework.response import Response

from taller.models.help import HelpArticle, HelpCategory
from .configs import FAQS, PASOS_RECOMENDADOS, PANEL_AYUDA_CONFIG


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
    }
    return render(request, "help/buscar.html", context)


@api_view(["GET"])
def help_contextual(request):
    """
    Retorna contenido de ayuda contextual basado en el contexto (módulo) enviado
    """
    contexto = request.GET.get("contexto", "general").lower()

    # Obtener FAQS y Pasos del config
    from .configs import FAQS, PASOS_RECOMENDADOS

    faqs = FAQS.get(contexto, FAQS.get("general", []))
    pasos = PASOS_RECOMENDADOS.get(contexto, [])

    return Response({"contexto": contexto, "faqs": faqs, "pasos": pasos, "success": True})


# API Views para contenido estático/extensible
@api_view(["GET"])
def api_faqs(request, modulo=None):
    """API para obtener FAQs por módulo o todas"""
    if modulo:
        faqs = FAQS.get(modulo, [])
    else:
        # Todas las FAQs agrupadas por módulo
        faqs = FAQS

    return Response({"faqs": faqs, "modulo": modulo})


@api_view(["GET"])
def api_pasos_recomendados(request, modulo=None):
    """API para obtener pasos recomendados por módulo"""
    if modulo:
        pasos = PASOS_RECOMENDADOS.get(modulo, [])
    else:
        pasos = PASOS_RECOMENDADOS

    return Response({"pasos": pasos, "modulo": modulo})


@api_view(["GET"])
def api_panel_ayuda_config(request):
    """API para configuración del panel de ayuda"""
    return Response(PANEL_AYUDA_CONFIG)
