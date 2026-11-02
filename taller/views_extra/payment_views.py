import logging
import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods

from taller.models.empresa import Empresa
from taller.services.suscripcion_transaccion_service import (
    approve_transaction,
    create_gateway_transaction,
    mark_transaction_pending,
    reject_transaction,
)
from taller.utils.flow_helper import FlowAPIError, create_payment_order, get_payment_status
from taller.utils.mp_helper import MPAPIError, create_mp_preference, get_mp_payment
from taller.utils.payment_config import get_paypal_business_email, get_transfer_payment_details
from taller.utils.plan_catalog import (
    BILLING_ANNUAL,
    BILLING_MONTHLY,
    PAYMENT_METHOD_BANK_TRANSFER,
    PAYMENT_METHOD_FLOW,
    PAYMENT_METHOD_MERCADOPAGO,
    PAYMENT_METHOD_PAYPAL,
    PLAN_TRIAL,
    PLAN_ENTRY,
    PLAN_GROWTH,
    PLAN_BUSINESS,
    get_plan_display_name,
    get_plan_price,
    get_supported_payment_methods,
    normalize_billing_cycle,
    normalize_plan_code,
)


logger = logging.getLogger(__name__)

CHILE_PAYMENT_PRICING = {
    "individual_mensual": {"valor": 20000, "dias": 30, "nombre": "Individual Mensual (1 Usu)"},
    "individual_anual": {"valor": 200000, "dias": 365, "nombre": "Individual Anual (1 Usu)"},
    "equipo_mensual": {"valor": 35000, "dias": 30, "nombre": "Equipo Mensual (2-5 Usu)"},
    "equipo_anual": {"valor": 350000, "dias": 365, "nombre": "Equipo Anual (2-5 Usu)"},
    "empresa_mensual": {"valor": 50000, "dias": 30, "nombre": "Corporativo Mensual (6-10 Usu)"},
    "empresa_anual": {"valor": 500000, "dias": 365, "nombre": "Corporativo Anual (6-10 Usu)"},
}

MEXICO_PAYMENT_PRICING = {
    "mensual": {"valor": 399, "dias": 30, "nombre": "Mensual"},
    "semestral": {"valor": 2199, "dias": 180, "nombre": "Semestral"},
    "anual": {"valor": 3990, "dias": 365, "nombre": "Anual"},
}

USA_PAYMENT_PRICING = {
    "mensual": {"valor": "20.00", "dias": 30, "nombre": "Monthly"},
    "semestral": {"valor": "110.00", "dias": 180, "nombre": "Semi-Annual"},
    "anual": {"valor": "200.00", "dias": 365, "nombre": "Annual"},
}


def _flow_is_enabled():
    return bool(
        getattr(settings, "FLOW_ENABLED", False)
        and (getattr(settings, "FLOW_API_KEY", "") or "").strip()
        and (getattr(settings, "FLOW_SECRET_KEY", "") or "").strip()
        and (getattr(settings, "FLOW_API_URL", "") or "").strip()
    )


def _mp_is_enabled():
    return bool(
        getattr(settings, "MP_ENABLED", False)
        and (getattr(settings, "MP_ACCESS_TOKEN", "") or "").strip()
    )


def _plan_context_for_country(country, raw_plan, lang="es"):
    raw_plan = (raw_plan or "").strip().lower() or "mensual"
    plan_code = normalize_plan_code(raw_plan)
    billing_cycle = normalize_billing_cycle(raw_plan)

    # Fallback para valores desconocidos: usar la opción mensual/entry en vez de trial.
    if plan_code == PLAN_TRIAL and raw_plan not in {"trial"}:
        plan_code = PLAN_ENTRY
        billing_cycle = BILLING_MONTHLY

    plan_price = get_plan_price(country, plan_code, billing_cycle)
    plan_name = get_plan_display_name(plan_code, lang=lang)
    plan_days = 30 if billing_cycle == BILLING_MONTHLY else 365
    return plan_code, billing_cycle, plan_price, plan_name, plan_days


