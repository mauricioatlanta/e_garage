
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

TIPOS_SUSCRIPCION = [
    ("trial", "Prueba gratuita"),
    ("mensual", "Mensual"),
    ("semestral", "Semestral"),
    ("anual", "Anual"),
]

class Suscripcion(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="suscripcion")
    tipo = models.CharField(max_length=20, choices=TIPOS_SUSCRIPCION, default="trial")
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    activa = models.BooleanField(default=False)

    def activar(self):
        self.fecha_inicio = timezone.now().date()
        if self.tipo == "trial":
            self.fecha_fin = self.fecha_inicio + timedelta(days=30)
        elif self.tipo == "mensual":
            self.fecha_fin = self.fecha_inicio + timedelta(days=30)
        elif self.tipo == "semestral":
            self.fecha_fin = self.fecha_inicio + timedelta(days=180)
        elif self.tipo == "anual":
            self.fecha_fin = self.fecha_inicio + timedelta(days=365)
        self.activa = True
        self.save()

    def esta_vencida(self):
        return self.fecha_fin and timezone.now().date() > self.fecha_fin

    def por_vencer(self):
        if not self.fecha_fin:
            return False
        dias = (self.fecha_fin - timezone.now().date()).days
        return 0 < dias <= 5

    def es_prueba(self):
        return self.tipo == "trial"

    def __str__(self):
        return f"{self.user.username} - {self.tipo.title()}"
