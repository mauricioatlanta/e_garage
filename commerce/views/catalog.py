import datetime

from django.http import Http404, JsonResponse
from django.shortcuts import render

from commerce.services.gateway import CommerceCatalogGateway


def _gateway(request):
    empresa = getattr(request, "empresa", None) or getattr(request, "commerce_empresa", None)
    if not empresa:
        raise Http404
    return CommerceCatalogGateway(empresa)


def _empresa(request):
    return getattr(request, "empresa", None) or getattr(request, "commerce_empresa", None)


def _base_ctx(request, gw):
    """Contexto mínimo presente en todas las páginas del storefront."""
    root_cats = gw.get_categories()
    return {
        "empresa": _empresa(request),
        "brand": request.commerce_brand,
        "categories": root_cats,
        "root_categories": root_cats,
    }


def _vehicle_ctx(request):
    """Contexto para el selector de vehículo (años + marcas)."""
    from commerce.models import CommerceVehicleBrand
    empresa = _empresa(request)
    current_year = datetime.date.today().year
    years = list(range(current_year + 1, 1984, -1))
    brands = list(
        CommerceVehicleBrand.objects.filter(empresa=empresa).values("id", "name")
    ) if empresa else []
    return {"years": years, "brands": brands}


def catalog_home(request):
    gw = _gateway(request)
    ctx = _base_ctx(request, gw)
    ctx.update(_vehicle_ctx(request))
    ctx["featured"] = gw.list_products(limit=8)
    brand = ctx.get("brand") or {}
    ctx["title"] = brand.get("meta_title", "")
    ctx["meta_description"] = brand.get("meta_description", "")
    return render(request, "commerce/themes/monteazul/home.html", ctx)


def category_detail(request, slug):
    gw = _gateway(request)
    category = gw.get_category(slug)
    ctx = _base_ctx(request, gw)
    ctx.update({
        "category": category,
        "current_category": category,
        "subcategories": gw.get_categories(parent=category),
        "products": gw.list_products(category=category),
        "q": request.GET.get("q", ""),
        "is_cataliticos_subcat": False,
    })
    return render(request, "commerce/themes/monteazul/catalog/product_list.html", ctx)


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
    return render(request, "commerce/themes/monteazul/catalog/product_detail.html", ctx)


def search_view(request):
    gw = _gateway(request)
    query = request.GET.get("q", "").strip()
    ctx = _base_ctx(request, gw)
    ctx.update({
        "q": query,
        "products": gw.search(query),
        "current_category": None,
        "is_cataliticos_subcat": False,
    })
    return render(request, "commerce/themes/monteazul/catalog/product_list.html", ctx)


def api_vehicle_models(request):
    """GET /commerce/api/vehicle-models/?brand_id=<id>  →  {models: [{id, name}, ...]}"""
    from commerce.models import CommerceVehicleModel
    empresa = _empresa(request)
    if not empresa:
        return JsonResponse({"models": []})
    brand_id = request.GET.get("brand_id", "")
    qs = CommerceVehicleModel.objects.filter(empresa=empresa)
    if brand_id:
        qs = qs.filter(brand_id=brand_id)
    models = list(qs.values("id", "name").order_by("name"))
    return JsonResponse({"models": models})