def _supported_payment_flags(country):
    methods = get_supported_payment_methods(country)
    return {
        "flow_enabled": PAYMENT_METHOD_FLOW in methods and _flow_is_enabled(),
        "mp_enabled": PAYMENT_METHOD_MERCADOPAGO in methods and _mp_is_enabled(),
        "paypal_enabled": PAYMENT_METHOD_PAYPAL in methods,
        "bank_transfer_enabled": PAYMENT_METHOD_BANK_TRANSFER in methods,
    }


def _dashboard_path_for_company(empresa):
    country = (getattr(empresa, "pais", "") or "CL").upper()
    if country == "US":
        return "/us/en/dashboard/"
    if country == "MX":
        return "/mx/es/dashboard/"
    return "/cl/es/dashboard/"


def _redirect_after_payment(request, empresa=None):
    if empresa is None and request.user.is_authenticated:
        try:
            empresa = request.user.empresa
        except Empresa.DoesNotExist:
            empresa = None

    target = _dashboard_path_for_company(empresa) if empresa else "/"
    if request.user.is_authenticated or empresa is None:
        return redirect(target)
    return redirect(f"/accounts/login/?next={target}")


def _get_flow_transaction(token, status_data):
    from taller.models.suscripcion_transaccion import SuscripcionTransaccion

    commerce_order = str(status_data.get("commerceOrder") or "").strip()
    queryset = SuscripcionTransaccion.objects.select_related("empresa", "empresa__user")

    transaccion = queryset.filter(external_transaction_id=token).first()
    if transaccion:
        return transaccion

    if commerce_order:
        return queryset.filter(reference=commerce_order).first()

    return None


def _get_mp_transaction(payment_data, payment_id):
    from taller.models.suscripcion_transaccion import SuscripcionTransaccion

    external_reference = str(payment_data.get("external_reference") or "").strip()
    preference_id = str(payment_data.get("preference_id") or "").strip()
    payment_id = str(payment_id or payment_data.get("id") or "").strip()

    queryset = SuscripcionTransaccion.objects.select_related("empresa", "empresa__user")

    if external_reference:
        transaccion = queryset.filter(reference=external_reference).first()
        if transaccion:
            return transaccion

    if preference_id:
        transaccion = queryset.filter(external_transaction_id=preference_id).first()
        if transaccion:
            return transaccion

    if payment_id:
        transaccion = queryset.filter(external_transaction_id=payment_id).first()
        if transaccion:
            return transaccion

    return None


def _process_flow_notification(token, *, processed_by):
    status_data = get_payment_status(token)
    transaccion = _get_flow_transaction(token, status_data)
    if transaccion is None:
        raise LookupError(f"No existe SuscripcionTransaccion para token Flow {token}")

    update_fields = []
    commerce_order = str(status_data.get("commerceOrder") or "").strip()
    payer = (status_data.get("payer") or "").strip()
    if transaccion.external_transaction_id != token:
        transaccion.external_transaction_id = token
        update_fields.append("external_transaction_id")
    if commerce_order and transaccion.reference != commerce_order:
        transaccion.reference = commerce_order
        update_fields.append("reference")
    if payer and not transaccion.customer_email:
        transaccion.customer_email = payer
        update_fields.append("customer_email")
    if update_fields:
        transaccion.save(update_fields=update_fields + ["updated_at"])

    flow_status = status_data.get("status")
    try:
        flow_status = int(flow_status)
    except (TypeError, ValueError):
        flow_status = None

    payload = {
        "flow_status_response": status_data,
    }

    if flow_status == 2:
        transaccion = approve_transaction(
            transaccion,
            raw_status=str(flow_status),
            processed_by=processed_by,
            gateway_payload=payload,
        )
    elif flow_status == 1:
        transaccion = mark_transaction_pending(
            transaccion,
            raw_status=str(flow_status),
            processed_by=processed_by,
            gateway_payload=payload,
        )
    elif flow_status == 3:
        transaccion = reject_transaction(
            transaccion,
            status="rejected",
            raw_status=str(flow_status),
            reason="Pago rechazado por Flow.",
            processed_by=processed_by,
            gateway_payload=payload,
        )
    elif flow_status == 4:
        transaccion = reject_transaction(
            transaccion,
            status="cancelled",
            raw_status=str(flow_status),
            reason="Pago anulado en Flow.",
            processed_by=processed_by,
            gateway_payload=payload,
        )
    else:
        transaccion = reject_transaction(
            transaccion,
            status="error",
            raw_status=str(flow_status),
            reason="Flow devolvio un estado no reconocido.",
            processed_by=processed_by,
            gateway_payload=payload,
        )

    return transaccion, status_data


