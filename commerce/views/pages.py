from django.http import Http404
from django.shortcuts import get_object_or_404, render

from commerce.models import CommerceFAQ, CommerceStaticPage
from commerce.services.gateway import CommerceCatalogGateway


def _require_empresa(request):
    empresa = getattr(request, "empresa", None) or getattr(request, "commerce_empresa", None)
    if not empresa:
        raise Http404
    return empresa


def _base_ctx(request):
    empresa = _require_empresa(request)
    gw = CommerceCatalogGateway(empresa)
    return {
        "empresa": empresa,
        "brand": request.commerce_brand,
        "categories": gw.get_categories(),
    }


def static_page_detail(request, slug):
    empresa = _require_empresa(request)
    page = get_object_or_404(
        CommerceStaticPage,
        empresa=empresa,
        slug=slug,
        is_active=True,
    )
    ctx = _base_ctx(request)
    ctx["page"] = page

    if page.key == "faq":
        ctx["faqs"] = (
            CommerceFAQ.objects
            .filter(empresa=empresa, page=page, is_active=True)
            .order_by("position")
        )
        return render(request, "commerce/faq.html", ctx)

    return render(request, "commerce/static_page.html", ctx)
