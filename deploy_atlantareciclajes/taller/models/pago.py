from django.db import models
from django.utils import timezone


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

        # Actualizar empresa
        self.empresa.extender_suscripcion(dias=dias)
        self.empresa.plan = self.plan
        self.empresa.valor_mensual = self.monto
        self.empresa.save()

        # Actualizar estado del pago
        self.estado = "procesado"
        self.fecha_verificacion = timezone.now()
        self.verificado_por = admin_user
        self.save()

        # 📧 ENVIAR EMAIL DE CONFIRMACIÓN
        try:
            # Determinar idioma según país
            language = "es" if self.empresa.pais in {"CL", "MX"} else "en"

            # Determinar moneda
            moneda = (
                "CLP"
                if self.empresa.pais == "CL"
                else "MXN" if self.empresa.pais == "MX" else "USD"
            )

            # Asunto según idioma
            if language == "en":
                subject = "✅ Payment Confirmed - eGarage"
            else:
                subject = "✅ Pago Confirmado - eGarage"

            # Renderizar HTML
            html_message = render_to_string(
                "email/pago_confirmado.html",
                {
                    "empresa": self.empresa,
                    "plan": self.plan,
                    "monto": self.monto,
                    "moneda": moneda,
                    "fecha_fin": self.empresa.fecha_fin,
                    "language": language,
                },
            )

            # Enviar email
            send_mail(
                subject=subject,
                message="",  # Text version (vacío, usamos HTML)
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.empresa.email],
                html_message=html_message,
                fail_silently=False,
            )

            print(f"✅ Email de confirmación enviado a {self.empresa.email}")

        except Exception as e:
            print(f"⚠️ Error al enviar email de confirmación: {str(e)}")
            # No fallar si el email falla, el pago ya está aprobado

    def rechazar_pago(self, admin_user, razon=""):
        """
        Rechazar pago
        """
        self.estado = "rechazado"
        self.fecha_verificacion = timezone.now()
        self.verificado_por = admin_user
        self.notas = razon
        self.save()
