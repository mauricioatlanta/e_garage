import uuid

from django.db import models
from django.utils import timezone

from taller.models.empresa import Empresa


class SuscripcionTransaccion(models.Model):
    SOURCE_CHOICES = [
        ("legacy_pago_pendiente", "Legacy PagoPendiente"),
        ("legacy_comprobante_pago", "Legacy ComprobantePago"),
        ("flow", "Flow"),
        ("mercadopago", "MercadoPago"),
        ("paypal", "PayPal"),
        ("transferencia_manual", "Transferencia Manual"),
        ("otro", "Otro"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("processing", "En proceso"),
        ("approved", "Aprobada"),
        ("rejected", "Rechazada"),
        ("cancelled", "Cancelada"),
        ("error", "Error"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("transferencia", "Transferencia Bancaria"),
        ("flow", "Flow"),
        ("webpay", "WebPay Plus"),
        ("khipu", "Khipu"),
        ("mercadopago", "MercadoPago"),
        ("paypal", "PayPal"),
        ("otro", "Otro"),
    ]

    BILLING_CYCLE_CHOICES = [
        ("mensual", "Mensual"),
        ("semestral", "Semestral"),
        ("anual", "Anual"),
        ("otro", "Otro"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, related_name="suscripcion_transacciones"
    )
    source_type = models.CharField(max_length=40, choices=SOURCE_CHOICES, db_index=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    raw_status = models.CharField(max_length=50, blank=True)

    payment_method = models.CharField(
        max_length=30, choices=PAYMENT_METHOD_CHOICES, default="transferencia"
    )
    billing_cycle = models.CharField(
        max_length=20, choices=BILLING_CYCLE_CHOICES, default="mensual"
    )
    plan_code = models.CharField(max_length=20, choices=Empresa.PLAN_CHOICES, default="basic")
    months_paid = models.PositiveIntegerField(default=1)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="CLP")

    reference = models.CharField(max_length=120, blank=True, db_index=True)
    external_transaction_id = models.CharField(max_length=120, blank=True, db_index=True)
    checkout_url = models.URLField(blank=True)
    customer_email = models.EmailField(blank=True)
    receipt_path = models.CharField(max_length=500, blank=True)

    description = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    gateway_payload = models.JSONField(default=dict, blank=True)

    submitted_at = models.DateTimeField(default=timezone.now, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    subscription_applied_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    legacy_pago_pendiente = models.OneToOneField(
        "taller.PagoPendiente",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="suscripcion_transaccion",
    )
    legacy_comprobante_pago = models.OneToOneField(
        "taller.ComprobantePago",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="suscripcion_transaccion",
    )

    class Meta:
        ordering = ["-submitted_at", "-created_at"]
        verbose_name = "Transacción de Suscripción"
        verbose_name_plural = "Transacciones de Suscripción"
        indexes = [
            models.Index(fields=["empresa", "status"], name="t_susc_emp_b56f73_idx"),
            models.Index(fields=["payment_method", "status"], name="t_susc_pay_461adc_idx"),
            models.Index(fields=["source_type", "submitted_at"], name="t_susc_src_e43df4_idx"),
        ]

    @property
    def metodo(self):
        return self.payment_method

    @property
    def estado(self):
        return self.status

    @property
    def monto(self):
        return self.amount

    @property
    def moneda(self):
        return self.currency

    @property
    def external_id(self):
        return self.external_transaction_id

    @property
    def payload_historico(self):
        return self.gateway_payload

    @property
    def monto_formateado(self):
        amount = self.amount or 0
        decimals = 0 if (self.currency or "").upper() == "CLP" else 2
        amount_format = f"{amount:,.{decimals}f}"
        return f"${amount_format} {self.currency or 'CLP'}"

    def get_metodo_display(self):
        return self.get_payment_method_display()

    def get_estado_display(self):
        return self.get_status_display()

    def __str__(self):
        return (
            f"{self.empresa.nombre_taller} - {self.payment_method} - "
            f"${self.amount} {self.currency} ({self.status})"
        )
