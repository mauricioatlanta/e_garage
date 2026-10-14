from django.db import models

class PartApplication(models.Model):
    """
    Modelo canónico que define a qué vehículos, años y motorizaciones 
    aplica una pieza o código OEM específico.
    """
    codigo_pieza = models.CharField(max_length=100, db_index=True)
    oem_normalizado = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    # Especificación del vehículo compatible
    marca = models.CharField(max_length=50, db_index=True)
    modelo = models.CharField(max_length=100, db_index=True)
    anio_desde = models.PositiveIntegerField(null=True, blank=True)
    anio_hasta = models.PositiveIntegerField(null=True, blank=True)
    
    # Restricciones técnicas opcionales
    motor = models.CharField(max_length=100, blank=True, null=True)
    transmision = models.CharField(max_length=50, blank=True, null=True)
    carroceria = models.CharField(max_length=50, blank=True, null=True)
    
    # Metadatos de confianza y origen
    fuente = models.CharField(max_length=50, default="manual")
    nivel_confianza = models.PositiveSmallIntegerField(default=5)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Aplicación de Pieza (Interchange)"
        verbose_name_plural = "Aplicaciones de Piezas"
        indexes = [
            models.Index(fields=['marca', 'modelo', 'anio_desde', 'anio_hasta']),
        ]

    def __str__(self):
        anos = f"({self.anio_desde}-{self.anio_hasta})" if self.anio_desde else ""
        return f"{self.codigo_pieza} -> {self.marca} {self.modelo} {anos}"
