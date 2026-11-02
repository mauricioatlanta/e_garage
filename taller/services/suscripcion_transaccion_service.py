import logging

from django.db import transaction
from django.utils import timezone

from taller.utils.email_helper import send_template_email
from taller.utils.payment_config import normalize_company_plan
from taller.utils.plan_catalog import (
    ALL_BILLING_PERIODS,
    ALL_PLAN_CODES,
    BILLING_ANNUAL,
    BILLING_MONTHLY,
    LEGACY_BILLING_MAPPING,
    LEGACY_PLAN_MAPPING,
    get_months_paid,
    normalize_billing_cycle as normalize_catalog_billing_cycle,
)


logger = logging.getLogger(__name__)

PAGO_PENDIENTE_STATUS_MAP = {
    "pendiente": "pending",
    "verificado": "processing",
    "rechazado": "rejected",
    "procesado": "approved",
}

COMPROBANTE_STATUS_MAP = {
    "pendiente": "pending",
    "aprobado": "approved",
    "rechazado": "rejected",
}

MONTHS_BY_BILLING_CYCLE = {
    BILLING_MONTHLY: 1,
    BILLING_ANNUAL: 12,
    "mensual": 1,
    "semestral": 6,
    "anual": 12,
    "individual_mensual": 1,
    "individual_anual": 12,
    "equipo_mensual": 1,
    "equipo_anual": 12,
    "empresa_mensual": 1,
    "empresa_anual": 12,
}

DAYS_BY_BILLING_CYCLE = {
    BILLING_MONTHLY: 30,
    BILLING_ANNUAL: 365,
    "mensual": 30,
    "semestral": 180,
    "anual": 365,
    "individual_mensual": 30,
    "individual_anual": 365,
    "equipo_mensual": 30,
    "equipo_anual": 365,
    "empresa_mensual": 30,
    "empresa_anual": 365,
}


def _safe_receipt_path(file_field):
    try:
        return file_field.name or ""
    except Exception:
        return ""


def _safe_customer_email(empresa):
    return getattr(empresa, "email", "") or getattr(getattr(empresa, "user", None), "email", "")


def _normalize_payment_method(value, default="transferencia"):
    value = (value or default).strip().lower()
    allowed = {
        "transferencia",
        "flow",
        "webpay",
        "khipu",
        "mercadopago",
        "paypal",
        "otro",
    }
    return value if value in allowed else "otro"


def _normalize_billing_cycle(value):
    raw_value = (value or "").strip().lower()
    valid_values = (
        ALL_BILLING_PERIODS
        | ALL_PLAN_CODES
        | set(LEGACY_BILLING_MAPPING)
        | set(LEGACY_PLAN_MAPPING)
        | set(MONTHS_BY_BILLING_CYCLE)
    )
    if raw_value and raw_value not in valid_values:
        return "otro"
    billing_cycle = normalize_catalog_billing_cycle(raw_value)
    if billing_cycle in ALL_BILLING_PERIODS:
        return billing_cycle
    return "otro"


def _months_paid_for_billing_cycle(value):
    billing_cycle = _normalize_billing_cycle(value)
    if billing_cycle == "otro":
        return MONTHS_BY_BILLING_CYCLE.get((value or "").strip().lower(), 1)
    return get_months_paid(billing_cycle)


def _merge_gateway_payload(instance, payload=None):
    if not payload:
        return instance.gateway_payload or {}
    merged = dict(instance.gateway_payload or {})
    merged.update(payload)
    return merged


def _append_admin_note(instance, note):
    if not note:
        return instance.admin_notes
    current = (instance.admin_notes or "").strip()
    if not current:
        return note
    if note in current:
        return current
    return f"{current}\n{note}"


def _lock_transaccion(transaccion):
    from taller.models.suscripcion_transaccion import SuscripcionTransaccion

    return (
        SuscripcionTransaccion.objects.select_for_update()
        .select_related("empresa", "empresa__user")
        .get(pk=transaccion.pk)
    )


def _unique_email_recipients(*emails):
    recipients = []
    seen = set()
    for email in emails:
        normalized = (email or "").strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        recipients.append(normalized)
    return recipients


