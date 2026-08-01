from django.http import Http404
from django.shortcuts import render

from commerce.services.gateway import CommerceCatalogGateway


def _gateway(request):
    empresa = getattr(request, "empresa", None) or getattr(request, "commerce_empresa", None)
    if not empresa:
        raise Http404
    return CommerceCatalogGateway(empresa)


def _base_ctx(request, gw):
    """Contexto mínimo presente en todas las páginas del storefront."""
    return {
        "empresa": getattr(request, "empresa", None) or getattr(request, "commerce_empresa", None),
        "brand": request.commerce_brand,
        "categories": gw.get_categories(),
    }


def catalog_home(request):
    gw = _gateway(request)
    ctx = _base_ctx(request, gw)
    ctx["featured"] = gw.list_products(limit=8)
    return render(request, "commerce/home.html", ctx)


def category_detail(request, slug):
    gw = _gateway(request)
    category = gw.get_category(slug)
    ctx = _base_ctx(request, gw)
    ctx.update({
        "category": category,
        "subcategories": gw.get_categories(parent=category),
        "products": gw.list_products(category=category),
    })
    return render(request, "commerce/category.html", ctx)


def product_detail(request, slug):
    gw = _gateway(request)
    product = gw.get_product(slug)
    ctx = _base_ctx(request, gw)
    ctx.update({
        "product": product,
        "images": product.images.all(),
        "related": (
            gw.list_products(category=product.category, limit=4, exclude_product=product)
            if product.category else []
        ),
    })
    return render(request, "commerce/product.html", ctx)


def search_view(request):
    gw = _gateway(request)
    query = request.GET.get("q", "").strip()
    ctx = _base_ctx(request, gw)
    ctx.update({
        "query": query,
        "results": gw.search(query),
    })
    return render(request, "commerce/search.html", ctx)
