"""
Modelo PiezaDesarme: inventario físico de piezas extraídas de vehículos de desarme.
Sigue el patrón multi-tenant canónico (TenantScoped) como Vehiculo y Repuesto.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Index

from core.models import TenantScoped


# Estados de la partida (a nivel de registro completo)
ESTADO_DISPONIBLE = "DISPONIBLE"
ESTADO_RESERVADA = "RESERVADA"
ESTADO_VENDIDA = "VENDIDA"
ESTADO_DANADA = "DANADA"
ESTADO_SCRAP = "SCRAP"
ESTADO_FALTANTE = "FALTANTE"
ESTADO_PIEZA_CHOICES = [
    (ESTADO_DISPONIBLE, "Disponible"),
    (ESTADO_RESERVADA, "Reservada"),
    (ESTADO_VENDIDA, "Vendida"),
    (ESTADO_DANADA, "Dañada"),
    (ESTADO_SCRAP, "Scrap"),
    (ESTADO_FALTANTE, "Faltante"),
]

# Origen del precio (referencia catálogo vs sugerencia sistema vs manual)
ORIGEN_PRECIO_CATALOGO = "CATALOGO"
ORIGEN_PRECIO_MODELO = "MODELO"
ORIGEN_PRECIO_HISTORIAL = "HISTORIAL"
ORIGEN_PRECIO_MANUAL = "MANUAL"
ORIGEN_PRECIO_CHOICES = [
    (ORIGEN_PRECIO_CATALOGO, "Catálogo"),
    (ORIGEN_PRECIO_MODELO, "Modelo / IA"),
    (ORIGEN_PRECIO_HISTORIAL, "Historial"),
    (ORIGEN_PRECIO_MANUAL, "Manual"),
]


class PiezaDesarme(TenantScoped):
    """
    Partida de piezas extraídas de un vehículo de desarme.
    - Repuesto = catálogo/inventario bodega.
    - PiezaDesarme = unidad física en yarda con trazabilidad por vehículo.
    costo_asignado = costo unitario imputado (por unidad).
    estado_pieza VENDIDA = partida agotada (cantidad llegó a 0).
    """

    vehiculo = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.PROTECT,
        related_name="piezas_desarme",
        limit_choices_to={"tipo_uso": "DESARME"},
    )

    repuesto = models.ForeignKey(
        "taller.Repuesto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="piezas_desarme",
    )
    part = models.ForeignKey(
        "taller.Part",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="piezas_desarme",
    )

    codigo = models.CharField(max_length=100, db_index=True)
    nombre = models.CharField(max_length=255)
    cantidad = models.PositiveIntegerField(default=1)
    costo_asignado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Costo unitario imputado (por unidad).",
    )
    precio_venta_sugerido = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Precio base de venta (legado / catálogo). Se mantiene para compatibilidad.",
    )
    # Campos para valorización v4: referencia, sugerencia y trazabilidad
    precio_referencia = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Precio de referencia (catálogo / lista).",
    )
    precio_sugerido = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Precio sugerido por el sistema (modelo / IA / historial).",
    )
    origen_precio = models.CharField(
        max_length=20,
        choices=ORIGEN_PRECIO_CHOICES,
        null=True,
        blank=True,
        db_index=True,
        help_text="Origen del precio actual o de la última sugerencia.",
    )
    prioridad = models.PositiveSmallIntegerField(
        default=0,
        blank=True,
        help_text="Prioridad para ordenar sugerencias o alertas (mayor = más relevante).",
    )
    revisado = models.BooleanField(
        default=False,
        help_text="Indica si el precio fue revisado por un operador.",
    )
    fecha_revision = models.DateTimeField(null=True, blank=True)
    fecha_extraccion = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    estado_pieza = models.CharField(
        max_length=20,
        choices=ESTADO_PIEZA_CHOICES,
        default=ESTADO_DISPONIBLE,
        db_index=True,
    )
    ubicacion_fisica = models.CharField(max_length=120, null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    lado = models.CharField(max_length=50, null=True, blank=True)
    zona = models.CharField(max_length=50, null=True, blank=True)
    posicion = models.CharField(max_length=50, null=True, blank=True)

    def clean(self):
        super().clean()
        if not self.vehiculo_id:
            return
        # vehiculo debe ser tipo DESARME
        if self.vehiculo.tipo_uso != "DESARME":
            raise ValidationError(
                {"vehiculo": "El vehículo debe ser de tipo Desarme."}
            )
        # empresa coherente con vehículo
        if self.empresa_id and self.vehiculo.empresa_id != self.empresa_id:
            raise ValidationError(
                "La pieza y el vehículo deben pertenecer a la misma empresa."
            )
        # repuesto (si existe) misma empresa
        if self.repuesto_id and self.repuesto.empresa_id != self.empresa_id:
            raise ValidationError(
                "El repuesto referenciado debe pertenecer a la misma empresa."
            )
        # part: permitir catálogo global (empresa null) o misma empresa
        if self.part_id and getattr(self.part, "empresa_id", None) is not None and self.part.empresa_id != self.empresa_id:
            raise ValidationError(
                "El part referenciado debe ser de la misma empresa o catálogo global."
            )
        # estado_pieza VENDIDA solo cuando cantidad == 0 (ventas parciales no marcan VENDIDA)
        if self.estado_pieza == ESTADO_VENDIDA and self.cantidad != 0:
            raise ValidationError(
                {"estado_pieza": "Solo se puede marcar como Vendida cuando la cantidad es 0."}
            )

    class Meta(TenantScoped.Meta):
        verbose_name = "Pieza de desarme"
        verbose_name_plural = "Piezas de desarme"
        indexes = [
            Index(fields=["empresa", "vehiculo"]),
            Index(fields=["empresa", "codigo"]),
            Index(fields=["empresa", "estado_pieza"]),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.codigo}) x{self.cantidad} — {self.vehiculo}"


class PiezaDesarmeName(models.Model):
    LANGUAGE_CHOICES = [
        ("es", "Español"),
        ("en", "English"),
        ("pt", "Português"),
    ]

    pieza_desarme = models.ForeignKey(
        PiezaDesarme,
        on_delete=models.CASCADE,
        related_name="names",
    )
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    label = models.CharField(max_length=255, help_text="Nombre canónico en este idioma")
    aliases = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de sinónimos/slang para búsqueda (ej. ['engine', 'motor'])",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Nombre principal para este idioma (un solo True por pieza+language)",
    )

    class Meta:
        verbose_name = "Nombre de pieza desarme"
        verbose_name_plural = "Nombres de piezas desarme"
        constraints = [
            models.UniqueConstraint(
                fields=("pieza_desarme", "language", "is_default"),
                name="uq_pieza_desarme_name_pieza_lang_default",
            ),
        ]

    def __str__(self):
        return f"{self.pieza_desarme_id} [{self.language}] {self.label}"


# Tipos de evento para historial de precios (v4)
TIPO_EVENTO_VALORIZACION = "VALORIZACION"
TIPO_EVENTO_VENTA = "VENTA"
TIPO_EVENTO_AJUSTE = "AJUSTE"
TIPO_EVENTO_HISTORICO_CHOICES = [
    (TIPO_EVENTO_VALORIZACION, "Valorización"),
    (TIPO_EVENTO_VENTA, "Venta"),
    (TIPO_EVENTO_AJUSTE, "Ajuste"),
]


class PrecioHistoricoPieza(models.Model):
    """
    Historial de precios para piezas de desarme (v4).
    Permite trazabilidad y alimentar sugerencias de valorización.
    """

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="precios_historicos_pieza",
    )
    pieza_desarme = models.ForeignKey(
        PiezaDesarme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historial_precios",
    )
    vehiculo = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.CASCADE,
        related_name="precios_historicos_pieza",
        help_text="Vehículo de origen (contexto del precio).",
    )
    codigo = models.CharField(max_length=100, db_index=True)
    nombre = models.CharField(max_length=255)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=150, blank=True)
    anio = models.PositiveIntegerField(null=True, blank=True)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    tipo_evento = models.CharField(
        max_length=20,
        choices=TIPO_EVENTO_HISTORICO_CHOICES,
        db_index=True,
    )
    origen_precio = models.CharField(
        max_length=20,
        choices=ORIGEN_PRECIO_CHOICES,
        null=True,
        blank=True,
        db_index=True,
    )
    fecha = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name = "Precio histórico pieza"
        verbose_name_plural = "Precios históricos pieza"
        ordering = ["-fecha"]
        indexes = [
            Index(fields=["empresa", "fecha"]),
            Index(fields=["empresa", "tipo_evento"]),
            Index(fields=["pieza_desarme", "fecha"]),
        ]

    def __str__(self):
        return f"{self.codigo} {self.precio} ({self.tipo_evento}) @ {self.fecha}"
