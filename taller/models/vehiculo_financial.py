from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.utils import timezone

from .vehiculo_desarme import VehiculoDesarme


class VehiculoFinancialSnapshot(models.Model):
    """Snapshot financiero instantáneo de un vehículo de desarme.

    Se usa para conservar historiales y alimentar dashboards/timelines.
    """

    vehiculo_desarme = models.ForeignKey(VehiculoDesarme, on_delete=models.CASCADE, related_name="financial_snapshots")
    empresa = models.ForeignKey("taller.Empresa", on_delete=models.CASCADE, related_name="vehiculo_snapshots")
    fecha = models.DateTimeField(default=timezone.now, db_index=True)

    inversion_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    ingresos_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    costo_vendido = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    ganancia = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    roi_pct = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"))
    recuperacion_pct = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"))

    inventario_contable = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    inventario_mercado = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    dias_recuperacion = models.IntegerField(null=True, blank=True)
    health_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))

    # Estado lógico del stream financiero usado para construir el snapshot
    source_event_count = models.IntegerField(default=0, db_index=True)

    # Fingerprint deterministicamente reproducible
    snapshot_hash = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vehiculo Financial Snapshot"
        verbose_name_plural = "Vehiculo Financial Snapshots"

        constraints = [
            models.UniqueConstraint(
                fields=["snapshot_hash"],
                name="unique_vehicle_snapshot_hash",
            )
        ]

        indexes = [
            models.Index(fields=["vehiculo_desarme", "fecha"]),
            models.Index(fields=["vehiculo_desarme", "source_event_count"]),
            models.Index(fields=["snapshot_hash"]),
        ]


class VehicleFinancialEvent(models.Model):
    """Evento financiero atómico asociado a un vehículo.

    Ejemplos: compra vehículo, costo de grúa, venta de pieza (linea documento), ajuste.
    """

    TIPO_CHOICES = [
        ("COMPRA", "Compra Vehículo"),
        ("COSTO", "Costo Operativo"),
        ("VENTA", "Venta Pieza"),
        ("AJUSTE", "Ajuste"),
        ("OTRO", "Otro"),
    ]

    EVENT_TYPE_CHOICES = [
        ("COMPRA", "Compra"),
        ("COSTO", "Costo"),
        ("VENTA", "Venta"),
        ("AJUSTE", "Ajuste"),
        ("OTRO", "Otro"),
        ("UNKNOWN", "Unknown"),
    ]

    EVENT_TYPE_VENTA = "VENTA"
    EVENT_TYPE_COMPRA = "COMPRA"
    EVENT_TYPE_COSTO = "COSTO"
    EVENT_TYPE_AJUSTE = "AJUSTE"
    EVENT_TYPE_OTRO = "OTRO"
    EVENT_TYPE_UNKNOWN = "UNKNOWN"

    vehiculo_desarme = models.ForeignKey(VehiculoDesarme, on_delete=models.CASCADE, related_name="financial_events")
    empresa = models.ForeignKey("taller.Empresa", on_delete=models.CASCADE, related_name="financial_events")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, db_index=True)
    fecha = models.DateTimeField(default=timezone.now, db_index=True)
    monto = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    descripcion = models.TextField(blank=True, null=True)

    # referencias opcionales
    documento = models.ForeignKey(
        "taller.Documento",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="vehiculo_financial_events",
    )
    pieza_desarme = models.ForeignKey(
        "taller.PiezaDesarme",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="financial_events",
    )

    # Nueva identidad: preferir `linea_repuesto` como referencia única del evento
    linea_repuesto = models.ForeignKey(
        "taller.LineaRepuesto",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="financial_events",
        help_text="Referencia a la línea de repuesto (identidad del evento)",
    )

    # Metadatos de versionado/identificación del evento
    event_hash = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    event_version = models.IntegerField(default=1)
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPE_CHOICES,
        default=EVENT_TYPE_UNKNOWN,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vehicle Financial Event"
        verbose_name_plural = "Vehicle Financial Events"
        constraints = [
            models.UniqueConstraint(
                fields=["event_hash"],
                condition=Q(event_hash__isnull=False),
                name="uniq_vehicle_financial_event_hash",
            )
        ]
        indexes = [
            models.Index(fields=["vehiculo_desarme", "tipo", "fecha"]),
            models.Index(fields=["linea_repuesto"]),
            models.Index(fields=["event_hash"]),
            models.Index(fields=["event_type"]),
        ]
