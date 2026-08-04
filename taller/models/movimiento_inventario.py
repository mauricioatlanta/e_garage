from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class MovimientoInventario(models.Model):
    class TipoMovimiento(models.TextChoices):
        SNAPSHOT_INICIAL = "SNAPSHOT_INICIAL", "Saldo inicial"
        EMISION = "EMISION", "Emisión de documento"
        ANULACION = "ANULACION", "Anulación de documento"
        EDICION = "EDICION", "Edición de documento emitido"
        AJUSTE_POSITIVO = "AJUSTE_POSITIVO", "Ajuste positivo"
        AJUSTE_NEGATIVO = "AJUSTE_NEGATIVO", "Ajuste negativo"
        RECEPCION = "RECEPCION", "Recepción de inventario"

    class OrigenStock(models.TextChoices):
        STOCK_BODEGA = "STOCK_BODEGA", "Stock de bodega"
        DESARME = "DESARME", "Pieza de desarme"

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.PROTECT,
        related_name="movimientos_inventario",
    )
    tipo = models.CharField(max_length=24, choices=TipoMovimiento.choices)
    origen_stock = models.CharField(max_length=20, choices=OrigenStock.choices)

    repuesto = models.ForeignKey(
        "taller.Repuesto",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_inventario",
    )
    pieza_desarme = models.ForeignKey(
        "taller.PiezaDesarme",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_inventario",
    )
    documento = models.ForeignKey(
        "taller.Documento",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_inventario",
    )
    linea_repuesto = models.ForeignKey(
        "taller.LineaRepuesto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_inventario",
    )

    cantidad_delta = models.IntegerField()
    saldo_resultante = models.IntegerField()

    costo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    idempotency_key = models.CharField(max_length=64, unique=True)
    event_version = models.PositiveSmallIntegerField(default=1)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    notas = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = "taller"
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ["-created_at"]
        constraints = [
            # origen_stock debe coincidir con la FK informada (exactamente una).
            models.CheckConstraint(
                name="inventario_exactamente_un_origen",
                check=(
                    models.Q(
                        origen_stock="STOCK_BODEGA",
                        repuesto_id__isnull=False,
                        pieza_desarme_id__isnull=True,
                    )
                    | models.Q(
                        origen_stock="DESARME",
                        repuesto_id__isnull=True,
                        pieza_desarme_id__isnull=False,
                    )
                ),
            ),
            models.CheckConstraint(
                name="inventario_delta_no_cero",
                check=~models.Q(cantidad_delta=0),
            ),
            models.CheckConstraint(
                name="inventario_saldo_no_negativo",
                check=models.Q(saldo_resultante__gte=0),
            ),
        ]
        indexes = [
            models.Index(
                fields=["empresa", "repuesto", "-created_at"],
                name="inv_emp_rep_fecha_idx",
            ),
            models.Index(
                fields=["empresa", "pieza_desarme", "-created_at"],
                name="inv_emp_pieza_fecha_idx",
            ),
            models.Index(
                fields=["documento", "tipo"],
                name="inv_doc_tipo_idx",
            ),
        ]

    def clean(self):
        has_repuesto = self.repuesto_id is not None
        has_pieza = self.pieza_desarme_id is not None

        if has_repuesto and has_pieza:
            raise ValidationError(
                "Solo uno de repuesto o pieza_desarme puede estar informado."
            )
        if not has_repuesto and not has_pieza:
            raise ValidationError("Debe informar repuesto o pieza_desarme.")
        if self.origen_stock == self.OrigenStock.STOCK_BODEGA and not has_repuesto:
            raise ValidationError("origen_stock STOCK_BODEGA requiere repuesto.")
        if self.origen_stock == self.OrigenStock.DESARME and not has_pieza:
            raise ValidationError("origen_stock DESARME requiere pieza_desarme.")
        if self.cantidad_delta == 0:
            raise ValidationError("cantidad_delta no puede ser cero.")
        if self.saldo_resultante < 0:
            raise ValidationError("saldo_resultante no puede ser negativo.")

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError(
                "MovimientoInventario es inmutable; registra un movimiento compensatorio."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("MovimientoInventario no puede eliminarse.")

    def __str__(self):
        return f"{self.tipo} {self.origen_stock} Δ{self.cantidad_delta} → {self.saldo_resultante}"
