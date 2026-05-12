"""
Webhook de PayPal para procesar pagos automáticamente
"""

import json
import logging
from datetime import timedelta

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from taller.utils.payment_config import normalize_company_plan

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def paypal_webhook(request):
    """
    Recibe notificaciones de PayPal sobre pagos completados

    Eventos importantes:
    - PAYMENT.SALE.COMPLETED: Pago completado
    - BILLING.SUBSCRIPTION.CREATED: Suscripción creada
    - BILLING.SUBSCRIPTION.ACTIVATED: Suscripción activada
    """
    try:
        # Leer payload
        payload = json.loads(request.body.decode("utf-8"))
        event_type = payload.get("event_type")

        logger.info(f"📨 Webhook PayPal recibido: {event_type}")

        # TODO: Verificar firma de PayPal para seguridad
        # webhook_id = request.headers.get('PAYPAL-TRANSMISSION-ID')
        # verify_webhook_signature(webhook_id, payload)

        if event_type == "PAYMENT.SALE.COMPLETED":
            # Pago completado
            return handle_payment_completed(payload)

        elif event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
            # Suscripción activada
            return handle_subscription_activated(payload)

        else:
            logger.info(f"Evento no manejado: {event_type}")
            return JsonResponse({"status": "ignored"})

    except Exception as e:
        logger.error(f"Error en webhook PayPal: {str(e)}")
        return HttpResponse(status=500)


def handle_payment_completed(payload):
    """
    Procesar pago completado
    """
    from taller.models.empresa import Empresa
    from taller.models.pago import PagoPendiente

    try:
        # Extraer datos del payload
        sale_id = payload["resource"]["id"]
        payer_email = payload["resource"]["payer"]["email_address"]
        amount = float(payload["resource"]["amount"]["total"])
        currency = payload["resource"]["amount"]["currency"]

        # Buscar empresa por email
        try:
            empresa = Empresa.objects.get(email=payer_email)
        except Empresa.DoesNotExist:
            logger.error(f"Empresa no encontrada con email: {payer_email}")
            return JsonResponse({"status": "error", "message": "Company not found"})

        # Determinar ciclo de cobro según monto
        if currency == "USD":
            if amount >= 190:
                billing_cycle = "anual"
                dias = 365
            elif amount >= 100:
                billing_cycle = "semestral"
                dias = 180
            else:
                billing_cycle = "mensual"
                dias = 30
        else:
            billing_cycle = "mensual"
            dias = 30

        plan = normalize_company_plan(billing_cycle)

        # Crear registro de pago
        pago = PagoPendiente.objects.create(
            empresa=empresa,
            plan=billing_cycle,
            monto=amount,
            referencia=sale_id,
            metodo_pago="paypal",
            estado="procesado",  # Ya procesado por PayPal
        )

        # Detectar si es nueva suscripción o renovación
        plan_anterior = empresa.plan
        es_nueva_suscripcion = not empresa.suscripcion_activa or empresa.plan == "trial"
        es_cambio_plan = (
            empresa.suscripcion_activa and plan_anterior != plan and plan_anterior != "trial"
        )

        # Activar suscripción
        empresa.suscripcion_activa = True
        empresa.plan = plan
        empresa.valor_mensual = amount
        empresa.fecha_inicio = timezone.now()
        empresa.fecha_fin = timezone.now() + timedelta(days=dias)
        empresa.save()

        logger.info(f"✅ Pago PayPal procesado para {empresa.nombre_taller}")

        # Enviar notificaciones automáticas (Email + WhatsApp)
        from taller.utils.notificaciones_suscripcion import (
            notificar_cambio_plan,
            notificar_nueva_suscripcion,
            notificar_renovacion_exitosa,
        )

        if es_nueva_suscripcion:
            # A. NUEVA SUSCRIPCIÓN
            notificar_nueva_suscripcion(
                empresa=empresa,
                plan=plan,
                monto=amount,
                es_nueva_empresa=es_nueva_suscripcion,
            )
            logger.info(f"📧 Notificación de nueva suscripción enviada a {empresa.user.email}")
        elif es_cambio_plan:
            # B. CAMBIO DE PLAN
            notificar_cambio_plan(
                empresa=empresa,
                plan_anterior=plan_anterior,
                plan_nuevo=plan,
                monto=amount,
                fecha_inicio=empresa.fecha_inicio,
            )
            logger.info(f"📧 Notificación de cambio de plan enviada a {empresa.user.email}")
        else:
            # C. RENOVACIÓN EXITOSA
            notificar_renovacion_exitosa(
                empresa=empresa,
                plan=plan,
                monto=amount,
                dias_renovados=dias,
            )
            logger.info(f"📧 Notificación de renovación exitosa enviada a {empresa.user.email}")

        return JsonResponse({"status": "success"})

    except Exception as e:
        logger.error(f"Error procesando pago: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)})


def handle_subscription_activated(payload):
    """
    Procesar suscripción activada
    """
    logger.info("Suscripción activada via PayPal")
    return JsonResponse({"status": "success"})
