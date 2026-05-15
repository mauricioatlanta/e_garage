from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# Intentamos importar Empresa para marcar 'ha_usado_prueba' al activar trial
try:
    from taller.models.empresa import Empresa
except Exception:
    Empresa = None

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
        # Marcar que la empresa vinculada (si existe) ya usó la prueba
        if self.tipo == "trial":
            try:
                # Buscar un TeamMember activo que vincule al usuario con una Empresa
                team_member = None
                if hasattr(self.user, "team_memberships"):
                    team_member = self.user.team_memberships.filter(is_active=True).first()

                # Si existe team_member y empresa, marcar el flag en Empresa
                if team_member and getattr(team_member, "empresa", None):
                    empresa = team_member.empresa
                    if Empresa is not None and hasattr(empresa, "ha_usado_prueba"):
                        empresa.ha_usado_prueba = True
                        empresa.save(update_fields=["ha_usado_prueba"])
            except Exception as e:
                # No impedir la activación por errores en la lógica de empresa
                print(f"Advertencia: no se pudo actualizar ha_usado_prueba: {e}")

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
