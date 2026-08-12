from django import forms
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from commerce.models.cart import CommerceCart
from commerce.models.order import CommerceOrder
from commerce.services.cart_service import CartService
from commerce.services.order_service import OrderService


class CheckoutForm(forms.Form):
    name = forms.CharField(
        label="Nombre completo",
        max_length=120,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Tu nombre", "class": "form-input"}),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "correo@ejemplo.com", "class": "form-input"}),
    )
    phone = forms.CharField(
        label="Teléfono",
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "+56 9 1234 5678", "class": "form-input"}),
    )
    shipping_address = forms.CharField(
        label="Dirección de despacho",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Calle, número, ciudad, región", "class": "form-input"}),
    )
    notes = forms.CharField(
        label="Notas para el pedido",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Instrucciones especiales (opcional)", "class": "form-input"}),
    )


def _get_empresa_or_404(request):
    empresa = getattr(request, "empresa", None) or getattr(request, "commerce_empresa", None)
    if not empresa:
        raise Http404
    return empresa


@require_http_methods(["GET", "POST"])
def checkout_view(request):
    empresa = _get_empresa_or_404(request)
    session_key = request.session.session_key or ""
    if not session_key:
        return redirect("commerce:cart")

    try:
        cart = CommerceCart.objects.get(empresa=empresa, session_key=session_key)
    except CommerceCart.DoesNotExist:
        return redirect("commerce:cart")

    items = CartService.get_items(cart)
    total = CartService.total(cart)
    item_list = list(items)

    if not item_list:
        return redirect("commerce:cart")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = OrderService.create_from_cart(cart, {
                    "name": form.cleaned_data["name"],
                    "email": form.cleaned_data["email"],
                    "phone": form.cleaned_data["phone"],
                    "shipping_address": form.cleaned_data["shipping_address"],
                    "notes": form.cleaned_data["notes"],
                })
            except ValueError as exc:
                form.add_error(None, str(exc))
            else:
                return redirect("commerce:payment_select", order_number=order.order_number)
    else:
        form = CheckoutForm()

    return render(request, "commerce/themes/monteazul/cart/checkout.html", {
        "brand": request.commerce_brand,
        "form": form,
        "items": item_list,
        "total": total,
    })


def order_received(request, order_number):
    empresa = _get_empresa_or_404(request)
    order = get_object_or_404(
        CommerceOrder.objects.prefetch_related("items"),
        empresa=empresa,
        order_number=order_number,
    )
    return render(request, "commerce/order_received.html", {
        "brand": request.commerce_brand,
        "order": order,
    })