def _send_subscription_confirmation_email(*, empresa, transaccion, es_nueva_suscripcion):
    recipients = _unique_email_recipients(
        getattr(getattr(empresa, "user", None), "email", ""),
        getattr(empresa, "email", ""),
        getattr(transaccion, "customer_email", ""),
    )
    if not recipients:
        logger.warning(
            "No hay destinatarios para la confirmacion de suscripcion de la transaccion %s",
            getattr(transaccion, "pk", None),
        )
        return 0

    subject = (
        "Welcome to eGarage - Subscription confirmed"
        if getattr(empresa, "pais", "") == "US"
        else (
            "Suscripción activada en eGarage"
            if es_nueva_suscripcion
            else "Pago confirmado - Suscripción activa en eGarage"
        )
    )
    template_name = "emails/suscripcion_confirmada.html"

    return send_template_email(
        template_name=template_name,
        context={
            "empresa": empresa,
            "transaccion": transaccion,
            "es_nueva_suscripcion": es_nueva_suscripcion,
        },
        subject=subject,
        recipient_list=recipients,
        fail_silently=False,
    )


def _send_subscription_notifications(
    *,
    empresa,
    transaccion,
    plan_anterior,
    plan_nuevo,
    monto,
    fecha_inicio,
    dias_renovados,
    suscripcion_activa_anterior,
):
    es_nueva_suscripcion = (not suscripcion_activa_anterior) or plan_anterior == "trial"
    es_cambio_plan = suscripcion_activa_anterior and plan_anterior != plan_nuevo and plan_anterior != "trial"

    try:
        _send_subscription_confirmation_email(
            empresa=empresa,
            transaccion=transaccion,
            es_nueva_suscripcion=es_nueva_suscripcion,
        )

        from taller.utils.notificaciones_suscripcion import (
            notificar_cambio_plan,
            notificar_nueva_suscripcion,
            notificar_renovacion_exitosa,
        )

        if es_nueva_suscripcion:
            notificar_nueva_suscripcion(
                empresa=empresa,
                plan=plan_nuevo,
                monto=monto,
                es_nueva_empresa=es_nueva_suscripcion,
                send_email=False,
            )
            return

        if es_cambio_plan:
            notificar_cambio_plan(
                empresa=empresa,
                plan_anterior=plan_anterior,
                plan_nuevo=plan_nuevo,
                monto=monto,
                fecha_inicio=fecha_inicio,
                send_email=False,
            )
            return

        notificar_renovacion_exitosa(
            empresa=empresa,
            plan=plan_nuevo,
            monto=monto,
            dias_renovados=dias_renovados,
            send_email=False,
        )
    except Exception:
        logger.exception(
            "No se pudo enviar la notificacion de suscripcion para la transaccion %s",
            getattr(transaccion, "pk", None),
        )


def sync_from_pago_pendiente(pago_pendiente):
    from taller.models.suscripcion_transaccion import SuscripcionTransaccion

    billing_cycle = _normalize_billing_cycle(pago_pendiente.plan)
    defaults = {
        "empresa": pago_pendiente.empresa,
        "source_type": "legacy_pago_pendiente",
        "status": PAGO_PENDIENTE_STATUS_MAP.get(pago_pendiente.estado, "pending"),
        "raw_status": pago_pendiente.estado,
        "payment_method": _normalize_payment_method(pago_pendiente.metodo_pago),
        "billing_cycle": billing_cycle,
        "plan_code": normalize_company_plan(pago_pendiente.plan),
        "months_paid": _months_paid_for_billing_cycle(pago_pendiente.plan),
        "amount": pago_pendiente.monto,
        "currency": "CLP" if pago_pendiente.empresa.pais == "CL" else "USD",
        "reference": pago_pendiente.referencia or f"pago-pendiente-{pago_pendiente.pk}",
        "external_transaction_id": pago_pendiente.referencia or "",
        "customer_email": _safe_customer_email(pago_pendiente.empresa),
        "receipt_path": _safe_receipt_path(pago_pendiente.comprobante),
        "description": "",
        "admin_notes": pago_pendiente.notas or "",
        "gateway_payload": {
            "legacy_model": "PagoPendiente",
            "legacy_pk": pago_pendiente.pk,
        },
        "submitted_at": pago_pendiente.fecha_subida or timezone.now(),
        "processed_at": pago_pendiente.fecha_verificacion,
        "processed_by": (
            getattr(pago_pendiente.verificado_por, "username", "") if pago_pendiente.verificado_por else ""
        ),
    }
    return SuscripcionTransaccion.objects.update_or_create(
        legacy_pago_pendiente=pago_pendiente,
        defaults=defaults,
    )[0]


