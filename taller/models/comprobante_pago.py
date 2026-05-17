from django.db import models
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.utils.payment_config import normalize_company_plan


class ComprobantePago(models.Model):
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente de Revisión"),
        ("aprobado", "Aprobado"),
        ("rechazado", "Rechazado"),
    ]

    METODO_PAGO_CHOICES = [
        ("transferencia", "Transferencia Bancaria"),
        ("webpay", "WebPay Plus"),
        ("paypal", "PayPal"),
        ("mercadopago", "MercadoPago"),
        ("otro", "Otro"),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="comprobantes")
    fecha_subida = models.DateTimeField(default=timezone.now)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default="CLP")

    # Archivos
    comprobante = models.ImageField(
        upload_to="comprobantes/", help_text="Imagen del comprobante de pago"
    )
    numero_transaccion = models.CharField(
        max_length=100, blank=True, help_text="Número de transacción o referencia"
    )

    # Estados
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="pendiente")
    fecha_procesado = models.DateTimeField(null=True, blank=True)
    procesado_por = models.CharField(max_length=100, blank=True)

    # Notas
    descripcion = models.TextField(blank=True, help_text="Descripción del pago")
    notas_admin = models.TextField(blank=True, help_text="Notas administrativas")

    # Configuración de plan
    plan_solicitado = models.CharField(max_length=20, choices=Empresa.PLAN_CHOICES, default="basic")
    meses_pagados = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-fecha_subida"]
        verbose_name = "Comprobante de Pago"
        verbose_name_plural = "Comprobantes de Pago"

    def __str__(self):
        return f"Pago {self.empresa.nombre_taller} - ${self.monto} ({self.estado})"

    def aprobar(self, procesado_por="Sistema"):
        """Aprobar el comprobante y extender suscripción"""
        self.estado = "aprobado"
        self.fecha_procesado = timezone.now()
        self.procesado_por = procesado_por

        # Detectar si es nueva suscripción, cambio de plan o renovación
        plan_anterior = normalize_company_plan(self.empresa.plan)
        plan_nuevo = normalize_company_plan(self.plan_solicitado)
        es_nueva_suscripcion = not self.empresa.suscripcion_activa or self.empresa.plan == "trial"
        es_cambio_plan = (
            self.empresa.suscripcion_activa
            and plan_anterior != plan_nuevo
            and plan_anterior != "trial"
        )

        # Extender suscripción de la empresa
        dias_extension = self.meses_pagados * 30
        # 🔒 ANTI-DUPLICADO: No enviar notificación aquí, la enviaremos después
        # Esto evita doble notificación si extender_suscripcion() también notifica
        self.empresa.extender_suscripcion(dias_extension, enviar_notificacion=False)
        self.plan_solicitado = plan_nuevo
        self.empresa.plan = plan_nuevo
        self.empresa.valor_mensual = self.monto / self.meses_pagados
        self.empresa.save()

        # 🔒 IDEMPOTENCIA: Pasar ID del comprobante para tracking en DB
        # Resetear flag de notificación antes de notificar
        if hasattr(self.empresa, "_admin_whatsapp_notified"):
            delattr(self.empresa, "_admin_whatsapp_notified")

        # Pasar ID del comprobante para idempotencia
        self.empresa._current_comprobante_pago_id = self.id

        self.save()

        # Enviar notificaciones automáticas (Email + WhatsApp)
        try:
            from taller.utils.notificaciones_suscripcion import (
                notificar_cambio_plan,
                notificar_nueva_suscripcion,
                notificar_renovacion_exitosa,
            )

            if es_nueva_suscripcion:
                # A. NUEVA SUSCRIPCIÓN
                notificar_nueva_suscripcion(
                    empresa=self.empresa,
                    plan=plan_nuevo,
                    monto=self.monto,
                    es_nueva_empresa=es_nueva_suscripcion,
                )
            elif es_cambio_plan:
                # B. CAMBIO DE PLAN
                notificar_cambio_plan(
                    empresa=self.empresa,
                    plan_anterior=plan_anterior,
                    plan_nuevo=plan_nuevo,
                    monto=self.monto,
                    fecha_inicio=self.empresa.fecha_inicio,
                )
            else:
                # C. RENOVACIÓN EXITOSA
                notificar_renovacion_exitosa(
                    empresa=self.empresa,
                    plan=plan_nuevo,
                    monto=self.monto,
                    dias_renovados=dias_extension,
                )
        except Exception as e:
            print(f"⚠️ Error al enviar notificaciones: {str(e)}")
            # Si fallan las notificaciones nuevas, usar el método antiguo como fallback
            self.enviar_notificacion_aprobacion()

    def rechazar(self, motivo="", procesado_por="Sistema"):
        """Rechazar el comprobante"""
        self.estado = "rechazado"
        self.fecha_procesado = timezone.now()
        self.procesado_por = procesado_por
        self.notas_admin = motivo
        self.save()

        # Enviar notificación de rechazo
        self.enviar_notificacion_rechazo()

    def enviar_notificacion_aprobacion(self):
        """Envía notificación de que el pago fue aprobado"""
        from django.conf import settings
        from taller.utils.email_helper import (
            get_branded_from_email,
            get_support_reply_to,
            send_email_with_reply_to,
        )

        subject = f"✅ Pago Aprobado - {self.empresa.nombre_taller}"
        fecha_vencimiento = (
            self.empresa.fecha_fin.strftime("%d/%m/%Y") if self.empresa.fecha_fin else "No definida"
        )
        plan_display = dict(self.empresa.PLAN_CHOICES).get(
            self.plan_solicitado, self.plan_solicitado
        )

        message = f"""
        ¡Excelente! Tu pago ha sido aprobado.

        Detalles:
        - Empresa: {self.empresa.nombre_taller}
        - Monto: ${self.monto} {self.moneda}
        - Plan: {plan_display}
        - Nueva fecha de vencimiento: {fecha_vencimiento}

        Ya puedes continuar usando eGarage sin restricciones.

        ¡Gracias por confiar en nosotros!
        """

        try:
            send_email_with_reply_to(
                subject=subject,
                message=message,
                from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                recipient_list=[self.empresa.email, self.empresa.user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error enviando email de aprobación: {e}")

    def enviar_notificacion_rechazo(self):
        """Envía notificación de que el pago fue rechazado"""
        from django.conf import settings
        from taller.utils.email_helper import get_branded_from_email, send_email_with_reply_to

        support_whatsapp_display = getattr(
            settings, "SUPPORT_WHATSAPP_DISPLAY", "+56 9 5357 4683"
        )

        subject = f"❌ Pago Rechazado - {self.empresa.nombre_taller}"
        message = f"""
        Tu comprobante de pago ha sido rechazado.

        Detalles:
        - Empresa: {self.empresa.nombre_taller}
        - Monto: ${self.monto} {self.moneda}
        - Motivo: {self.notas_admin}

        Por favor, revisa el comprobante y vuelve a subirlo o contáctanos para más información.

        WhatsApp: {support_whatsapp_display}
        Email: {get_support_reply_to()}
        """

        try:
            send_email_with_reply_to(
                subject=subject,
                message=message,
                from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                recipient_list=[self.empresa.email, self.empresa.user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error enviando email de rechazo: {e}")

    def enviar_notificacion_admin(self):
        """Envía notificación al admin de nuevo comprobante"""
        from django.conf import settings
        from taller.utils.email_helper import (
            get_branded_from_email,
            get_support_reply_to,
            send_email_with_reply_to,
        )

        plan_display = dict(self.empresa.PLAN_CHOICES).get(
            self.plan_solicitado, self.plan_solicitado
        )
        metodo_display = dict(self.METODO_PAGO_CHOICES).get(self.metodo_pago, self.metodo_pago)

        subject = f"💰 Nuevo Comprobante de Pago - {self.empresa.nombre_taller}"
        message = f"""
        Se ha subido un nuevo comprobante de pago.

        Detalles:
        - Empresa: {self.empresa.nombre_taller}
        - Usuario: {self.empresa.user.username} ({self.empresa.user.email})
        - Monto: ${self.monto} {self.moneda}
        - Plan solicitado: {plan_display}
        - Método de pago: {metodo_display}
        - Número transacción: {self.numero_transaccion}

        Revisa el comprobante en el panel de administración.
        """

        try:
            send_email_with_reply_to(
                subject=subject,
                message=message,
                from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                recipient_list=[getattr(settings, "ADMIN_EMAIL", None) or get_support_reply_to()],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error enviando email al admin: {e}")

    def save(self, *args, **kwargs):
        """Al crear nuevo comprobante, enviar notificación al admin"""
        is_new = not self.pk
        super().save(*args, **kwargs)

        if is_new:
            self.enviar_notificacion_admin()

        from taller.services.suscripcion_transaccion_service import sync_from_comprobante_pago

        sync_from_comprobante_pago(self)
