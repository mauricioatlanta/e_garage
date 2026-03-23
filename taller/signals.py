"""
Signals para notificaciones automáticas en eGarage
"""

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from taller.models.pago import PagoPendiente


@receiver(post_save, sender=PagoPendiente)
def notificar_pago_nuevo(sender, instance, created, **kwargs):
    """
    📧 Enviar notificaciones cuando se crea un nuevo pago pendiente

    1. Email al cliente confirmando recepción del comprobante
    2. Email al admin notificando nuevo pago para verificar
    """
    if not created:
        return  # Solo para pagos nuevos

    if instance.estado != "pendiente":
        return  # Solo para pagos pendientes

    # 📧 EMAIL 1: Confirmación al cliente (comprobante recibido)
    try:
        # Determinar moneda
        moneda = "CLP" if instance.empresa.pais == "CL" else "USD"

        html_message = render_to_string(
            "email/comprobante_recibido.html",
            {
                "empresa": instance.empresa,
                "plan": instance.plan,
                "monto": instance.monto,
                "moneda": moneda,
                "fecha": instance.fecha_subida.strftime("%d/%m/%Y %H:%M"),
            },
        )

        send_mail(
            subject="💰 Comprobante Recibido - eGarage",
            message="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.empresa.email],
            html_message=html_message,
            fail_silently=True,  # No fallar si hay error
        )

        print(f"✅ Email de comprobante recibido enviado a {instance.empresa.email}")

    except Exception as e:
        print(f"⚠️ Error al enviar email al cliente: {str(e)}")

    # 📧 EMAIL 2: Notificación al admin
    try:
        moneda = "CLP" if instance.empresa.pais == "CL" else "USD"

        html_message = render_to_string(
            "email/admin_pago_nuevo.html",
            {
                "empresa": instance.empresa,
                "plan": instance.plan,
                "monto": instance.monto,
                "moneda": moneda,
                "fecha": instance.fecha_subida.strftime("%d/%m/%Y %H:%M"),
                "pago_id": instance.id,
            },
        )

        # Email del admin (configurable)
        admin_email = getattr(settings, "ADMIN_EMAIL", "mauricioatlanta@gmail.com")

        send_mail(
            subject=f"🔔 Nuevo Pago Pendiente - {instance.empresa.nombre_taller}",
            message="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=True,
        )

        print(f"✅ Notificación enviada al admin: {admin_email}")

    except Exception as e:
        print(f"⚠️ Error al enviar notificación al admin: {str(e)}")


@receiver(post_save, sender="taller.Empresa")
def verificar_vencimiento_suscripcion(sender, instance, **kwargs):
    """
    Verificar si la suscripción está vencida y actualizar estado
    """
    from django.utils import timezone

    if instance.suscripcion_activa and instance.fecha_fin:
        if instance.fecha_fin < timezone.now():
            # Suscripción vencida
            instance.suscripcion_activa = False
            instance.save(update_fields=["suscripcion_activa"])
            print(f"⚠️ Suscripción vencida para {instance.nombre_taller}")


@receiver(post_save, sender="allauth.account.models.EmailAddress")
def registrar_email_confirmado_embudo(sender, instance, **kwargs):
    """
    ✅ Registra en el embudo cuando se confirma un email.

    Se dispara cuando Allauth marca un EmailAddress como verified=True
    """
    if instance.verified:
        try:
            from taller.services.registro_embudo_service import registrar_email_confirmado

            registrar_email_confirmado(instance.user)
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"[Signals] Error registrando email confirmado en embudo: {e}")


@receiver(user_logged_in)
def registrar_primer_login_embudo(sender, request, user, **kwargs):
    """
    ✅ Registra en el embudo cuando un usuario hace login por primera vez.
    """
    try:
        from taller.services.registro_embudo_service import registrar_primer_login

        registrar_primer_login(user)
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"[Signals] Error registrando primer login en embudo: {e}")
