from django.db import models
from decimal import Decimal

class ConfiguracionEmpresa(models.Model):
    empresa = models.OneToOneField("taller.Empresa", on_delete=models.CASCADE, related_name="config")
    nombre_publico = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)
    iva_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19'))
    moneda = models.CharField(max_length=10, default="CLP")  # o "USD" según país
    tecnico_por_defecto = models.ForeignKey(
        "taller.Tecnico", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="tecnico_por_defecto_de"
    )
    dividir_por_tecnico_por_defecto = models.BooleanField(default=False)

    def __str__(self):
        return f"Configuración de {self.empresa}" if getattr(self, 'empresa', None) else "Configuración sin empresa"
