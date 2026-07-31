from django.http import Http404
from django.shortcuts import render

from commerce.services.gateway import CommerceCatalogGateway


def _gateway(request):
    empresa = getattr(request, "commerce_empresa", None)
    if not empresa:
        raise Http404
    return CommerceCatalogGateway(empresa)


def catalog_home(request):
    gw = _gateway(request)
    return render(request, "commerce/home.html", {
        "categories": gw.get_categories(),
        "featured": gw.list_products(limit=8),
        "empresa": request.commerce_empresa,
    })


def category_detail(request, slug):
    gw = _gateway(request)
    category = gw.get_category(slug)
    return render(request, "commerce/category.html", {
        "category": category,
        "subcategories": gw.get_categories(parent=category),
        "products": gw.list_products(category=category),
        "empresa": request.commerce_empresa,
    })


def product_detail(request, slug):
    gw = _gateway(request)
    product = gw.get_product(slug)
    return render(request, "commerce/product.html", {
        "product": product,
        "images": product.images.all(),
        "related": gw.list_products(category=product.category, limit=4) if product.category else [],
        "empresa": request.commerce_empresa,
    })


def search_view(request):
    gw = _gateway(request)
    query = request.GET.get("q", "").strip()
    return render(request, "commerce/search.html", {
        "query": query,
        "results": gw.search(query),
        "empresa": request.commerce_empresa,
    })