def _process_mp_notification(payment_id, *, processed_by):
    payment_data = get_mp_payment(payment_id)
    transaccion = _get_mp_transaction(payment_data, payment_id)
    if transaccion is None:
        raise LookupError(f"No existe SuscripcionTransaccion para Mercado Pago {payment_id}")

    update_fields = []
    external_reference = str(payment_data.get("external_reference") or "").strip()
    preference_id = str(payment_data.get("preference_id") or "").strip()
    resolved_payment_id = str(payment_data.get("id") or payment_id or "").strip()
    if external_reference and transaccion.reference != external_reference:
        transaccion.reference = external_reference
        update_fields.append("reference")
    if resolved_payment_id and transaccion.external_transaction_id != resolved_payment_id:
        transaccion.external_transaction_id = resolved_payment_id
        update_fields.append("external_transaction_id")
    if update_fields:
        transaccion.save(update_fields=update_fields)

    mp_status = (payment_data.get("status") or "").strip().lower()
    payload = {"mp_payment_response": payment_data}

    if mp_status == "approved":
        transaccion = approve_transaction(
            transaccion,
            raw_status=mp_status,
            processed_by=processed_by,
            gateway_payload=payload,
        )
    elif mp_status in {"pending", "in_process", "authorized"}:
        transaccion = mark_transaction_pending(
            transaccion,
            raw_status=mp_status,
            processed_by=processed_by,
            gateway_payload=payload,
        )
    elif mp_status in {"rejected", "cancelled", "refunded", "charged_back"}:
        transaccion = reject_transaction(
            transaccion,
            status="rejected" if mp_status != "cancelled" else "cancelled",
            raw_status=mp_status,
            reason=f"Pago Mercado Pago en estado {mp_status}.",
            processed_by=processed_by,
            gateway_payload=payload,
        )
    else:
        transaccion = reject_transaction(
            transaccion,
            status="error",
            raw_status=mp_status or "unknown",
            reason="Mercado Pago devolvio un estado no reconocido.",
            processed_by=processed_by,
            gateway_payload=payload,
        )

    return transaccion, payment_data


@login_required
def payment_chile(request):
    """
    Pagina de pago para Chile con Flow y transferencia bancaria.
    """
    try:
        empresa = request.user.empresa
    except Empresa.DoesNotExist:
        messages.error(
            request,
            "No hay una empresa asociada a tu cuenta. Completa el registro o contacta soporte.",
        )
        return redirect("chile:dashboard")

    raw_plan = (request.GET.get("plan") or "mensual").strip().lower()
    plan_code, billing_cycle, plan_price, plan_name, plan_days = _plan_context_for_country(
        "CL", raw_plan, lang="es"
    )
    datos_banco = get_transfer_payment_details("CL")
    flags = _supported_payment_flags("CL")

    plan_info = {
        "valor": plan_price["price"],
        "dias": plan_days,
        "nombre": plan_name,
    }

    context = {
        "empresa": empresa,
        "plan": raw_plan,
        "plan_info": plan_info,
        "datos_banco": datos_banco,
        "monto_pagar": plan_price["price"],
        "referencia": f"eGarage-{empresa.id}-{raw_plan}",
        **flags,
    }
    return render(request, "saas/suscripcion/pago_chile.html", context)


@login_required
def payment_mexico(request):
    """
    Pagina de pago para Mexico con transferencia bancaria.
    """
    try:
        empresa = request.user.empresa
    except Empresa.DoesNotExist:
        messages.error(
            request,
            "No hay una empresa asociada a tu cuenta. Completa el registro o contacta soporte.",
        )
        return redirect("mexico:dashboard_mexico")

    raw_plan = (request.GET.get("plan") or "mensual").strip().lower()
    plan_code, billing_cycle, plan_price, plan_name, plan_days = _plan_context_for_country(
        "MX", raw_plan, lang="es"
    )
    datos_banco = get_transfer_payment_details("MX")
    flags = _supported_payment_flags("MX")

    plan_info = {
        "valor": plan_price["price"],
        "dias": plan_days,
        "nombre": plan_name,
    }

    context = {
        "empresa": empresa,
        "plan": raw_plan,
        "plan_info": plan_info,
        "datos_banco": datos_banco,
        "monto_pagar": plan_price["price"],
        "referencia": f"eGarage-MX-{empresa.id}-{raw_plan}",
        **flags,
    }

    return render(request, "saas/suscripcion/pago_mexico.html", context)


