#!/usr/bin/env python
"""
Modelos de líneas de documento con validaciones de consistencia robustas
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, Value
from django.db.models.functions import Coalesce

from .utils_monedas import money_quantize


class ValidacionConsistencia:
    """Clase helper para validaciones de consistencia cross-country"""

    @staticmethod
    def assert_same_country(a, b, mensaje="Objetos pertenecen a países diferentes"):
        """Validar que dos objetos tengan el mismo country"""
        country_a = getattr(a, "country", getattr(getattr(a, "empresa", None), "pais", None))
        country_b = getattr(b, "country", getattr(getattr(b, "empresa", None), "pais", None))

        if country_a != country_b:
            raise ValidationError(f"{mensaje} ({country_a} != {country_b})")

    @staticmethod
    def assert_correct_tipo(servicio, tipo_esperado, mensaje="Tipo de servicio incorrecto"):
        """Validar que un servicio tenga el tipo correcto"""
        if servicio.tipo != tipo_esperado:
            raise ValidationError(f"{mensaje}. Esperado: {tipo_esperado}, Actual: {servicio.tipo}")


class LineaServicio(models.Model):
    """Línea de servicio interno del taller"""

    documento = models.ForeignKey(
        "taller.Documento", on_delete=models.CASCADE, related_name="lineas_servicio"
    )
    servicio = models.ForeignKey(
        "taller.Servicio",  # ✅ String reference (legacy, app taller.servicios)
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="[LEGACY] Servicio interno del taller (modelo antiguo)",
    )

    # === NUEVO: FK opcional a catálogo con I18N ===
    service = models.ForeignKey(
        "taller.Service",  # ✅ String reference (actualmente en taller, mover a servicios en Release 2.0)
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lineas",
        help_text="Servicio del catálogo con I18N (usar en lugar de 'servicio')",
    )

    nombre = models.CharField(
        max_length=255, help_text="Nombre del servicio (congelado al emitir documento)"
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    from decimal import Decimal

    descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Descuento en porcentaje",
    )
    observaciones = models.TextField(blank=True, null=True)
    tecnico_responsable = models.ForeignKey(
        "taller.Tecnico",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lineas_servicio",
        help_text="Técnico responsable de esta línea (si no se especifica, hereda del documento)",
    )

    def clean(self):
        """Validaciones de consistencia para LineaServicio"""
        # Validar country consistency
        if hasattr(self, "documento") and self.documento and self.servicio:
            ValidacionConsistencia.assert_same_country(
                self.documento,
                self.servicio,
                "Servicio de otro país no puede usarse en este documento",
            )

        # Validar que sea servicio interno
        if hasattr(self, "servicio") and self.servicio:
            # Temporalmente desactivado hasta agregar campo tipo
            # ValidacionConsistencia.assert_correct_tipo(
            #     self.servicio, 'interno',
            #     "Esta línea requiere un servicio de tipo 'interno' (del taller)"
            # )
            pass

    def save(self, *args, **kwargs):
        """Calcular subtotal (solo lectura) y llamar validaciones antes de guardar"""
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def subtotal(self):
        """Subtotal para templates/PDF: cantidad * precio_unitario con descuento %."""
        subtotal_bruto = (self.cantidad or 0) * (self.precio_unitario or 0)
        descuento_valor = subtotal_bruto * ((self.descuento or 0) / 100)
        return subtotal_bruto - descuento_valor

    @classmethod
    def subtotal_expr(cls):
        """Expresión DB para aggregate/annotate (Sum). Descuento en porcentaje."""
        return ExpressionWrapper(
            F("cantidad") * F("precio_unitario") * (1 - Coalesce(F("descuento"), Value(0)) / 100),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

    class Meta:
        verbose_name = "Línea de Servicio"
        verbose_name_plural = "Líneas de Servicios"
        indexes = [
            models.Index(fields=["documento", "servicio"]),
            models.Index(fields=["tecnico_responsable"]),
            # Los KPIs usarán documento__tecnico_responsable con Coalesce
            # Los índices en Documento ya optimizan las consultas por fecha_emision
        ]

    def __str__(self):
        return f"{self.nombre} (x{self.cantidad})"


class LineaOtroServicio(models.Model):
    """Línea de servicio externo subcontratado"""

    documento = models.ForeignKey(
        "taller.Documento",
        on_delete=models.CASCADE,
        related_name="lineas_otro_servicio",
    )
    # Referencia al servicio externo
    # servicio_externo = models.ForeignKey(
    #     'taller.ServicioExterno',
    #     on_delete=models.PROTECT,
    #     null=True, blank=True,
    #     help_text="Servicio externo configurado"
    # )
    # Campos manuales (legacy support)
    servicio = models.ForeignKey(
        "taller.Servicio",  # ✅ String reference (legacy, en taller.servicios)
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Servicio legacy (para compatibilidad)",
    )
    nombre = models.CharField(max_length=255, help_text="Nombre del servicio externo")
    empresa_externa = models.CharField(max_length=255, help_text="Empresa que realiza el servicio")
    cantidad = models.PositiveIntegerField(default=1)
    costo_interno = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Costo pagado a la empresa externa"
    )
    precio_cliente = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Precio cobrado al cliente"
    )
    observaciones = models.TextField(blank=True, null=True)
    tecnico_responsable = models.ForeignKey(
        "taller.Tecnico",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lineas_otro_servicio",
        help_text="Técnico responsable de esta línea (si no se especifica, hereda del documento)",
    )

    def clean(self):
        """Validaciones de consistencia para LineaOtroServicio"""
        # Validar que al menos un servicio esté configurado o campos manuales
        if not self.servicio and not self.nombre:
            raise ValidationError("Debe especificar un servicio o un nombre de servicio")

        # Validar country consistency si hay servicio legacy
        if hasattr(self, "documento") and self.documento and self.servicio:
            ValidacionConsistencia.assert_same_country(
                self.documento,
                self.servicio,
                "Otro servicio de otro país no puede usarse en este documento",
            )

        # Validar precios lógicos
        if self.costo_interno and self.precio_cliente:
            if self.precio_cliente < self.costo_interno:
                raise ValidationError("El precio al cliente no puede ser menor al costo interno")

    def save(self, *args, **kwargs):
        """Llamar validaciones antes de guardar"""
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def subtotal(self):
        """Subtotal para templates/PDF: precio_cliente * cantidad."""
        return (self.precio_cliente or 0) * (self.cantidad or 0)

    @classmethod
    def subtotal_expr(cls):
        """Expresión DB para aggregate/annotate (Sum)."""
        return ExpressionWrapper(
            F("cantidad") * Coalesce(F("precio_cliente"), Value(0)),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

    @property
    def ganancia(self):
        """Calcular ganancia por línea"""
        return (self.precio_cliente - self.costo_interno) * self.cantidad

    @property
    def margen_porcentaje(self):
        """Calcular margen en porcentaje"""
        if self.precio_cliente > 0:
            return ((self.precio_cliente - self.costo_interno) / self.precio_cliente) * 100
        return 0

    class Meta:
        verbose_name = "Línea de Otro Servicio"
        verbose_name_plural = "Líneas de Otros Servicios"
        indexes = [
            models.Index(fields=["documento", "servicio"]),
            models.Index(fields=["empresa_externa"]),
            models.Index(fields=["tecnico_responsable"]),
            # Los KPIs usarán documento__tecnico_responsable con Coalesce
            # Los índices en Documento ya optimizan las consultas por fecha_emision
        ]

    def __str__(self):
        return f"{self.nombre} - {self.empresa_externa} (x{self.cantidad})"


class LineaRepuesto(models.Model):
    """Línea de repuesto con validaciones de país y source_type (customer/stock/sourced)"""

    SOURCE_TYPE_CHOICES = [
        ("CUSTOMER_SUPPLIED", "Customer supplied"),
        ("IN_STOCK", "In stock"),
        ("SOURCED", "Sourced"),
    ]

    documento = models.ForeignKey(
        "taller.Documento", on_delete=models.CASCADE, related_name="lineas_repuesto"
    )
    repuesto = models.ForeignKey(
        "taller.Repuesto",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="[LEGACY] Repuesto del catálogo antiguo",
    )

    # === NUEVO: FK opcional a catálogo con I18N ===
    part = models.ForeignKey(
        "taller.Part",  # ✅ String reference (actualmente en taller, mover a repuestos en Release 2.0)
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lineas",
        help_text="Repuesto del catálogo con I18N (usar en lugar de 'repuesto')",
    )

    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE_CHOICES,
        default="IN_STOCK",
        db_index=True,
        help_text="Origen del repuesto: cliente lo trae, en stock, o conseguido afuera",
    )
    customer_part_description = models.CharField(
        max_length=255, blank=True, null=True, help_text="Descripción si lo trae el cliente"
    )
    customer_part_notes = models.TextField(
        blank=True, null=True, help_text="Notas sobre pieza traída por cliente"
    )

    codigo = models.CharField(max_length=100, help_text="Código del repuesto")
    nombre = models.CharField(
        max_length=255, help_text="Nombre del repuesto (congelado al emitir documento)"
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    from decimal import Decimal

    descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Descuento en porcentaje",
    )
    observaciones = models.TextField(blank=True, null=True)
    tecnico_responsable = models.ForeignKey(
        "taller.Tecnico",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lineas_repuesto",
        help_text="Técnico responsable de esta línea (si no se especifica, hereda del documento)",
    )

    def clean(self):
        """Validaciones de consistencia para LineaRepuesto"""
        # Regla de oro: customer supplied → precio 0, descuento 0
        if getattr(self, "source_type", "IN_STOCK") == "CUSTOMER_SUPPLIED":
            self.precio_unitario = Decimal("0.00")
            self.descuento = Decimal("0.00")

        # Solo validar country si el documento existe y el repuesto tiene field country
        if (
            hasattr(self, "documento")
            and self.documento
            and self.repuesto
            and hasattr(self.repuesto, "country")
        ):
            ValidacionConsistencia.assert_same_country(
                self.documento,
                self.repuesto,
                "Repuesto de otro país no puede usarse en este documento",
            )

    def save(self, *args, **kwargs):
        """Llamar validaciones antes de guardar. Forzar precio 0 si customer supplied."""
        if getattr(self, "source_type", "IN_STOCK") == "CUSTOMER_SUPPLIED":
            self.precio_unitario = Decimal("0.00")
            self.descuento = Decimal("0.00")
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def subtotal(self):
        """Subtotal para templates/PDF: cantidad * precio_unitario con descuento %."""
        subtotal_bruto = (self.cantidad or 0) * (self.precio_unitario or 0)
        descuento_valor = subtotal_bruto * ((self.descuento or 0) / 100)
        return subtotal_bruto - descuento_valor

    @classmethod
    def subtotal_expr(cls):
        """Expresión DB para aggregate/annotate (Sum). Descuento en porcentaje."""
        return ExpressionWrapper(
            F("cantidad") * F("precio_unitario") * (1 - Coalesce(F("descuento"), Value(0)) / 100),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

    class Meta:
        verbose_name = "Línea de Repuesto"
        verbose_name_plural = "Líneas de Repuestos"
        indexes = [
            models.Index(fields=["documento", "repuesto"]),
            models.Index(fields=["codigo"]),
            models.Index(fields=["tecnico_responsable"]),
            # Los KPIs usarán documento__tecnico_responsable con Coalesce
            # Los índices en Documento ya optimizan las consultas por fecha_emision
        ]

    def __str__(self):
        return f"{self.nombre} ({self.codigo}) x{self.cantidad}"
