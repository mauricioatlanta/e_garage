from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from core.models import TenantScoped

from .order import CommerceOrder


def _validate_card_last4(value):
    """Acepta exactamente 4 dígitos o cadena vacía."""
    if value and not (len(value) == 4 and value.isdigit()):
        raise ValidationError(
            "card_last4 debe ser exactamente 4 dígitos numéricos o estar vacío."
        )


class CommercePaymentTransaction(TenantScoped):
    """
    Registro de la transacción de pago asociada a un CommerceOrder.

    Inmutable en admin. El servicio puede actualizar confirmed_at y status
    vía save(update_fields=[...]) en transiciones controladas.
    Nunca almacena PAN completo, CVV ni secretos.
    """

    INITIATED = "initiated"
    AUTHORIZED = "authorized"
    FAILED = "failed"
    REFUNDED = "refunded"
    PENDING_VERIFICATION = "pending_verification"

    STATUS_CHOICES = [
        (INITIATED, "Iniciado"),
        (AUTHORIZED, "Autorizado"),
        (FAILED, "Fallido"),
        (REFUNDED, "Devuelto"),
        (PENDING_VERIFICATION, "Pendiente de verificación"),
    ]

    order = models.ForeignKey(
        CommerceOrder,
        on_delete=models.PROTECT,
        related_name="payment_transactions",
    )
    gateway = models.CharField(max_length=30)
    gateway_token = models.CharField(max_length=255, blank=True, default="")
    gateway_ref = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    currency = models.CharField(max_length=3, default="CLP")
    raw_response = models.JSONField(default=dict, blank=True)
    card_last4 = models.CharField(
        max_length=4,
        blank=True,
        default="",
        validators=[_validate_card_last4],
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantScoped.Meta):
        verbose_name = "Transacción de pago"
        verbose_name_plural = "Transacciones de pago"
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.order_id and self.empresa_id:
            if self.empresa_id != self.order.empresa_id:
                raise ValidationError(
                    "La empresa de la transacción debe coincidir con la del pedido."
                )

    @property
    def initiated_at(self):
        return self.created_at

    def __str__(self):
        return f"{self.gateway} [{self.status}] — Pedido {self.order.order_number}"


class PaymentAttempt(TenantScoped):
    """
    Registro inmutable de cada intento de pago para un CommerceOrder.

    Un pedido puede tener N intentos (rechazos, timeouts, cancelaciones) antes
    del intento exitoso. Cada intento es un registro independiente e inmutable:
    no se modifica ni elimina una vez creado.

    attempt_number se auto-asigna secuencialmente por pedido si no se provee.
    """

    INITIATED = "initiated"
    AUTHORIZED = "authorized"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PENDING_VERIFICATION = "pending_verification"

    STATUS_CHOICES = [
        (INITIATED, "Iniciado"),
        (AUTHORIZED, "Autorizado"),
        (FAILED, "Fallido"),
        (CANCELLED, "Cancelado"),
        (PENDING_VERIFICATION, "Pendiente de verificación"),
    ]

    order = models.ForeignKey(
        CommerceOrder,
        on_delete=models.PROTECT,
        related_name="payment_attempts",
    )
    attempt_number = models.PositiveSmallIntegerField()
    gateway = models.CharField(max_length=30)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    gateway_token = models.CharField(max_length=255, blank=True, default="")
    gateway_ref = models.CharField(max_length=100, blank=True, default="")
    raw_status = models.CharField(max_length=50, blank=True, default="")
    error_code = models.CharField(max_length=50, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantScoped.Meta):
        verbose_name = "Intento de pago"
        verbose_name_plural = "Intentos de pago"
        ordering = ["order", "attempt_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "attempt_number"],
                name="unique_attempt_number_per_order",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.pk and not self.attempt_number:
            last = (
                PaymentAttempt.objects.filter(order=self.order)
                .order_by("-attempt_number")
                .first()
            )
            self.attempt_number = (last.attempt_number + 1) if last else 1
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        raise TypeError("PaymentAttempt es inmutable y no puede eliminarse.")

    def clean(self):
        super().clean()
        if self.pk is not None:
            raise ValidationError(
                "PaymentAttempt es inmutable y no puede modificarse."
            )
        if self.order_id and self.empresa_id:
            if self.empresa_id != self.order.empresa_id:
                raise ValidationError(
                    "La empresa del intento debe coincidir con la del pedido."
                )

    def __str__(self):
        return (
            f"Intento #{self.attempt_number} [{self.gateway} {self.status}]"
            f" — Pedido {self.order.order_number}"
        )
