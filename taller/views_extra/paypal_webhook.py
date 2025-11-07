"""
Webhook de PayPal para procesar pagos automáticamente
"""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

import json
import logging

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
        payload = json.loads(request.body.decode('utf-8'))
        event_type = payload.get('event_type')
        
        logger.info(f"📨 Webhook PayPal recibido: {event_type}")
        
        # TODO: Verificar firma de PayPal para seguridad
        # webhook_id = request.headers.get('PAYPAL-TRANSMISSION-ID')
        # verify_webhook_signature(webhook_id, payload)
        
        if event_type == 'PAYMENT.SALE.COMPLETED':
            # Pago completado
            return handle_payment_completed(payload)
        
        elif event_type == 'BILLING.SUBSCRIPTION.ACTIVATED':
            # Suscripción activada
            return handle_subscription_activated(payload)
        
        else:
            logger.info(f"Evento no manejado: {event_type}")
            return JsonResponse({'status': 'ignored'})
    
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
        sale_id = payload['resource']['id']
        payer_email = payload['resource']['payer']['email_address']
        amount = float(payload['resource']['amount']['total'])
        currency = payload['resource']['amount']['currency']
        
        # Buscar empresa por email
        try:
            empresa = Empresa.objects.get(email=payer_email)
        except Empresa.DoesNotExist:
            logger.error(f"Empresa no encontrada con email: {payer_email}")
            return JsonResponse({'status': 'error', 'message': 'Company not found'})
        
        # Determinar plan según monto
        if currency == 'USD':
            if amount >= 190:
                plan = 'anual'
                dias = 365
            elif amount >= 100:
                plan = 'semestral'
                dias = 180
            else:
                plan = 'mensual'
                dias = 30
        else:
            plan = 'mensual'
            dias = 30
        
        # Crear registro de pago
        pago = PagoPendiente.objects.create(
            empresa=empresa,
            plan=plan,
            monto=amount,
            referencia=sale_id,
            metodo_pago='paypal',
            estado='procesado',  # Ya procesado por PayPal
        )
        
        # Activar suscripción
        empresa.suscripcion_activa = True
        empresa.plan = plan
        empresa.valor_mensual = amount
        empresa.fecha_inicio = timezone.now()
        empresa.fecha_fin = timezone.now() + timedelta(days=dias)
        empresa.save()
        
        logger.info(f"✅ Pago PayPal procesado para {empresa.nombre_taller}")
        
        # Enviar email de confirmación
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        
        html_message = render_to_string('email/pago_confirmado.html', {
            'empresa': empresa,
            'plan': plan,
            'monto': amount,
            'moneda': currency,
            'fecha_fin': empresa.fecha_fin,
            'language': 'en',
        })
        
        send_mail(
            subject='✅ Payment Confirmed - eGarage',
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[empresa.email],
            html_message=html_message,
            fail_silently=True,
        )
        
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        logger.error(f"Error procesando pago: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})


def handle_subscription_activated(payload):
    """
    Procesar suscripción activada
    """
    logger.info("Suscripción activada via PayPal")
    return JsonResponse({'status': 'success'})

