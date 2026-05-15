from django.db import models
from django.utils import timezone

from taller.utils.payment_config import normalize_company_plan


class PagoPendiente(models.Model):
    """
    Registro de pagos pendientes de verificación
    Usado principalmente para Chile (transferencias bancarias)
    """

    ESTADO_CHOICES = [
        ("pendiente", "Pendiente de Verificación"),
        ("verificado", "Verificado"),
        ("rechazado", "Rechazado"),
        ("procesado", "Procesado - Suscripción Activada"),
    ]

    empresa = models.ForeignKey(
        "taller.Empresa", on_delete=models.CASCADE, related_name="pagos_pendientes"
    )
    plan = models.CharField(max_length=20)  # mensual, semestral, anual
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    comprobante = models.FileField(upload_to="comprobantes_pago/")

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="pendiente")
    fecha_subida = models.DateTimeField(default=timezone.now)
    fecha_verificacion = models.DateTimeField(null=True, blank=True)
    verificado_por = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pagos_verificados",
    )

    notas = models.TextField(blank=True, help_text="Notas del administrador")

    # Datos adicionales del pago
    referencia = models.CharField(max_length=100, blank=True)
    metodo_pago = models.CharField(
        max_length=50, default="transferencia"
    )  # transferencia, paypal, stripe

    class Meta:
        verbose_name = "Pago Pendiente"
        verbose_name_plural = "Pagos Pendientes"
        ordering = ["-fecha_subida"]

    def __str__(self):
        return f"{self.empresa.nombre_taller} - {self.plan} - ${self.monto} ({self.estado})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from taller.services.suscripcion_transaccion_service import sync_from_pago_pendiente

        sync_from_pago_pendiente(self)

    def aprobar_pago(self, admin_user):
        """
        Aprobar pago y activar suscripción
        📧 Envía email de confirmación al cliente
        """
        from django.conf import settings
        from django.core.mail import send_mail
        from django.template.loader import render_to_string

        dias_plan = {
            "mensual": 30,
            "semestral": 180,
            "anual": 365,
        }

        dias = dias_plan.get(self.plan, 30)

        # Detectar si es nueva suscripción, cambio de plan o renovación
        plan_nuevo = normalize_company_plan(self.plan)
        plan_anterior = self.empresa.plan
        es_nueva_suscripcion = not self.empresa.suscripcion_activa or self.empresa.plan == "trial"
        es_cambio_plan = (
            self.empresa.suscripcion_activa
            and plan_anterior != plan_nuevo
            and plan_anterior != "trial"
        )

        # Actualizar empresa
        # 🔒 IDEMPOTENCIA: Pasar ID del pago para tracking en DB
        # No enviar notificación aquí, se enviará después si corresponde
        self.empresa.extender_suscripcion(dias=dias, enviar_notificacion=False)

        # Resetear flag de notificación antes de notificar
        if hasattr(self.empresa, "_admin_whatsapp_notified"):
            delattr(self.empresa, "_admin_whatsapp_notified")

        # Pasar ID del pago para idempotencia
        self.empresa._current_pago_pendiente_id = self.id
        self.empresa.plan = plan_nuevo
        self.empresa.valor_mensual = self.monto
        self.empresa.save()

        # Actualizar estado del pago
        self.estado = "procesado"
        self.fecha_verificacion = timezone.now()
        self.verificado_por = admin_user
        self.save()

        # 📧 ENVIAR NOTIFICACIONES AUTOMÁTICAS (Email + WhatsApp)
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
                print(f"✅ Notificación de nueva suscripción enviada a {self.empresa.user.email}")
            elif es_cambio_plan:
                # B. CAMBIO DE PLAN
                notificar_cambio_plan(
                    empresa=self.empresa,
                    plan_anterior=plan_anterior,
                    plan_nuevo=plan_nuevo,
                    monto=self.monto,
                    fecha_inicio=self.empresa.fecha_inicio,
                )
                print(f"✅ Notificación de cambio de plan enviada a {self.empresa.user.email}")
            else:
                # C. RENOVACIÓN EXITOSA
                notificar_renovacion_exitosa(
                    empresa=self.empresa,
                    plan=plan_nuevo,
                    monto=self.monto,
                    dias_renovados=dias,
                )
                print(f"✅ Notificación de renovación exitosa enviada a {self.empresa.user.email}")

        except Exception as e:
            print(f"⚠️ Error al enviar notificaciones: {str(e)}")
            # No fallar si las notificaciones fallan, el pago ya está aprobado

    def rechazar_pago(self, admin_user, razon=""):
        """
        Rechazar pago
        """
        self.estado = "rechazado"
        self.fecha_verificacion = timezone.now()
        self.verificado_por = admin_user
        self.notas = razon
        self.save()
