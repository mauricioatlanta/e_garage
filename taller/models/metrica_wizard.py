from django.db import models
from .empresa import Empresa


class MetricaWizard(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, related_name='metricas_wizard')
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    ano = models.IntegerField(null=True, blank=True)
    cilindrada = models.CharField(max_length=50, blank=True, null=True)
    encontrado = models.BooleanField(default=False)
    codigo_catalitico = models.CharField(max_length=100, null=True, blank=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    fecha_consulta = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'taller_metricawizard'
        verbose_name = 'Métrica Wizard'
        verbose_name_plural = 'Métricas Wizard'
        ordering = ['-fecha_consulta']

    def __str__(self):
        estado = "ENCONTRADO" if self.encontrado else "FALLIDA"
        return f"[{estado}] {self.marca} {self.modelo} ({self.ano}) - {self.fecha_consulta.strftime('%d/%m/%Y %H:%M')}"
