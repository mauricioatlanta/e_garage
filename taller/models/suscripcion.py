from datetime import timedelta
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

try:
    from taller.models.empresa import Empresa
except Exception:
    Empresa = None

TIPOS_SUSCRIPCION = [
    ("trial", "Prueba Gratuita (30 días)"),
    ("individual_mensual", "Individual Mensual (1 Usuario)"),
    ("individual_anual", "Individual Anual (1 Usuario)"),
    ("equipo_mensual", "Equipo Mensual (2 a 5 Usuarios)"),
    ("equipo_anual", "Equipo Anual (2 a 5 Usuarios)"),
    ("empresa_mensual", "Corporativo Mensual (6 a 10 Usuarios)"),
    ("empresa_anual", "Corporativo Anual (6 a 10 Usuarios)"),
]

PLANES_PRECIOS_FLOW = {
    "individual_mensual": 20000,
    "individual_anual": 200000,
    "equipo_mensual": 35000,
    "equipo_anual": 350000,
    "empresa_mensual": 50000,
    "empresa_anual": 500000,
}

class Suscripcion(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="suscripcion")
    tipo = models.CharField(max_length=30, choices=TIPOS_SUSCRIPCION, default="trial")
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    activa = models.BooleanField(default=False)
    flow_order_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    flow_token = models.CharField(max_length=255, null=True, blank=True)

    def activar(self):
        if self.tipo == "trial":
            try:
                team_member = None
                if hasattr(self.user, "team_memberships"):
                    team_member = self.user.team_memberships.filter(is_active=True).first()

                if team_member and getattr(team_member, "empresa", None):
                    empresa = team_member.empresa
                    if Empresa is not None and hasattr(empresa, "ha_usado_prueba"):
                        empresa.ha_usado_prueba = True
                        empresa.save(update_fields=["ha_usado_prueba"])
            except Exception as e:
                print(f"Advertencia: no se pudo actualizar ha_usado_prueba: {e}")

        self.fecha_inicio = timezone.now().date()
        
        if self.tipo == "trial":
            self.fecha_fin = self.fecha_inicio + timedelta(days=30)
        elif "mensual" in self.tipo:
            self.fecha_fin = self.fecha_inicio + timedelta(days=30)
        elif "anual" in self.tipo:
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

    def limite_usuarios(self):
        if "individual" in self.tipo:
            return 1
        elif "equipo" in self.tipo:
            return 5
        elif "empresa" in self.tipo:
            return 10
        return 1

    def __str__(self):
        return f"{self.user.username} - {self.tipo.title()}"
