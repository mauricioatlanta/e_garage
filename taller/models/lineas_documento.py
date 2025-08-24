#!/usr/bin/env python
"""
Modelos de líneas de documento con validaciones de consistencia robustas
"""
from django.db import models
from django.core.exceptions import ValidationError
from taller.models.documento import Documento
from taller.servicios.models import Servicio

class ValidacionConsistencia:
    """Clase helper para validaciones de consistencia cross-country"""
    
    @staticmethod
    def assert_same_country(a, b, mensaje="Objetos pertenecen a países diferentes"):
        """Validar que dos objetos tengan el mismo country"""
        country_a = getattr(a, 'country', getattr(getattr(a, 'empresa', None), 'pais', None))
        country_b = getattr(b, 'country', getattr(getattr(b, 'empresa', None), 'pais', None))
        
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
        'taller.Documento',
        on_delete=models.CASCADE,
        related_name='lineas_servicio'
    )
    servicio = models.ForeignKey(
        Servicio, 
        on_delete=models.PROTECT,
        help_text="Servicio interno del taller"
    )
    nombre = models.CharField(max_length=255, help_text="Nombre del servicio")
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    from decimal import Decimal
    descuento = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('0.00'),
        help_text="Descuento en porcentaje"
    )
    observaciones = models.TextField(blank=True, null=True)
    
    def clean(self):
        """Validaciones de consistencia para LineaServicio"""
        # Validar country consistency
        if self.documento and self.servicio:
            ValidacionConsistencia.assert_same_country(
                self.documento, self.servicio,
                "Servicio de otro país no puede usarse en este documento"
            )
        
        # Validar que sea servicio interno
        if self.servicio:
            # Temporalmente desactivado hasta agregar campo tipo
            # ValidacionConsistencia.assert_correct_tipo(
            #     self.servicio, 'interno',
            #     "Esta línea requiere un servicio de tipo 'interno' (del taller)"
            # )
            pass
    
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
        verbose_name = "Línea de Servicio"
        verbose_name_plural = "Líneas de Servicios"
        indexes = [
            models.Index(fields=['documento', 'servicio']),
        ]
    
    def __str__(self):
        return f"{self.nombre} (x{self.cantidad})"


class LineaOtroServicio(models.Model):
    """Línea de servicio externo subcontratado"""
    documento = models.ForeignKey(
        'taller.Documento',
        on_delete=models.CASCADE,
        related_name='lineas_otro_servicio'
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
        Servicio, 
        on_delete=models.PROTECT,
        null=True, blank=True,
        help_text="Servicio legacy (para compatibilidad)"
    )
    nombre = models.CharField(max_length=255, help_text="Nombre del servicio externo")
    empresa_externa = models.CharField(
        max_length=255, 
        help_text="Empresa que realiza el servicio"
    )
    cantidad = models.PositiveIntegerField(default=1)
    costo_interno = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Costo pagado a la empresa externa"
    )
    precio_cliente = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Precio cobrado al cliente"
    )
    observaciones = models.TextField(blank=True, null=True)
    
    def clean(self):
        """Validaciones de consistencia para LineaOtroServicio"""
        # Validar que al menos un servicio esté configurado o campos manuales
        if not self.servicio and not self.nombre:
            raise ValidationError("Debe especificar un servicio o un nombre de servicio")
        
        # Validar country consistency si hay servicio legacy
        if self.documento and self.servicio:
            ValidacionConsistencia.assert_same_country(
                self.documento, self.servicio,
                "Otro servicio de otro país no puede usarse en este documento"
            )
        
        # Validar precios lógicos
        if self.costo_interno and self.precio_cliente:
            if self.precio_cliente < self.costo_interno:
                raise ValidationError(
                    "El precio al cliente no puede ser menor al costo interno"
                )
    
    def save(self, *args, **kwargs):
        """Llamar validaciones antes de guardar"""
        self.full_clean()
        return super().save(*args, **kwargs)
    
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
            models.Index(fields=['documento', 'servicio']),
            models.Index(fields=['empresa_externa']),
        ]
    
    def __str__(self):
        return f"{self.nombre} - {self.empresa_externa} (x{self.cantidad})"


class LineaRepuesto(models.Model):
    """Línea de repuesto con validaciones de país"""
    documento = models.ForeignKey(
        'taller.Documento',
        on_delete=models.CASCADE,
        related_name='lineas_repuesto'
    )
    repuesto = models.ForeignKey(
        'taller.Repuesto', 
        on_delete=models.PROTECT,
        null=True, blank=True,
        help_text="Repuesto del catálogo"
    )
    codigo = models.CharField(max_length=100, help_text="Código del repuesto")
    nombre = models.CharField(max_length=255, help_text="Nombre del repuesto")
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    from decimal import Decimal
    descuento = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('0.00'),
        help_text="Descuento en porcentaje"
    )
    observaciones = models.TextField(blank=True, null=True)
    
    def clean(self):
        """Validaciones de consistencia para LineaRepuesto"""
        # Solo validar country si el repuesto tiene field country
        if self.documento and self.repuesto and hasattr(self.repuesto, 'country'):
            ValidacionConsistencia.assert_same_country(
                self.documento, self.repuesto,
                "Repuesto de otro país no puede usarse en este documento"
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
            models.Index(fields=['documento', 'repuesto']),
            models.Index(fields=['codigo']),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo}) x{self.cantidad}"
