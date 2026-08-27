"""
taller/reciclaje/views_public.py — vistas públicas (sin login) del storefront
de un tenant RECYCLING sobre su dominio propio (ver taller/views/landing_views.py).

Reutiliza los modelos ya existentes en taller/models/reciclaje.py
(CategoriaChatarra, ProductoChatarra, Catalitico) — no crea modelos nuevos.
"""

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render

from taller.models.reciclaje import Catalitico, ProductoChatarra
from taller.reciclaje.views_staff import _reciclaje_url


def _empresa_publica(request):
    empresa = getattr(request, "empresa", None)
    if empresa is None:
        raise Http404
    return empresa


def landing_cataliticos(request):
    """Mini página de bienvenida de la sección Catalíticos, entre la
    bienvenida general del tenant y la consulta de precio por código."""
    _empresa_publica(request)
    return render(
        request,
        "taller/reciclaje/landing_cataliticos.html",
        {"dashboard_url": _reciclaje_url("")},
    )


def consulta_catalitico(request):
    """Consulta pública de precio de compra de un catalítico por código,
    marca o modelo. Nunca expone precio_compra — solo precio_venta."""
    empresa = _empresa_publica(request)
    codigo = request.GET.get("codigo", "").strip()
    resultados = []
    resultado = None
    sin_resultado = False

    if codigo:
        q = (
            Q(codigo__iexact=codigo)
            | Q(codigo__icontains=codigo)
            | Q(nombre__icontains=codigo)
            | Q(marca_vehiculo__icontains=codigo)
            | Q(modelo_vehiculo__icontains=codigo)
        )
        cataliticos = list(
            Catalitico.objects.filter(q, empresa=empresa, activo=True)
            .order_by("codigo")
            .distinct()
        )
        if cataliticos:
            resultados = cataliticos
            if len(resultados) == 1:
                resultado = resultados[0]
        else:
            sin_resultado = True

    return render(
        request,
        "taller/reciclaje/consulta_catalitico.html",
        {
            "codigo": codigo,
            "resultado": resultado,
            "resultados": resultados,
            "sin_resultado": sin_resultado,
        },
    )


def api_consulta_sugerencias(request):
    """API pública de autocomplete. GET term=... -> {"results": [...]}"""
    empresa = _empresa_publica(request)
    term = (request.GET.get("term") or request.GET.get("q") or "").strip()
    if not term or len(term) < 2:
        return JsonResponse({"results": []})

    q = Q(codigo__icontains=term) | Q(nombre__icontains=term)
    cataliticos = (
        Catalitico.objects.filter(q, empresa=empresa, activo=True)
        .order_by("codigo")
        .distinct()[:15]
    )
    results = [
        {
            "id": c.pk,
            "codigo": c.codigo,
            "nombre": c.nombre,
            "precio_referencia": float(c.precio_venta) if c.precio_venta else None,
        }
        for c in cataliticos
    ]
    return JsonResponse({"results": results})


def detalle_catalitico(request, pk):
    empresa = _empresa_publica(request)
    catalitico = get_object_or_404(
        Catalitico, pk=pk, empresa=empresa, activo=True
    )
    return render(
        request,
        "taller/reciclaje/detalle_catalitico.html",
        {"catalitico": catalitico},
    )


def catalogo_chatarra(request):
    empresa = _empresa_publica(request)
    productos = ProductoChatarra.objects.filter(
        empresa=empresa, activo=True
    ).order_by("nombre")
    paginator = Paginator(productos, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "taller/reciclaje/catalogo_chatarra.html",
        {"page_obj": page_obj},
    )