def sync_from_comprobante_pago(comprobante_pago):
    from taller.models.suscripcion_transaccion import SuscripcionTransaccion

    defaults = {
        "empresa": comprobante_pago.empresa,
        "source_type": "legacy_comprobante_pago",
        "status": COMPROBANTE_STATUS_MAP.get(comprobante_pago.estado, "pending"),
        "raw_status": comprobante_pago.estado,
        "payment_method": _normalize_payment_method(comprobante_pago.metodo_pago, default="otro"),
        "billing_cycle": _normalize_billing_cycle(
            {
                1: "mensual",
                6: "semestral",
                12: "anual",
            }.get(comprobante_pago.meses_pagados, "otro")
        ),
        "plan_code": normalize_company_plan(comprobante_pago.plan_solicitado),
        "months_paid": comprobante_pago.meses_pagados or 1,
        "amount": comprobante_pago.monto,
        "currency": comprobante_pago.moneda or "CLP",
        "reference": (
            comprobante_pago.numero_transaccion or f"comprobante-pago-{comprobante_pago.pk}"
        ),
        "external_transaction_id": comprobante_pago.numero_transaccion or "",
        "customer_email": _safe_customer_email(comprobante_pago.empresa),
        "receipt_path": _safe_receipt_path(comprobante_pago.comprobante),
        "description": comprobante_pago.descripcion or "",
        "admin_notes": comprobante_pago.notas_admin or "",
        "gateway_payload": {
            "legacy_model": "ComprobantePago",
            "legacy_pk": comprobante_pago.pk,
        },
        "submitted_at": comprobante_pago.fecha_subida or timezone.now(),
        "processed_at": comprobante_pago.fecha_procesado,
        "processed_by": comprobante_pago.procesado_por or "",
    }
    return SuscripcionTransaccion.objects.update_or_create(
        legacy_comprobante_pago=comprobante_pago,
        defaults=defaults,
    )[0]


def create_gateway_transaction(
    *,
    empresa,
    source_type,
    payment_method,
    amount,
    currency,
    billing_cycle,
    plan_code,
    reference="",
    external_transaction_id="",
    checkout_url="",
    customer_email="",
    description="",
    gateway_payload=None,
):
    from taller.models.suscripcion_transaccion import SuscripcionTransaccion

    return SuscripcionTransaccion.objects.create(
        empresa=empresa,
        source_type=source_type,
        status="pending",
        raw_status="pending",
        payment_method=_normalize_payment_method(payment_method),
        billing_cycle=_normalize_billing_cycle(billing_cycle),
        plan_code=normalize_company_plan(plan_code),
        months_paid=_months_paid_for_billing_cycle(billing_cycle),
        amount=amount,
        currency=currency,
        reference=reference,
        external_transaction_id=external_transaction_id,
        checkout_url=checkout_url,
        customer_email=customer_email or _safe_customer_email(empresa),
        description=description,
        gateway_payload=gateway_payload or {},
    )


def mark_transaction_pending(
    transaccion,
    *,
    raw_status="pending",
    processed_by="",
    gateway_payload=None,
):
    with transaction.atomic():
        locked = _lock_transaccion(transaccion)
        if locked.subscription_applied_at:
            locked.gateway_payload = _merge_gateway_payload(locked, gateway_payload)
            if processed_by:
                locked.processed_by = processed_by
            locked.save(
                update_fields=[
                    "gateway_payload",
                    "processed_by",
                    "updated_at",
                ]
            )
            return locked

        locked.status = "pending"
        locked.raw_status = str(raw_status)
        locked.gateway_payload = _merge_gateway_payload(locked, gateway_payload)
        if processed_by:
            locked.processed_by = processed_by
        locked.save(
            update_fields=[
                "status",
                "raw_status",
                "gateway_payload",
                "processed_by",
                "updated_at",
            ]
        )
        return locked


