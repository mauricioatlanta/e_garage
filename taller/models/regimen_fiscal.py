"""
Modelo de Régimen Fiscal para eGarage
======================================

Sistema flexible de impuestos que se adapta a las reglas fiscales de cada país.
Permite configurar diferentes tipos de impuestos (IVA, ISS, Sales Tax) con
comportamientos de cálculo distintos según el país.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class RegimenFiscal(models.Model):
    """
    Configuración fiscal por país.
    
    Define el tipo de impuesto, tasa y comportamiento de cálculo
    para cada país soportado por eGarage.
    """
    
    PAISES = [
        ('CL', 'Chile'),
        ('BR', 'Brasil'),
        ('US', 'USA'),
        ('MX', 'México'),
        ('PE', 'Perú'),
        ('CO', 'Colombia'),
        ('EC', 'Ecuador'),
        ('AR', 'Argentina'),
        ('VE', 'Venezuela'),
        ('UY', 'Uruguay'),
    ]
    
    # Comportamientos de cálculo de impuesto
    CALCULO_EXCLUIDO = 'excluido'  # USA: Se suma al final
    CALCULO_INCLUIDO = 'incluido'  # Latam: Ya está incluido (desglose)
    CALCULO_NINGUNO = 'ninguno'    # Sin impuesto
    
    METODOS_CALCULO = [
        (CALCULO_EXCLUIDO, _('Excluido (se suma al final)')),
        (CALCULO_INCLUIDO, _('Incluido (desglose del precio)')),
        (CALCULO_NINGUNO, _('Sin impuesto')),
    ]
    
    pais = models.CharField(
        max_length=2,
        choices=PAISES,
        unique=True,
        db_index=True,
        help_text=_("Código ISO 3166-1 alpha-2 del país")
    )
    
    nombre_impuesto = models.CharField(
        max_length=50,
        help_text=_("Nombre del impuesto (IVA, ISS, Sales Tax, IGV, etc.)")
    )
    
    nombre_impuesto_en = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Nombre del impuesto en inglés (opcional)")
    )
    
    tasa_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
        help_text=_("Tasa de impuesto en porcentaje (ej: 19.00 para 19%)")
    )
    
    metodo_calculo = models.CharField(
        max_length=20,
        choices=METODOS_CALCULO,
        default=CALCULO_INCLUIDO,
        help_text=_("Cómo se calcula el impuesto: excluido (USA), incluido (Latam), o ninguno")
    )
    
    activo = models.BooleanField(
        default=True,
        help_text=_("Si está activo, se usará como configuración por defecto para el país")
    )
    
    descripcion = models.TextField(
        blank=True,
        help_text=_("Descripción adicional del régimen fiscal")
    )
    
    # Campos de metadatos
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Régimen Fiscal")
        verbose_name_plural = _("Régimenes Fiscales")
        ordering = ['pais']
        indexes = [
            models.Index(fields=['pais', 'activo']),
        ]
    
    def __str__(self):
        return f"{self.get_pais_display()} - {self.nombre_impuesto} ({self.tasa_porcentaje}%)"
    
    def calcular_impuesto(self, subtotal):
        """
        Calcula el impuesto según el método de cálculo del país.
        
        Args:
            subtotal: Decimal - Monto base para calcular el impuesto
        
        Returns:
            tuple: (impuesto_calculado, total_final)
            - Para excluido: (impuesto, subtotal + impuesto)
            - Para incluido: (impuesto_desglosado, subtotal)
            - Para ninguno: (0, subtotal)
        """
        if self.metodo_calculo == self.CALCULO_NINGUNO or self.tasa_porcentaje == 0:
            return Decimal("0.00"), subtotal
        
        if self.metodo_calculo == self.CALCULO_EXCLUIDO:
            # USA: Se suma al final
            # impuesto = subtotal * (tasa / 100)
            impuesto = subtotal * (self.tasa_porcentaje / Decimal("100.0"))
            total = subtotal + impuesto
            return impuesto, total
        
        elif self.metodo_calculo == self.CALCULO_INCLUIDO:
            # Latam: Ya está incluido, calcular desglose
            # Si precio_incluye_impuesto = subtotal
            # entonces precio_sin_impuesto = subtotal / (1 + tasa/100)
            # impuesto = subtotal - precio_sin_impuesto
            tasa_decimal = self.tasa_porcentaje / Decimal("100.0")
            denominador = Decimal("1.0") + tasa_decimal
            precio_sin_impuesto = subtotal / denominador
            impuesto = subtotal - precio_sin_impuesto
            return impuesto, subtotal  # El total sigue siendo el subtotal
        
        return Decimal("0.00"), subtotal
    
    @classmethod
    def get_regimen_pais(cls, pais):
        """
        Obtiene el régimen fiscal activo para un país.
        
        Args:
            pais: str - Código de país (CL, BR, US, etc.)
        
        Returns:
            RegimenFiscal o None
        """
        try:
            return cls.objects.get(pais=pais.upper(), activo=True)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_tasa_pais(cls, pais):
        """
        Obtiene la tasa de impuesto para un país.
        
        Args:
            pais: str - Código de país
        
        Returns:
            Decimal - Tasa de impuesto o 0.00
        """
        regimen = cls.get_regimen_pais(pais)
        if regimen:
            return regimen.tasa_porcentaje
        return Decimal("0.00")
    
    @classmethod
    def get_metodo_calculo_pais(cls, pais):
        """
        Obtiene el método de cálculo para un país.
        
        Args:
            pais: str - Código de país
        
        Returns:
            str - Método de cálculo (excluido, incluido, ninguno)
        """
        regimen = cls.get_regimen_pais(pais)
        if regimen:
            return regimen.metodo_calculo
        return cls.CALCULO_INCLUIDO  # Por defecto incluido (Latam)


def crear_regimenes_fiscales_default():
    """
    Función helper para crear los regímenes fiscales por defecto.
    Se puede ejecutar desde una migración o un comando de management.
    """
    regimenes = [
        {
            'pais': 'CL',
            'nombre_impuesto': 'IVA',
            'nombre_impuesto_en': 'VAT',
            'tasa_porcentaje': Decimal('19.00'),
            'metodo_calculo': RegimenFiscal.CALCULO_INCLUIDO,
            'descripcion': 'IVA chileno al 19%. Generalmente incluido en el precio.',
        },
        {
            'pais': 'BR',
            'nombre_impuesto': 'ISS',
            'nombre_impuesto_en': 'ISS',
            'tasa_porcentaje': Decimal('5.00'),  # Promedio, varía por municipio
            'metodo_calculo': RegimenFiscal.CALCULO_INCLUIDO,
            'descripcion': 'ISS (Imposto Sobre Serviços). Varía según el municipio (2-5%).',
        },
        {
            'pais': 'US',
            'nombre_impuesto': 'Sales Tax',
            'nombre_impuesto_en': 'Sales Tax',
            'tasa_porcentaje': Decimal('0.00'),  # Varía por estado, se configura manualmente
            'metodo_calculo': RegimenFiscal.CALCULO_EXCLUIDO,
            'descripcion': 'Sales Tax. Varía por estado (0-10%). Se suma al final del ticket. Muchos estados no gravan mano de obra.',
        },
        {
            'pais': 'MX',
            'nombre_impuesto': 'IVA',
            'nombre_impuesto_en': 'VAT',
            'tasa_porcentaje': Decimal('16.00'),
            'metodo_calculo': RegimenFiscal.CALCULO_INCLUIDO,
            'descripcion': 'IVA mexicano al 16%. Generalmente incluido en el precio.',
        },
        {
            'pais': 'PE',
            'nombre_impuesto': 'IGV',
            'nombre_impuesto_en': 'IGV',
            'tasa_porcentaje': Decimal('18.00'),
            'metodo_calculo': RegimenFiscal.CALCULO_INCLUIDO,
            'descripcion': 'IGV (Impuesto General a las Ventas) al 18%. Incluido en el precio.',
        },
        {
            'pais': 'CO',
            'nombre_impuesto': 'IVA',
            'nombre_impuesto_en': 'VAT',
            'tasa_porcentaje': Decimal('19.00'),
            'metodo_calculo': RegimenFiscal.CALCULO_INCLUIDO,
            'descripcion': 'IVA colombiano al 19%. Generalmente incluido en el precio.',
        },
        {
            'pais': 'EC',
            'nombre_impuesto': 'IVA',
            'nombre_impuesto_en': 'VAT',
            'tasa_porcentaje': Decimal('12.00'),
            'metodo_calculo': RegimenFiscal.CALCULO_INCLUIDO,
            'descripcion': 'IVA ecuatoriano al 12%. Incluido en el precio.',
        },
        {
            'pais': 'AR',
            'nombre_impuesto': 'IVA',
            'nombre_impuesto_en': 'VAT',
            'tasa_porcentaje': Decimal('21.00'),
            'metodo_calculo': RegimenFiscal.CALCULO_INCLUIDO,
            'descripcion': 'IVA argentino al 21%. Generalmente incluido en el precio.',
        },
        {
            'pais': 'VE',
            'nombre_impuesto': 'IVA',
            'nombre_impuesto_en': 'VAT',
            'tasa_porcentaje': Decimal('16.00'),
            'metodo_calculo': RegimenFiscal.CALCULO_INCLUIDO,
            'descripcion': 'IVA venezolano al 16%. Incluido en el precio.',
        },
        {
            'pais': 'UY',
            'nombre_impuesto': 'IVA',
            'nombre_impuesto_en': 'VAT',
            'tasa_porcentaje': Decimal('22.00'),
            'metodo_calculo': RegimenFiscal.CALCULO_INCLUIDO,
            'descripcion': 'IVA uruguayo al 22%. Incluido en el precio.',
        },
    ]
    
    creados = []
    for regimen_data in regimenes:
        regimen, created = RegimenFiscal.objects.get_or_create(
            pais=regimen_data['pais'],
            defaults=regimen_data
        )
        if created:
            creados.append(regimen)
    
    return creados




