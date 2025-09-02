from django.db import models
from decimal import Decimal

class ConfiguracionEmpresa(models.Model):
    empresa = models.OneToOneField("taller.Empresa", on_delete=models.CASCADE, related_name="config")
    nombre_publico = models.CharField(max_length=200, blank=True)
    tagline = models.CharField(max_length=200, blank=True, verbose_name="Eslogan", help_text="Texto corto que aparece bajo el nombre")
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)
    iva_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19'))
    moneda = models.CharField(max_length=10, default="CLP")  # o "USD" según país
    tecnico_por_defecto = models.ForeignKey(
        "taller.Tecnico", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="tecnico_por_defecto_de"
    )
    dividir_por_tecnico_por_defecto = models.BooleanField(default=False)
    
    # Campos adicionales para configuración
    aplicar_iva_por_defecto = models.BooleanField(default=True)
    brand_color = models.CharField(max_length=20, blank=True, default='')
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Configuración de {self.empresa}" if getattr(self, 'empresa', None) else "Configuración sin empresa"
    
    class Meta:
        verbose_name = "Configuración de Empresa"
        verbose_name_plural = "Configuraciones de Empresas"
