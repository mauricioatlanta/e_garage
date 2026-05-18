from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.models.suscripcion_transaccion import SuscripcionTransaccion


class SubscriptionChange(models.Model):
    CHANGE_UPGRADE = "upgrade"
    CHANGE_DOWNGRADE = "downgrade"

    STATUS_PENDING = "pending"
    STATUS_SCHEDULED = "scheduled"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_FAILED = "failed"

    CHANGE_TYPE_CHOICES = [
        (CHANGE_UPGRADE, "Upgrade"),
        (CHANGE_DOWNGRADE, "Downgrade"),
    ]
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_SCHEDULED, "Programado"),
        (STATUS_COMPLETED, "Completado"),
        (STATUS_CANCELLED, "Cancelado"),
        (STATUS_FAILED, "Fallido"),
    ]

    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, related_name="subscription_changes"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requested_subscription_changes",
    )
    current_plan = models.CharField(max_length=20, choices=Empresa.PLAN_CHOICES)
    requested_plan = models.CharField(max_length=20, choices=Empresa.PLAN_CHOICES)
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    billing_cycle = models.CharField(max_length=20, default="monthly")
    prorated_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    currency = models.CharField(max_length=3, default="USD")
    scheduled_at = models.DateTimeField(null=True, blank=True, db_index=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    validation_snapshot = models.JSONField(default=dict, blank=True)
    transaction = models.ForeignKey(
        SuscripcionTransaccion,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subscription_changes",
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Cambio de Suscripción"
        verbose_name_plural = "Cambios de Suscripción"
        indexes = [
            models.Index(fields=["empresa", "status"], name="taller_subs_empresa_76b9f4_idx"),
            models.Index(
                fields=["change_type", "status", "scheduled_at"],
                name="taller_subs_change__3cf7f2_idx",
            ),
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa"],
                condition=Q(status__in=["pending", "scheduled"]),
                name="uniq_open_subscription_change_per_empresa",
            )
        ]

    def __str__(self):
        return (
            f"{self.empresa} - {self.current_plan} -> {self.requested_plan} "
            f"({self.status})"
        )

    @property
    def is_pending_downgrade(self):
        return self.change_type == self.CHANGE_DOWNGRADE and self.status == self.STATUS_SCHEDULED
