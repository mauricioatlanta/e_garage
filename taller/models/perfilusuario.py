from django.db import models
from django.contrib.auth.models import User
from taller.models.empresa import Empresa

ROLES = [
    ('admin', 'Administrador'),
    ('vendedor', 'Vendedor'),
    ('mecanico', 'Mecánico'),
]

class PerfilUsuario(models.Model):
    """
    MODELO DESHABILITADO - Restricción de un solo usuario por empresa
    Este modelo se mantiene solo para compatibilidad con migraciones existentes.
    No debe ser usado para crear múltiples usuarios por empresa.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES, default='vendedor')

    def save(self, *args, **kwargs):
        """
        Bloquear la creación de nuevos perfiles usuario
        Solo permitir al usuario principal de la empresa
        """
        if not self.pk:  # Si es un nuevo registro
            # Verificar si el usuario ya tiene una empresa asignada
            if Empresa.objects.filter(user=self.user).exists():
                raise ValueError("❌ Esta cuenta ya tiene un usuario asignado. No es posible registrar otro usuario para esta suscripción.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.empresa.nombre_taller} ({self.rol})"

    @property
    def es_superadmin(self):
        return self.user.is_superuser or self.user.is_staff

    class Meta:
        verbose_name = "Perfil de Usuario (DESHABILITADO)"
        verbose_name_plural = "Perfiles de Usuario (DESHABILITADOS)"
