#!/usr/bin/env python
"""
Modelos de líneas de documento con validaciones de consistencia robustas
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

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
    vendedor = models.ForeignKey(
        "taller.TeamMember",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lineas_servicio_comision",
        help_text="Vendedor que generó esta línea (para comisión)",
    )
    porcentaje_comision = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="% de comisión congelado al momento de la venta. No se recalcula.",
    )

    def clean(self):
        """Validaciones de consistencia para LineaServicio"""
        doc_empresa_id = getattr(getattr(self, "documento", None), "empresa_id", None)
        # Validar country consistency
        if hasattr(self, "documento") and self.documento and self.servicio:
            ValidacionConsistencia.assert_same_country(
                self.documento,
                self.servicio,
                "Servicio de otro país no puede usarse en este documento",
            )

        if (
            doc_empresa_id
            and self.servicio
            and getattr(self.servicio, "empresa_id", None) != doc_empresa_id
        ):
            raise ValidationError(
                "El servicio legacy debe pertenecer a la misma empresa del documento."
            )

        if self.service and doc_empresa_id:
            service_empresa_id = getattr(self.service, "empresa_id", None)
            if service_empresa_id is not None and service_empresa_id != doc_empresa_id:
                raise ValidationError(
                    "El servicio del catalogo debe ser de la misma empresa del documento o global."
                )

        if self.tecnico_responsable and doc_empresa_id:
            if getattr(self.tecnico_responsable, "empresa_id", None) != doc_empresa_id:
                raise ValidationError(
                    "El tecnico responsable de la linea debe pertenecer a la empresa del documento."
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
        """Calcular subtotal con descuento"""
        subtotal_bruto = self.cantidad * self.precio_unitario
        descuento_valor = subtotal_bruto * (self.descuento / 100)
        return subtotal_bruto - descuento_valor

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
        """Validaciones de consistencia para LineaOtroServicio."""
        doc_empresa_id = getattr(getattr(self, "documento", None), "empresa_id", None)

        if not self.servicio and not self.nombre:
            raise ValidationError("Debe especificar un servicio o un nombre de servicio")

        if hasattr(self, "documento") and self.documento and self.servicio:
            ValidacionConsistencia.assert_same_country(
                self.documento,
                self.servicio,
                "Otro servicio de otro pais no puede usarse en este documento",
            )
            if doc_empresa_id and getattr(self.servicio, "empresa_id", None) != doc_empresa_id:
                raise ValidationError(
                    "El servicio legacy debe pertenecer a la misma empresa del documento."
                )

        if self.tecnico_responsable and doc_empresa_id:
            if getattr(self.tecnico_responsable, "empresa_id", None) != doc_empresa_id:
                raise ValidationError(
                    "El tecnico responsable de la linea debe pertenecer a la empresa del documento."
                )

        if self.costo_interno and self.precio_cliente:
            if self.precio_cliente < self.costo_interno:
                raise ValidationError("El precio al cliente no puede ser menor al costo interno")

    def _unused_cross_class_clean(self):
        """Helper legacy sin uso."""
        doc_empresa_id = getattr(getattr(self, "documento", None), "empresa_id", None)

        if self.tecnico_responsable and doc_empresa_id:
            if getattr(self.tecnico_responsable, "empresa_id", None) != doc_empresa_id:
                raise ValidationError(
                    "El tecnico responsable de la linea debe pertenecer a la empresa del documento."
                )

        self.clean_legacy()

    def _unused_cross_class_clean_legacy(self):
        """Helper legacy sin uso."""
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
        """Calcular subtotal (precio_cliente * cantidad)"""
        return self.precio_cliente * self.cantidad

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


# Origen del repuesto en la línea (para inventario y rentabilidad)
ORIGEN_EXTERNO = "EXTERNO"
ORIGEN_STOCK_BODEGA = "STOCK_BODEGA"
ORIGEN_DESARME = "DESARME"
ORIGEN_REPUESTO_CHOICES = [
    (ORIGEN_EXTERNO, "Externo"),
    (ORIGEN_STOCK_BODEGA, "Stock bodega"),
    (ORIGEN_DESARME, "Desarme"),
]


class LineaRepuesto(models.Model):
    """Línea de repuesto con validaciones de país y origen (bodega/desarme/externo)."""

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

    part = models.ForeignKey(
        "taller.Part",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lineas",
        help_text="Repuesto del catálogo con I18N (usar en lugar de 'repuesto')",
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
    vendedor = models.ForeignKey(
        "taller.TeamMember",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lineas_repuesto_comision",
        help_text="Vendedor que generó esta línea (para comisión)",
    )
    porcentaje_comision = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="% de comisión congelado al momento de la venta. No se recalcula.",
    )

    origen_repuesto = models.CharField(
        max_length=20,
        choices=ORIGEN_REPUESTO_CHOICES,
        default=ORIGEN_STOCK_BODEGA,
        db_index=True,
    )
    pieza_desarme = models.ForeignKey(
        "taller.PiezaDesarme",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="lineas_repuesto",
    )
    costo_linea = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Costo para rentabilidad (EXTERNO: costo compra; DESARME: puede venir de PiezaDesarme).",
    )

    def clean(self):
        """Validaciones de consistencia para LineaRepuesto."""
        doc_empresa_id = getattr(getattr(self, "documento", None), "empresa_id", None)

        if self.tecnico_responsable and doc_empresa_id:
            if getattr(self.tecnico_responsable, "empresa_id", None) != doc_empresa_id:
                raise ValidationError(
                    "El tecnico responsable de la linea debe pertenecer a la empresa del documento."
                )

        self.clean_legacy()

    def clean_legacy(self):
        """Validaciones de consistencia para LineaRepuesto"""
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
        if self.origen_repuesto == ORIGEN_DESARME:
            if not self.pieza_desarme_id:
                raise ValidationError(
                    {"pieza_desarme": "Origen Desarme requiere seleccionar una pieza de desarme."}
                )
            if (
                hasattr(self, "documento")
                and self.documento_id
                and self.pieza_desarme.empresa_id != self.documento.empresa_id
            ):
                raise ValidationError(
                    "La pieza de desarme debe pertenecer a la misma empresa del documento."
                )
            if not getattr(self.pieza_desarme, "activo", True):
                raise ValidationError("La pieza de desarme no está disponible (inactiva).")
            if self.pieza_desarme.cantidad < self.cantidad:
                raise ValidationError(
                    f"Stock insuficiente en pieza de desarme. Disponible: {self.pieza_desarme.cantidad}"
                )
        elif self.origen_repuesto == ORIGEN_STOCK_BODEGA:
            if not (self.repuesto_id or self.part_id):
                raise ValidationError("Origen Stock bodega requiere repuesto o part.")
            if hasattr(self, "documento") and self.documento_id:
                doc_empresa_id = getattr(self.documento, "empresa_id", None)
                if doc_empresa_id is not None:
                    if (
                        self.repuesto_id
                        and getattr(self.repuesto, "empresa_id", None) != doc_empresa_id
                    ):
                        raise ValidationError(
                            "El repuesto debe pertenecer a la misma empresa del documento."
                        )
                    if (
                        self.part_id
                        and getattr(self.part, "empresa_id", None) is not None
                        and self.part.empresa_id != doc_empresa_id
                    ):
                        raise ValidationError(
                            "El part del catálogo debe ser de la misma empresa del documento o catálogo global."
                        )

    def save(self, *args, **kwargs):
        """Llamar validaciones antes de guardar"""
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def subtotal(self):
        """Calcular subtotal con descuento"""
        subtotal_bruto = self.cantidad * self.precio_unitario
        descuento_valor = subtotal_bruto * (self.descuento / 100)
        return subtotal_bruto - descuento_valor

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
