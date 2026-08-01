from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from commerce.models.product import CommerceProduct
from commerce.services.cart_service import CartService


def _get_empresa_or_404(request):
    empresa = getattr(request, "empresa", None) or getattr(request, "commerce_empresa", None)
    if not empresa:
        raise Http404
    return empresa


def _ensure_session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _get_cart(request):
    empresa = _get_empresa_or_404(request)
    session_key = _ensure_session(request)
    return CartService.get_or_create(empresa, session_key)


def cart_detail(request):
    cart = _get_cart(request)
    items = CartService.get_items(cart)
    total = CartService.total(cart)
    return render(request, "commerce/themes/monteazul/cart/view.html", {
        "brand": request.commerce_brand,
        "cart": cart,
        "items": items,
        "total": total,
    })


@require_POST
def cart_add(request):
    empresa = _get_empresa_or_404(request)
    slug = request.POST.get("slug", "").strip()
    try:
        quantity = max(1, int(request.POST.get("quantity", 1)))
    except (ValueError, TypeError):
        quantity = 1

    product = get_object_or_404(
        CommerceProduct,
        empresa=empresa,
        slug=slug,
        is_publishable=True,
    )
    cart = _get_cart(request)
    CartService.add_item(cart, product, quantity)
    return redirect("commerce:cart")


@require_POST
def cart_update(request):
    empresa = _get_empresa_or_404(request)
    slug = request.POST.get("slug", "").strip()
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1

    product = get_object_or_404(CommerceProduct, empresa=empresa, slug=slug)
    cart = _get_cart(request)
    CartService.update_item(cart, product, quantity)
    return redirect("commerce:cart")


@require_POST
def cart_remove(request):
    empresa = _get_empresa_or_404(request)
    slug = request.POST.get("slug", "").strip()
    product = get_object_or_404(CommerceProduct, empresa=empresa, slug=slug)
    cart = _get_cart(request)
    CartService.remove_item(cart, product)
    return redirect("commerce:cart")
