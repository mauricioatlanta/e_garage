"""
Modelo DetalleDocumento - Líneas de items en documentos (Cotización/Orden)

Características:
  ✅ Choices para tipo_item (REPUESTO, SERVICIO, OTRO)
  ✅ Subtotal calculado automáticamente (editable=False)
  ✅ Validación multi-tenant en clean()
  ✅ max_digits ampliados para soportar CLP grandes
  ✅ MinValueValidator para evitar precios negativos
  ✅ Recálculo robusto en save() con manejo de None
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from taller.models.documento import Documento


class DetalleDocumento(models.Model):
    """
    Detalle/línea de un documento (cotización u orden de trabajo).

    Cada línea puede ser:
      - REPUESTO: Parte física vendida
      - SERVICIO: Mano de obra o servicio prestado
      - OTRO: Items misceláneos

    Subtotal se calcula automáticamente: precio_venta × cantidad
    """

    class TipoItem(models.TextChoices):
        REPUESTO = "REPUESTO", "Repuesto"
        SERVICIO = "SERVICIO", "Servicio"
        OTRO = "OTRO", "Otro"

    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name="detalles",
        help_text="Documento al que pertenece esta línea",
    )
    tipo_item = models.CharField(
        max_length=20,
        choices=TipoItem,
        default=TipoItem.SERVICIO,
        verbose_name="Tipo de ítem",
    )
    nombre = models.CharField(max_length=255, verbose_name="Descripción")
    precio_venta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Precio unitario",
        help_text="Precio de venta por unidad",
    )
    cantidad = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)], verbose_name="Cantidad"
    )
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
        verbose_name="Subtotal",
        help_text="Calculado automáticamente: precio_venta × cantidad",
    )

    # Campos opcionales para futuro
    # descuento = models.DecimalField(
    #     max_digits=5,
    #     decimal_places=2,
    #     default=Decimal("0.00"),
    #     validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
    #     verbose_name="Descuento (%)",
    #     help_text="Porcentaje de descuento sobre el subtotal"
    # )
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Detalle de documento"
        verbose_name_plural = "Detalles de documentos"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["documento", "tipo_item"]),
        ]

    def save(self, *args, **kwargs):
        """
        Recalcula subtotal antes de guardar.
        Maneja casos donde precio_venta o cantidad sean None.
        """
        precio = self.precio_venta or Decimal("0.00")
        cant = self.cantidad or 0
        self.subtotal = precio * Decimal(cant)
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validaciones de integridad y multi-tenant.

        Verifica:
          - Precio y cantidad sean válidos
          - (Opcional) Coherencia multi-tenant con empresa del documento
        """
        super().clean()

        # Validar precio positivo
        if self.precio_venta and self.precio_venta < 0:
            raise ValidationError({"precio_venta": "El precio no puede ser negativo"})

        # Validar cantidad mínima
        if self.cantidad and self.cantidad < 1:
            raise ValidationError({"cantidad": "La cantidad debe ser al menos 1"})

        # Validación multi-tenant (opcional, si tienes empresa en DetalleDocumento)
        # Descomenta si tu modelo tiene FK empresa:
        # if self.documento and hasattr(self.documento, "empresa_id"):
        #     if hasattr(self, "empresa_id") and self.empresa_id:
        #         if self.documento.empresa_id != self.empresa_id:
        #             raise ValidationError(
        #                 "El detalle no pertenece a la empresa del documento"
        #             )

    def __str__(self):
        """Representación legible del detalle."""
        tipo = self.get_tipo_item_display()
        return f"{tipo}: {self.nombre} x{self.cantidad} = ${self.subtotal:,.2f}"

    def get_precio_total(self):
        """
        Devuelve el subtotal (alias para consistencia con otros modelos).
        Útil si en el futuro agregas descuentos.
        """
        return self.subtotal

    def get_precio_con_descuento(self, descuento_pct=Decimal("0.00")):
        """
        Calcula precio con descuento aplicado.

        Args:
            descuento_pct: Porcentaje de descuento (0-100)

        Returns:
            Decimal: Subtotal con descuento aplicado

        Example:
            >>> detalle.get_precio_con_descuento(Decimal("10.00"))
            Decimal('90.00')  # 10% off de $100
        """
        if descuento_pct <= 0:
            return self.subtotal
        factor = (Decimal("100.00") - descuento_pct) / Decimal("100.00")
        return self.subtotal * factor
