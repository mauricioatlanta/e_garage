"""
SugerenciaPiezaDesarme: registro persistente del progreso de revisión.
PiezaDesarme real solo se crea cuando el usuario confirma cada sugerencia.
TenantScoped aporta: empresa (FK), created_at, updated_at.
"""
from django.db import models

from core.models import TenantScoped
from taller.models.pieza_desarme import CONDICION_CHOICES


class SugerenciaPiezaDesarme(TenantScoped):
    PENDIENTE  = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    DESCARTADA = "DESCARTADA"
    ESTADO_CHOICES = [
        (PENDIENTE,  "Pendiente"),
        (CONFIRMADA, "Confirmada"),
        (DESCARTADA, "Descartada"),
    ]

    vehiculo_desarme = models.ForeignKey(
        "taller.VehiculoDesarme",
        on_delete=models.CASCADE,
        related_name="sugerencias_piezas",
    )
    # Snapshot del catálogo al momento de sugerir (sobrevive a cambios del catálogo)
    codigo = models.CharField(max_length=100)
    nombre = models.CharField(max_length=255)
    zona   = models.CharField(max_length=50, blank=True, default="")

    precio_sugerido    = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    condicion_sugerida = models.CharField(max_length=10, choices=CONDICION_CHOICES, null=True, blank=True)

    estado = models.CharField(
        max_length=12, choices=ESTADO_CHOICES, default=PENDIENTE, db_index=True
    )
    # Referencia a la PiezaDesarme real creada al confirmar (null si PENDIENTE/DESCARTADA)
    pieza_creada = models.ForeignKey(
        "taller.PiezaDesarme",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sugerencia_origen",
    )

    class Meta(TenantScoped.Meta):
        verbose_name = "Sugerencia pieza desarme"
        verbose_name_plural = "Sugerencias piezas desarme"
        constraints = [
            models.UniqueConstraint(
                fields=["vehiculo_desarme", "codigo"],
                name="unique_sugerencia_por_vehiculo_desarme",
            )
        ]
        indexes = [
            models.Index(fields=["empresa", "vehiculo_desarme"],           name="sug_pieza_emp_veh_d_idx"),
            models.Index(fields=["empresa", "vehiculo_desarme", "estado"], name="sug_pieza_emp_veh_d_est_idx"),
        ]

    def __str__(self):
        return f"{self.codigo} — {self.nombre} [{self.estado}]"
