from django.db import models
from django.utils import timezone

class TrialRegistro(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    codigo = models.CharField(max_length=32, unique=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    fecha_activacion = models.DateTimeField(null=True, blank=True)
    prueba_activa = models.BooleanField(default=False)
    prueba_expirada = models.BooleanField(default=False)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    def dias_restantes(self):
        if not self.fecha_activacion:
            return 30
        delta = timezone.now() - self.fecha_activacion
        return max(0, 30 - delta.days)

    def expirar_si_corresponde(self):
        if self.prueba_activa and self.fecha_activacion:
            if (timezone.now() - self.fecha_activacion).days >= 30:
                self.prueba_activa = False
                self.prueba_expirada = True
                self.save()

    def __str__(self):
        return f"{self.email} ({'Activa' if self.prueba_activa else 'Inactiva'})"