@login_required
def payment_usa(request):
    """
    Pagina de pago para USA via PayPal.
    """
    try:
        empresa = request.user.empresa
    except Empresa.DoesNotExist:
        messages.error(
            request,
            "No hay una empresa asociada a tu cuenta. Completa el registro o contacta soporte.",
        )
        return redirect("usa:dashboard")

    raw_plan = (request.GET.get("plan") or "mensual").strip().lower()
    plan_code, billing_cycle, plan_price, plan_name, plan_days = _plan_context_for_country(
        "US", raw_plan, lang="en"
    )
    datos_banco = get_transfer_payment_details("US")
    flags = _supported_payment_flags("US")

    paypal_config = {
        "business_email": get_paypal_business_email(),
        "currency": plan_price["currency"],
        "item_name": f'eGarage {plan_name} Subscription',
        "item_number": f"egarage-{raw_plan}",
        "return_url": request.build_absolute_uri("/us/en/payment/success/"),
        "cancel_url": request.build_absolute_uri("/us/en/payment/cancel/"),
        "notify_url": request.build_absolute_uri("/webhooks/paypal/"),
    }

    plan_info = {
        "valor": plan_price["price"],
        "dias": plan_days,
        "nombre": plan_name,
    }

    context = {
        "empresa": empresa,
        "plan": raw_plan,
        "plan_info": plan_info,
        "paypal_config": paypal_config,
        "datos_banco": datos_banco,
        "amount": plan_price["price"],
        "reference": f"eGarage-{empresa.id}-{raw_plan}",
        **flags,
    }

    return render(request, "us/en/suscripcion/pago.html", context)


@login_required
@require_POST
def start_flow_payment(request):
    if not _flow_is_enabled():
        messages.error(request, "Flow no esta configurado todavia para este entorno.")
        return redirect(f"/cl/es/suscripcion/pago/?plan={request.POST.get('plan', 'mensual')}")

    try:
        empresa = request.user.empresa
    except Empresa.DoesNotExist:
        messages.error(
            request,
            "No hay una empresa asociada a tu cuenta. Completa el registro o contacta soporte.",
        )
        return redirect("chile:dashboard")

    raw_plan = (request.POST.get("plan") or "mensual").strip().lower()
    plan_code, billing_cycle, plan_price, plan_name, _ = _plan_context_for_country(
        "CL", raw_plan, lang="es"
    )

    transaccion = create_gateway_transaction(
        empresa=empresa,
        source_type="flow",
        payment_method="flow",
        amount=Decimal(str(plan_price["price"])),
        currency="CLP",
        billing_cycle=billing_cycle,
        plan_code=plan_code,
        reference=f"SUB-{uuid.uuid4().hex}",
        customer_email=request.user.email or empresa.email,
        description=f"Suscripcion eGarage - {plan_name}",
        gateway_payload={
            "gateway": "flow",
            "created_via": "payment_chile",
        },
    )

    try:
        checkout_url = create_payment_order(
            transaccion,
            return_url=request.build_absolute_uri(reverse("flow_return")),
            confirmation_url=request.build_absolute_uri(reverse("flow_webhook")),
        )
    except FlowAPIError as exc:
        transaccion.status = "error"
        transaccion.raw_status = "flow_create_error"
        transaccion.admin_notes = str(exc)
        transaccion.processed_at = timezone.now()
        transaccion.processed_by = "flow_create"
        transaccion.save(
            update_fields=[
                "status",
                "raw_status",
                "admin_notes",
                "processed_at",
                "processed_by",
                "updated_at",
            ]
        )
        logger.exception("Error creando la orden en Flow para la empresa %s", empresa.pk)
        messages.error(request, "No fue posible iniciar el pago con Flow. Intenta nuevamente.")
        return redirect(f"/cl/es/suscripcion/pago/?plan={raw_plan}")

    return redirect(checkout_url)