def reject_transaction(
    transaccion,
    *,
    status="rejected",
    raw_status="rejected",
    reason="",
    processed_by="",
    gateway_payload=None,
):
    final_status = status if status in {"rejected", "cancelled", "error"} else "rejected"
    with transaction.atomic():
        locked = _lock_transaccion(transaccion)
        if locked.subscription_applied_at:
            locked.admin_notes = _append_admin_note(locked, reason)
            locked.gateway_payload = _merge_gateway_payload(locked, gateway_payload)
            if processed_by:
                locked.processed_by = processed_by
            locked.save(
                update_fields=[
                    "admin_notes",
                    "gateway_payload",
                    "processed_by",
                    "updated_at",
                ]
            )
            return locked

        locked.status = final_status
        locked.raw_status = str(raw_status)
        locked.processed_at = timezone.now()
        if processed_by:
            locked.processed_by = processed_by
        locked.admin_notes = _append_admin_note(locked, reason)
        locked.gateway_payload = _merge_gateway_payload(locked, gateway_payload)
        locked.save(
            update_fields=[
                "status",
                "raw_status",
                "processed_at",
                "processed_by",
                "admin_notes",
                "gateway_payload",
                "updated_at",
            ]
        )
        return locked


def approve_transaction(
    transaccion,
    *,
    raw_status="approved",
    processed_by="",
    gateway_payload=None,
):
    with transaction.atomic():
        locked = _lock_transaccion(transaccion)
        normalized_plan = normalize_company_plan(locked.plan_code or locked.billing_cycle)
        update_fields = ["plan_code", "status", "raw_status", "gateway_payload", "updated_at"]

        locked.plan_code = normalized_plan
        locked.status = "approved"
        locked.raw_status = str(raw_status)
        locked.gateway_payload = _merge_gateway_payload(locked, gateway_payload)
        if processed_by:
            locked.processed_by = processed_by
            update_fields.append("processed_by")

        if locked.subscription_applied_at:
            if not locked.processed_at:
                locked.processed_at = locked.subscription_applied_at
                update_fields.append("processed_at")
            locked.save(update_fields=update_fields)
            return locked

        from taller.models.subscription_change import SubscriptionChange

        plan_change = locked.subscription_changes.select_for_update().filter(
            change_type=SubscriptionChange.CHANGE_UPGRADE,
            status=SubscriptionChange.STATUS_PENDING,
        ).first()
        if plan_change:
            empresa = locked.empresa
            suscripcion_activa_anterior = bool(empresa.suscripcion_activa)
            plan_anterior = empresa.plan
            fecha_inicio_notificacion = empresa.fecha_inicio

            from taller.services.plan_change_service import complete_paid_plan_change

            completed_change = complete_paid_plan_change(change=plan_change)
            normalized_plan = completed_change.requested_plan
            locked.plan_code = normalized_plan
            locked.processed_at = timezone.now()
            locked.subscription_applied_at = locked.processed_at
            update_fields.extend(["processed_at", "subscription_applied_at"])
            locked.save(update_fields=update_fields)

            dias_renovados = 0
        else:
            empresa = locked.empresa
            suscripcion_activa_anterior = bool(empresa.suscripcion_activa)
            plan_anterior = empresa.plan
            fecha_inicio_notificacion = empresa.fecha_inicio
            dias_renovados = DAYS_BY_BILLING_CYCLE.get(locked.billing_cycle, 30)
            es_nueva_suscripcion = (not suscripcion_activa_anterior) or plan_anterior == "trial"

            empresa.extender_suscripcion(
                dias=dias_renovados,
                enviar_notificacion=False,
                desde_ahora=es_nueva_suscripcion,
            )
            empresa.plan = normalized_plan
            empresa.valor_mensual = locked.amount
            empresa.save()

            locked.processed_at = timezone.now()
            locked.subscription_applied_at = locked.processed_at
            update_fields.extend(["processed_at", "subscription_applied_at"])
            locked.save(update_fields=update_fields)

    _send_subscription_notifications(
        empresa=empresa,
        transaccion=locked,
        plan_anterior=plan_anterior,
        plan_nuevo=normalized_plan,
        monto=locked.amount,
        fecha_inicio=fecha_inicio_notificacion,
        dias_renovados=dias_renovados,
        suscripcion_activa_anterior=suscripcion_activa_anterior,
    )
    return locked


class SuscripcionTransaccionService:
    finalizar_pago_exitoso = staticmethod(approve_transaction)
    aprobar = staticmethod(approve_transaction)
    marcar_pendiente = staticmethod(mark_transaction_pending)
    rechazar = staticmethod(reject_transaction)
    crear_transaccion_gateway = staticmethod(create_gateway_transaction)
    sincronizar_desde_pago_pendiente = staticmethod(sync_from_pago_pendiente)
    sincronizar_desde_comprobante_pago = staticmethod(sync_from_comprobante_pago)
