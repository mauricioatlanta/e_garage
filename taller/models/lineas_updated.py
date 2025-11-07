# -*- coding: utf-8 -*-
from decimal import Decimal
from django.db import models
from .utils_monedas import money_quantize

class LineaRepuesto(models.Model):
    documento = models.ForeignKey('taller.Documento', on_delete=models.CASCADE, related_name='lineas_repuesto')
    nombre = models.CharField(max_length=255)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        pais = getattr(getattr(self.documento, 'empresa', None), 'pais', 'CL')
        bruto = (self.cantidad or 0) * (self.precio_unitario or 0)
        neto = Decimal(bruto) - Decimal(self.descuento or 0)
        self.subtotal = money_quantize(neto if neto > 0 else Decimal("0"), pais)
        super().save(*args, **kwargs)

class LineaServicio(models.Model):
    documento = models.ForeignKey('taller.Documento', on_delete=models.CASCADE, related_name='lineas_servicio')
    nombre = models.CharField(max_length=255)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        pais = getattr(getattr(self.documento, 'empresa', None), 'pais', 'CL')
        bruto = (self.cantidad or 0) * (self.precio_unitario or 0)
        neto = Decimal(bruto) - Decimal(self.descuento or 0)
        self.subtotal = money_quantize(neto if neto > 0 else Decimal("0"), pais)
        super().save(*args, **kwargs)

class LineaOtroServicio(models.Model):
    documento = models.ForeignKey('taller.Documento', on_delete=models.CASCADE, related_name='lineas_otro_servicio')
    nombre = models.CharField(max_length=255)
    empresa_externa = models.CharField(max_length=255, blank=True, null=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    costo_interno = models.DecimalField(max_digits=12, decimal_places=2, default=0)   # costo a ti
    precio_cliente = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # cobrado al cliente
    ganancia = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)  # para totales (usamos precio_cliente)

    def save(self, *args, **kwargs):
        pais = getattr(getattr(self.documento, 'empresa', None), 'pais', 'CL')
        # Para totales: usamos precio cliente * cantidad
        bruto_cliente = (self.cantidad or 0) * (self.precio_cliente or 0)
        self.subtotal = money_quantize(Decimal(bruto_cliente), pais)
        # Ganancia visible en reportes
        bruto_costo = (self.cantidad or 0) * (self.costo_interno or 0)
        self.ganancia = money_quantize(Decimal(bruto_cliente) - Decimal(bruto_costo), pais)
        super().save(*args, **kwargs)