@login_required
@require_POST
def start_mp_payment(request):
    if not _mp_is_enabled():
        messages.error(request, "Mercado Pago no esta configurado todavia para este entorno.")
        return redirect(f"/cl/es/suscripcion/pago/?plan={request.POST.get('plan', 'mensual')}")

    try:
        empresa = request.user.empresa
    except Empresa.DoesNotExist:
        messages.error(
            request,
            "No hay una empresa asociada a tu cuenta. Completa el registro o contacta soporte.",
        )
        return redirect("chile:dashboard")

    raw_plan = (request.POST.get("plan") or "mensual").strip().lower()
    plan_code, billing_cycle, plan_price, plan_name, _ = _plan_context_for_country(
        "CL", raw_plan, lang="es"
    )

    transaccion = create_gateway_transaction(
        empresa=empresa,
        source_type="mercadopago",
        payment_method="mercadopago",
        amount=Decimal(str(plan_price["price"])),
        currency="CLP",
        billing_cycle=billing_cycle,
        plan_code=plan_code,
        reference=str(uuid.uuid4().int),
        customer_email=empresa.email or request.user.email,
        description=f"Suscripcion eGarage - {plan_name}",
        gateway_payload={
            "gateway": "mercadopago",
            "created_via": "payment_chile",
        },
    )
    transaccion.reference = str(transaccion.id)
    transaccion.save(update_fields=["reference", "updated_at"])

    try:
        checkout_url = create_mp_preference(
            transaccion,
            success_url=request.build_absolute_uri(reverse("mp_return")),
            failure_url=request.build_absolute_uri(reverse("mp_return")),
            pending_url=request.build_absolute_uri(reverse("mp_return")),
            webhook_url=request.build_absolute_uri(reverse("mp_webhook")),
        )
    except MPAPIError as exc:
        transaccion.status = "error"
        transaccion.raw_status = "mp_create_error"
        transaccion.admin_notes = str(exc)
        transaccion.processed_at = timezone.now()
        transaccion.processed_by = "mp_create"
        transaccion.save(
            update_fields=[
                "status",
                "raw_status",
                "admin_notes",
                "processed_at",
                "processed_by",
                "updated_at",
            ]
        )
        logger.exception("Error creando preferencia en Mercado Pago para la empresa %s", empresa.pk)
        messages.error(request, "No fue posible iniciar el pago con Mercado Pago. Intenta nuevamente.")
        return redirect(f"/cl/es/suscripcion/pago/?plan={raw_plan}")

    return redirect(checkout_url)


@csrf_exempt
@require_POST
def flow_webhook(request):
    token = (request.POST.get("token") or "").strip()
    if not token:
        return HttpResponseBadRequest("Missing token")

    try:
        _process_flow_notification(token, processed_by="flow_webhook")
    except LookupError:
        logger.exception("Webhook Flow recibido con token desconocido: %s", token)
        return HttpResponse(status=404)
    except FlowAPIError:
        logger.exception("No se pudo consultar el estado en Flow para token %s", token)
        return HttpResponse(status=500)

    return HttpResponse("OK")


@require_http_methods(["GET", "POST"])
def flow_return(request):
    token = (request.POST.get("token") or request.GET.get("token") or "").strip()
    if not token:
        messages.warning(request, "Flow no devolvio un token de transaccion.")
        return _redirect_after_payment(request)

    transaccion = None
    try:
        transaccion, _status_data = _process_flow_notification(token, processed_by="flow_return")
    except LookupError:
        logger.exception("Retorno Flow con token desconocido: %s", token)
        messages.error(request, "No pudimos localizar la transaccion informada por Flow.")
        return _redirect_after_payment(request)
    except FlowAPIError:
        logger.exception("Error consultando Flow en retorno browser para token %s", token)
        messages.error(request, "No pudimos confirmar el estado del pago en este momento.")
        return _redirect_after_payment(request)

    if transaccion.status == "approved":
        messages.success(request, "Pago confirmado. Tu suscripcion ya fue activada.")
    elif transaccion.status == "pending":
        messages.info(
            request,
            "Tu pago quedo pendiente de confirmacion. Activaremos la suscripcion apenas Flow confirme el cobro.",
        )
    elif transaccion.status == "cancelled":
        messages.warning(request, "El pago fue anulado antes de completarse.")
    else:
        messages.error(request, "Flow informo que el pago no se pudo completar.")

    return _redirect_after_payment(request, transaccion.empresa)


