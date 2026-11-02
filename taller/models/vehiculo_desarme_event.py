"""
VehiculoDesarmeEvent — Registro append-only de hechos operacionales de un vehículo de desarme.

Diferencias con VehicleFinancialEvent (que también existe):
  - VehicleFinancialEvent registra movimientos de dinero (compra, venta, ajuste).
  - VehiculoDesarmeEvent registra hechos del ciclo operacional (revisión, desmontaje,
    publicación, cambios de estado operativo).

TenantScoped aporta: empresa (FK), created_at, updated_at.
No mezclar AuditMixin — duplicaría created_at/updated_at.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from core.models import TenantScoped


class TipoEventoDesarme(models.TextChoices):
    VEHICULO_CREADO            = "VEHICULO_CREADO",            "Vehículo creado"
    ESTADO_OPERATIVO_CAMBIADO  = "ESTADO_OPERATIVO_CAMBIADO",  "Estado operativo cambiado"
    REVISION_INICIADA          = "REVISION_INICIADA",          "Revisión iniciada"
    REVISION_FINALIZADA        = "REVISION_FINALIZADA",        "Revisión finalizada"
    PIEZA_CONFIRMADA           = "PIEZA_CONFIRMADA",           "Pieza confirmada"
    PIEZA_DESCARTADA           = "PIEZA_DESCARTADA",           "Pieza descartada"
    PIEZA_DESMONTADA           = "PIEZA_DESMONTADA",           "Pieza desmontada"
    PIEZA_ALMACENADA           = "PIEZA_ALMACENADA",           "Pieza almacenada"
    PIEZA_PUBLICADA            = "PIEZA_PUBLICADA",            "Pieza publicada"
    PIEZA_DESPUBLICADA         = "PIEZA_DESPUBLICADA",         "Pieza despublicada"
    PIEZA_RESERVADA            = "PIEZA_RESERVADA",            "Pieza reservada"
    PIEZA_VENDIDA              = "PIEZA_VENDIDA",              "Pieza vendida"
    VENTA_ANULADA              = "VENTA_ANULADA",              "Venta anulada"
    COSTO_REGISTRADO           = "COSTO_REGISTRADO",           "Costo registrado"
    CIERRE_INICIADO            = "CIERRE_INICIADO",            "Cierre iniciado"
    VEHICULO_CERRADO           = "VEHICULO_CERRADO",           "Vehículo cerrado"
    MIGRACION_ESTADO_INICIAL       = "MIGRACION_ESTADO_INICIAL",       "Migración — estado inicial inferido"
    SESION_DESPIECE_FINALIZADA     = "SESION_DESPIECE_FINALIZADA",     "Sesión de despiece finalizada"


class VehiculoDesarmeEvent(TenantScoped):
    """
    Evento operacional del ciclo de vida de un vehículo de desarme.

    Invariantes:
    - La empresa del evento coincide con la del vehículo.
    - Si existe pieza, pertenece al mismo vehículo y empresa.
    - Si existe documento, pertenece a la misma empresa.
    - metadata es siempre un dict.
    - idempotency_key es único por empresa (cuando no es null).

    Este modelo es append-only: los eventos no se modifican ni eliminan
    en operación normal.
    """

    vehiculo = models.ForeignKey(
        "taller.VehiculoDesarme",
        on_delete=models.CASCADE,
        related_name="eventos_operacionales",
    )
    pieza = models.ForeignKey(
        "taller.PiezaDesarme",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_operacionales",
    )
    documento = models.ForeignKey(
        "taller.Documento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_desarme",
    )
    tipo = models.CharField(
        max_length=40,
        choices=TipoEventoDesarme.choices,
        db_index=True,
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Contexto adicional del evento. Ej: {"from": "INGRESADO", "to": "EN_REVISION"}',
    )
    idempotency_key = models.CharField(
        max_length=160,
        null=True,
        blank=True,
        help_text="Clave única por tenant para evitar duplicados en reintento de operaciones.",
    )
    occurred_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Momento en que ocurrió el hecho de negocio (puede diferir de created_at).",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="eventos_desarme_creados",
        help_text="Usuario que originó el evento (null para eventos automáticos del sistema).",
    )

    def clean(self):
        super().clean()
        # Empresa del evento = empresa del vehículo
        if self.vehiculo_id and self.empresa_id:
            if self.vehiculo.empresa_id != self.empresa_id:
                raise ValidationError(
                    "La empresa del evento no coincide con la empresa del vehículo."
                )
        # Si hay pieza, verificar empresa primero (violación más grave), luego vehículo
        if self.pieza_id:
            if self.pieza.empresa_id != self.empresa_id:
                raise ValidationError(
                    "La pieza referenciada no pertenece a la misma empresa del evento."
                )
            if self.pieza.vehiculo_desarme_id != self.vehiculo_id:
                raise ValidationError(
                    "La pieza referenciada no pertenece al vehículo de este evento."
                )
        # Si hay documento, debe pertenecer a la misma empresa
        if self.documento_id:
            if self.documento.empresa_id != self.empresa_id:
                raise ValidationError(
                    "El documento referenciado no pertenece a la misma empresa del evento."
                )
        # metadata debe ser dict
        if not isinstance(self.metadata, dict):
            raise ValidationError({"metadata": "metadata debe ser un diccionario JSON."})

    class Meta(TenantScoped.Meta):
        verbose_name = "Evento operacional de desarme"
        verbose_name_plural = "Eventos operacionales de desarme"
        ordering = ["occurred_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "idempotency_key"],
                condition=Q(idempotency_key__isnull=False),
                name="uniq_desarme_event_idempotency_tenant",
            ),
        ]
        indexes = [
            models.Index(
                fields=["empresa", "vehiculo", "occurred_at"],
                name="desarme_ev_emp_veh_occ_idx",
            ),
            models.Index(
                fields=["empresa", "tipo", "occurred_at"],
                name="desarme_ev_emp_tipo_occ_idx",
            ),
        ]

    def __str__(self):
        return f"[{self.tipo}] {self.vehiculo_id} @ {self.occurred_at:%Y-%m-%d %H:%M}"
