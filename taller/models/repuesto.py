from decimal import Decimal
import re

from django.db import models
from django.db.models import Index, Q, UniqueConstraint

from core.models import TenantScoped


class RepuestoQuerySet(models.QuerySet):
    def buscar_medida_neumatico(self, medida: str):
        match = re.search(
            r"(?P<ancho>\d{3})\s*/\s*(?P<perfil>\d{2})\s*r?\s*(?P<aro>\d{2})",
            medida or "",
            re.I,
        )
        if not match:
            return self.none()
        return self.filter(
            ancho=int(match.group("ancho")),
            perfil=int(match.group("perfil")),
            aro=int(match.group("aro")),
        )

    def buscar_mostrador(self, termino: str):
        q = (termino or "").strip()
        if not q:
            return self.none()

        medida_qs = self.buscar_medida_neumatico(q)
        texto_qs = self.filter(
            Q(part_number__icontains=q)
            | Q(codigo_oem__icontains=q)
            | Q(codigos_equivalentes__icontains=q)
            | Q(nombre__icontains=q)
            | Q(proveedor__icontains=q)
            | Q(marca_neumatico__icontains=q)
            | Q(modelo_neumatico__icontains=q)
        )
        return (texto_qs | medida_qs).distinct()


class CategoriaRepuesto(TenantScoped):
    nombre = models.CharField(max_length=120, db_index=True)

    class Meta(TenantScoped.Meta):
        verbose_name = "Categoría de Repuesto"
        verbose_name_plural = "Categorías de Repuesto"
        indexes = [
            Index(fields=["empresa", "nombre"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "nombre"],
                condition=Q(nombre__isnull=False) & ~Q(nombre=""),
                name="uq_categoria_repuesto_empresa_nombre_present",
            ),
        ]

    def __str__(self):
        return self.nombre or f"Categoría #{self.pk}"


class Repuesto(TenantScoped):
    objects = RepuestoQuerySet.as_manager()

    part_number = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    codigo_oem = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    codigos_equivalentes = models.TextField(
        blank=True,
        default="",
        help_text="Códigos alternativos separados por coma, espacio o salto de línea.",
    )
    nombre = models.CharField(max_length=160, db_index=True)
    categoria = models.ForeignKey(
        CategoriaRepuesto,
        on_delete=models.PROTECT,
        db_index=True,
        null=True,
        blank=True,
    )
    precio_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Precio al que compraste el repuesto",
    )
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Precio al que vendes el repuesto",
    )
    cantidad_stock = models.PositiveIntegerField(
        default=0, help_text="Cantidad disponible en stock"
    )
    stock_minimo = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Stock minimo recomendado para reabastecimiento",
    )
    proveedor = models.CharField(
        max_length=200, null=True, blank=True, help_text="Donde compraste el repuesto"
    )
    ubicacion = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        help_text="Ubicación física en bodega, estante o casillero.",
    )
    ancho = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    perfil = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    aro = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    indice_carga = models.CharField(max_length=10, blank=True, default="")
    codigo_velocidad = models.CharField(max_length=5, blank=True, default="")
    condicion = models.CharField(
        max_length=10,
        choices=[("nuevo", "Nuevo"), ("usado", "Usado")],
        default="nuevo",
        db_index=True,
    )
    profundidad_mm = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )
    marca_neumatico = models.CharField(max_length=80, blank=True, default="")
    modelo_neumatico = models.CharField(max_length=120, blank=True, default="")

    class Meta(TenantScoped.Meta):
        indexes = [
            Index(fields=["empresa", "part_number"]),
            Index(fields=["empresa", "codigo_oem"]),
            Index(fields=["empresa", "nombre"]),
            Index(fields=["empresa", "categoria"]),
            Index(fields=["empresa", "ancho", "perfil", "aro"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "part_number"],
                condition=Q(part_number__isnull=False) & ~Q(part_number=""),
                name="uq_repuesto_empresa_partnumber_present",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.part_number})"

    @property
    def medida_completa(self):
        if self.ancho and self.perfil and self.aro:
            return f"{self.ancho}/{self.perfil}R{self.aro}"
        return ""