@csrf_exempt
@require_POST
def mp_webhook(request):
    payment_id = (
        request.GET.get("data.id")
        or request.GET.get("id")
        or request.POST.get("data.id")
        or request.POST.get("id")
        or ""
    ).strip()
    if not payment_id and request.body:
        try:
            import json

            payload = json.loads(request.body.decode("utf-8"))
            data = payload.get("data") or {}
            payment_id = str(data.get("id") or payload.get("id") or "").strip()
        except Exception:
            payment_id = ""

    if not payment_id:
        return HttpResponseBadRequest("Missing payment id")

    try:
        _process_mp_notification(payment_id, processed_by="mp_webhook")
    except LookupError:
        logger.exception("Webhook Mercado Pago recibido con payment desconocido: %s", payment_id)
        return HttpResponse(status=404)
    except MPAPIError:
        logger.exception("No se pudo consultar el pago en Mercado Pago para %s", payment_id)
        return HttpResponse(status=500)

    return HttpResponse("OK")


@require_http_methods(["GET", "POST"])
def mp_return(request):
    payment_id = (
        request.GET.get("payment_id")
        or request.GET.get("data.id")
        or request.GET.get("id")
        or request.POST.get("payment_id")
        or request.POST.get("data.id")
        or request.POST.get("id")
        or ""
    ).strip()

    if not payment_id:
        messages.warning(request, "Mercado Pago no devolvio un identificador de pago.")
        return _redirect_after_payment(request)

    try:
        transaccion, _payment_data = _process_mp_notification(payment_id, processed_by="mp_return")
    except LookupError:
        logger.exception("Retorno Mercado Pago con pago desconocido: %s", payment_id)
        messages.error(request, "No pudimos localizar el pago informado por Mercado Pago.")
        return _redirect_after_payment(request)
    except MPAPIError:
        logger.exception("Error consultando Mercado Pago en retorno browser para %s", payment_id)
        messages.error(request, "No pudimos confirmar el estado del pago en este momento.")
        return _redirect_after_payment(request)

    if transaccion.status == "approved":
        messages.success(request, "Pago confirmado. Tu suscripcion ya fue activada.")
    elif transaccion.status == "pending":
        messages.info(
            request,
            "Tu pago quedo pendiente de confirmacion. Activaremos la suscripcion cuando Mercado Pago lo apruebe.",
        )
    elif transaccion.status == "cancelled":
        messages.warning(request, "El pago fue cancelado antes de completarse.")
    else:
        messages.error(request, "Mercado Pago informo que el pago no se pudo completar.")

    return _redirect_after_payment(request, transaccion.empresa)


@login_required
def subir_comprobante(request):
    """
    Subir comprobante de pago manual.
    """
    if request.method == "POST":
        comprobante = request.FILES.get("comprobante")
        plan = request.POST.get("plan")
        monto = request.POST.get("monto")

        if comprobante:
            empresa = request.user.empresa

            from taller.models.pago import PagoPendiente

            PagoPendiente.objects.create(
                empresa=empresa,
                plan=plan,
                monto=Decimal(monto),
                comprobante=comprobante,
                estado="pendiente",
                fecha_subida=timezone.now(),
            )

            messages.success(
                request,
                "Comprobante recibido. Tu suscripcion sera activada en 24-48 horas despues de verificar el pago.",
            )

            return _redirect_after_payment(request, empresa)

    return render(
        request,
        "saas/suscripcion/subir_comprobante.html",
        {
            "empresa": request.user.empresa,
        },
    )


@login_required
def payment_success(request):
    """
    Callback de pago exitoso de PayPal.
    """
    messages.success(
        request, "Pago recibido. Tu suscripcion sera activada en las proximas horas."
    )
    return _redirect_after_payment(request)


@login_required
def payment_cancel(request):
    """
    Pago cancelado por el usuario.
    """
    messages.warning(request, "Pago cancelado. Puedes intentar nuevamente cuando lo desees.")
    return _redirect_after_payment(request)
