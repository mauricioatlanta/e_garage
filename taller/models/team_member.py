"""
Modelo para miembros del equipo (Team Members)

Permite vincular múltiples usuarios a una empresa con roles específicos.
El Owner es el usuario principal (relación OneToOne con Empresa).
Los miembros del equipo son usuarios adicionales vinculados a través de este modelo.
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .empresa import Empresa


class TeamMember(models.Model):
    """
    Modelo intermedio para vincular usuarios al equipo de una empresa.

    Características:
    - Relación Many-to-Many entre User y Empresa
    - Roles específicos por empresa
    - Soft delete (is_active)
    - Auditoría (fecha_creacion, fecha_actualizacion)
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="team_memberships", verbose_name="Usuario"
    )

    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, related_name="team_members", verbose_name="Empresa"
    )

    # Rol en esta empresa (el User puede tener múltiples roles en diferentes empresas)
    # Nota: El rol se almacena en Group, pero este campo permite tener roles específicos por empresa
    rol = models.CharField(
        max_length=50,
        choices=[
            ("Admin",    "Administrador"),
            ("Vendedor", "Vendedor"),
        ],
        default="Vendedor",
        verbose_name="Rol en el Taller",
    )

    # Estado del miembro
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Si está desactivado, el usuario no puede acceder a esta empresa",
    )

    # Auditoría
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Creación")

    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_members_created",
        verbose_name="Creado por",
    )

    # Notas adicionales (opcional)
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas",
        help_text="Notas adicionales sobre este miembro del equipo",
    )

    class Meta:
        verbose_name = "Miembro del Equipo"
        verbose_name_plural = "Miembros del Equipo"
        db_table = "taller_team_member"

        # Evitar duplicados: un usuario no puede estar en la misma empresa dos veces
        unique_together = [["user", "empresa"]]

        # Índices para mejor rendimiento
        indexes = [
            models.Index(fields=["empresa", "is_active"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.empresa.nombre_taller} ({self.rol})"

    def save(self, *args, **kwargs):
        """Asigna el rol al grupo de Django automáticamente al crear."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new or "rol" in kwargs.get("update_fields", []):
            from django.contrib.auth.models import Group
            group, _ = Group.objects.get_or_create(name=self.rol)
            if not self.user.groups.filter(name=self.rol).exists():
                self.user.groups.add(group)

    @property
    def email(self):
        """Retorna el email del usuario"""
        return self.user.email

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return self.user.get_full_name() or self.user.username
