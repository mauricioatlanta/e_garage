"""
Vistas del flujo de pagos Commerce — H3.

Principio: las vistas son deliberadamente delgadas.
Reciben el request, delegan en CommercePaymentService, redirigen o renderizan.
No contienen lógica de dominio ni llaman al SDK de Transbank directamente.
"""
from __future__ import annotations

import logging

from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods

from commerce.models.order import CommerceOrder
from commerce.models.payment import PaymentAttempt
from commerce.services.payment_service import (
    CommercePaymentService,
    PaymentAlreadyAuthorizedError,
    PaymentAttemptNotFoundError,
)

logger = logging.getLogger(__name__)

_ALLOWED_GATEWAYS = frozenset({"webpay", "bank_transfer"})


def _get_empresa_or_404(request):
    empresa = getattr(request, "empresa", None) or getattr(request, "commerce_empresa", None)
    if not empresa:
        raise Http404
    return empresa


@require_POST
def payment_start(request, order_number):
    """
    Inicia el flujo de pago para un pedido existente.

    Delega en CommercePaymentService.initiate() y renderiza la plantilla
    apropiada según el gateway elegido (redirect a Transbank o instrucciones
    de transferencia). Sin lógica de dominio aquí.
    """
    empresa = _get_empresa_or_404(request)
    order = get_object_or_404(CommerceOrder, empresa=empresa, order_number=order_number)

    # Aislamiento por sesión: solo el creador del pedido puede iniciar el pago
    session_key = request.session.session_key or ""
    if order.session_key and order.session_key != session_key:
        raise Http404

    if order.status == CommerceOrder.CANCELLED:
        raise Http404

    if order.payment_status == CommerceOrder.PAYMENT_PAID:
        return redirect("commerce:order_received", order_number=order_number)

    gateway_key = request.POST.get("gateway_key", "").strip()
    if gateway_key not in _ALLOWED_GATEWAYS:
        return HttpResponseBadRequest("Método de pago inválido.")

    return_url = request.build_absolute_uri(reverse("commerce:payment_return"))

    try:
        initiation = CommercePaymentService.initiate(order, gateway_key, return_url)
    except PaymentAlreadyAuthorizedError:
        return redirect("commerce:order_received", order_number=order_number)

    if gateway_key == "bank_transfer":
        return render(request, "commerce/payments/bank_transfer_instructions.html", {
            "brand": request.commerce_brand,
            "order": order,
            "gateway_token": initiation.gateway_token,
        })

    return render(request, "commerce/payments/redirect.html", {
        "brand": request.commerce_brand,
        "order": order,
        "redirect_url": initiation.redirect_url,
        "gateway_token": initiation.gateway_token,
    })


@csrf_exempt
@require_POST
def payment_return(request):
    """
    Punto de retorno de Transbank (csrf_exempt porque Transbank envía un POST externo).

    Busca el intento por gateway_token, valida el tenant, llama a confirm()
    y redirige según el resultado. No importa el SDK de Transbank.
    """
    empresa = _get_empresa_or_404(request)

    token_ws = request.POST.get("token_ws", "").strip()
    if not token_ws:
        return render(request, "commerce/payments/cancelled.html", {
            "brand": request.commerce_brand,
            "order": None,
        }, status=200)

    attempt = (
        PaymentAttempt.objects
        .filter(gateway_token=token_ws)
        .select_related("order__empresa")
        .first()
    )
    if attempt is None or attempt.order.empresa_id != empresa.pk:
        raise Http404

    order = attempt.order

    if order.payment_status == CommerceOrder.PAYMENT_PAID:
        return redirect("commerce:order_received", order_number=order.order_number)

    try:
        success = CommercePaymentService.confirm(order, token_ws)
    except PaymentAlreadyAuthorizedError:
        return redirect("commerce:order_received", order_number=order.order_number)
    except PaymentAttemptNotFoundError:
        raise Http404
    except Exception:
        logger.exception(
            "payment_return: error inesperado confirmando pago para pedido %s",
            order.order_number,
        )
        return render(request, "commerce/payments/failed.html", {
            "brand": request.commerce_brand,
            "order": order,
        }, status=502)

    if success:
        return redirect("commerce:order_received", order_number=order.order_number)

    return render(request, "commerce/payments/failed.html", {
        "brand": request.commerce_brand,
        "order": order,
    })


@require_http_methods(["GET"])
def payment_cancel(request, order_number):
    """
    Muestra pantalla de cancelación. No modifica ningún PaymentAttempt ni
    el estado logístico del pedido — el cliente puede reintentar desde order_received.
    """
    empresa = _get_empresa_or_404(request)
    order = get_object_or_404(CommerceOrder, empresa=empresa, order_number=order_number)

    session_key = request.session.session_key or ""
    if order.session_key and order.session_key != session_key:
        raise Http404

    return render(request, "commerce/payments/cancelled.html", {
        "brand": request.commerce_brand,
        "order": order,
    })
