from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

class Estado(models.Model):
    """Modelo para estados de EE.UU."""
    nombre = models.CharField(_('Nombre'), max_length=100)
    codigo = models.CharField(_('Código'), max_length=2, unique=True)  # GA, FL, NY, etc.
    sales_tax = models.DecimalField(_('Sales Tax (%)'), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    timezone = models.CharField(_('Zona Horaria'), max_length=50, default='America/New_York')
    
    class Meta:
        verbose_name = _('Estado')
        verbose_name_plural = _('Estados')
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

class Ciudad(models.Model):
    """Modelo para ciudades principales de EE.UU."""
    nombre = models.CharField(_('Nombre'), max_length=100)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, related_name='ciudades')
    poblacion = models.IntegerField(_('Población'), null=True, blank=True)
    es_capital = models.BooleanField(_('Es Capital'), default=False)
    latitud = models.DecimalField(_('Latitud'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(_('Longitud'), max_digits=9, decimal_places=6, null=True, blank=True)
    # Sales tax local adicional (se suma al del estado)
    sales_tax_local = models.DecimalField(_('Sales Tax Local (%)'), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        verbose_name = _('Ciudad')
        verbose_name_plural = _('Ciudades')
        ordering = ['estado__nombre', 'nombre']
        unique_together = ['nombre', 'estado']
        db_table = 'taller_ciudad_usa'  # Evitar conflicto con TallerCiudad existente
    
    def __str__(self):
        return f"{self.nombre}, {self.estado.codigo}"

    @property
    def nombre_completo(self):
        return f"{self.nombre}, {self.estado.nombre}"
    
    @property
    def sales_tax_total(self):
        """Sales tax total (estado + local)"""
        return self.estado.sales_tax + self.sales_tax_local
