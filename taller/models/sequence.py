from django.db import models, transaction
from taller.models.empresa import Empresa

class DocumentSequence(models.Model):
    """Modelo para manejar secuencias de documentos por empresa y tipo"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=3)  # 'OT','FAC','PRES'
    current = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('empresa', 'tipo')
        verbose_name = "Secuencia de Documento"
        verbose_name_plural = "Secuencias de Documentos"

    @classmethod
    def next(cls, empresa, tipo):
        """Obtiene el siguiente número de secuencia de forma segura para concurrencia"""
        with transaction.atomic():
            obj, _ = cls.objects.select_for_update().get_or_create(
                empresa=empresa, 
                tipo=tipo
            )
            obj.current += 1
            obj.save(update_fields=['current'])
            return obj.current

    def __str__(self):
        return f"{self.empresa.nombre} - {self.tipo}: {self.current}"
