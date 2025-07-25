from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime

class MarcaVehiculo(models.Model):
    """Marcas de vehículos disponibles en el mercado estadounidense"""
    nombre = models.CharField(_('Nombre'), max_length=100, unique=True)
    nombre_en = models.CharField(_('Nombre en Inglés'), max_length=100, blank=True)
    pais_origen = models.CharField(_('País de Origen'), max_length=50, default='USA')
    activa = models.BooleanField(_('Activa'), default=True)
    anio_inicio = models.PositiveIntegerField(
        _('Año Inicio'), 
        default=1980,
        validators=[MinValueValidator(1900), MaxValueValidator(datetime.now().year)]
    )
    anio_fin = models.PositiveIntegerField(
        _('Año Fin'), 
        null=True, 
        blank=True,
        validators=[MinValueValidator(1900), MaxValueValidator(datetime.now().year + 5)]
    )
    
    class Meta:
        verbose_name = _('Marca de Vehículo')
        verbose_name_plural = _('Marcas de Vehículos')
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    @property
    def nombre_localizado(self):
        """Devuelve el nombre en el idioma correspondiente"""
        from django.utils import translation
        if translation.get_language() == 'en' and self.nombre_en:
            return self.nombre_en
        return self.nombre

class ModeloVehiculo(models.Model):
    """Modelos específicos de cada marca"""
    marca = models.ForeignKey(MarcaVehiculo, on_delete=models.CASCADE, related_name='modelos')
    nombre = models.CharField(_('Nombre'), max_length=100)
    nombre_en = models.CharField(_('Nombre en Inglés'), max_length=100, blank=True)
    anio_inicio = models.PositiveIntegerField(
        _('Año Inicio'), 
        validators=[MinValueValidator(1980), MaxValueValidator(datetime.now().year)]
    )
    anio_fin = models.PositiveIntegerField(
        _('Año Fin'), 
        null=True, 
        blank=True,
        validators=[MinValueValidator(1980), MaxValueValidator(datetime.now().year + 5)]
    )
    tipo_vehiculo = models.CharField(
        _('Tipo de Vehículo'),
        max_length=50,
        choices=[
            ('sedan', _('Sedan')),
            ('suv', _('SUV')),
            ('truck', _('Pickup/Truck')),
            ('coupe', _('Coupe')),
            ('hatchback', _('Hatchback')),
            ('wagon', _('Station Wagon')),
            ('convertible', _('Convertible')),
            ('van', _('Van/Minivan')),
            ('motorcycle', _('Motorcycle')),
        ],
        default='sedan'
    )
    activo = models.BooleanField(_('Activo'), default=True)
    
    class Meta:
        verbose_name = _('Modelo de Vehículo')
        verbose_name_plural = _('Modelos de Vehículos')
        ordering = ['marca__nombre', 'nombre']
        unique_together = ['marca', 'nombre']
    
    def __str__(self):
        return f"{self.marca.nombre} {self.nombre}"
    
    @property
    def nombre_localizado(self):
        """Devuelve el nombre en el idioma correspondiente"""
        from django.utils import translation
        if translation.get_language() == 'en' and self.nombre_en:
            return self.nombre_en
        return self.nombre
    
    @property
    def rango_anos(self):
        """Devuelve el rango de años disponible"""
        fin = self.anio_fin or datetime.now().year
        return f"{self.anio_inicio}-{fin}"
    
    def get_anos_disponibles(self):
        """Lista de años disponibles para este modelo"""
        fin = self.anio_fin or datetime.now().year
        return list(range(self.anio_inicio, fin + 1))
