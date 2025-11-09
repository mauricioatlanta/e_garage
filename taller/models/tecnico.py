# taller/models/tecnico.py
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.functions import Lower

from .empresa import Empresa

# Si ya tienes AuditMixin, úsalo:
# from taller.models.mixins import AuditMixin


class TecnicoQuerySet(models.QuerySet):
    """QuerySet personalizado para Tecnico con métodos de conveniencia"""

    def activos(self):
        """Filtrar solo técnicos activos"""
        return self.filter(activo=True)

    def de_empresa(self, empresa):
        """Filtrar por empresa"""
        return self.filter(empresa=empresa)

    def buscar_por_nombre(self, texto):
        """Búsqueda por nombre (case-insensitive)"""
        return self.filter(nombre__icontains=texto)

    def por_rol(self, rol):
        """Filtrar por rol específico"""
        return self.filter(rol=rol)


class TecnicoManager(models.Manager):
    """Manager personalizado para Tecnico"""

    def get_queryset(self):
        return TecnicoQuerySet(self.model, using=self._db)

    def activos(self):
        return self.get_queryset().activos()

    def de_empresa(self, empresa):
        return self.get_queryset().de_empresa(empresa)

    def buscar_por_nombre(self, texto):
        return self.get_queryset().buscar_por_nombre(texto)

    def por_rol(self, rol):
        return self.get_queryset().por_rol(rol)


class Tecnico(models.Model):
    """Modelo unificado de Técnico/Vendedor con validaciones multi-tenant"""

    class Rol(models.TextChoices):
        TECNICO = "TECNICO", "Técnico"
        VENDEDOR = "VENDEDOR", "Vendedor"
        MIXTO = "MIXTO", "Técnico/Vendedor"

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="tecnicos",
        null=True,  # ← mantiene compatibilidad; valida en clean() para producción
        blank=True,
    )
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Teléfono de contacto del técnico",
    )
    direccion = models.TextField(
        blank=True, null=True, help_text="Dirección del técnico"
    )

    # Unificación técnico/vendedor
    rol = models.CharField(max_length=12, choices=Rol, default=Rol.MIXTO, db_index=True)

    activo = models.BooleanField(default=True, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    objects = TecnicoManager()

    def __str__(self):
        estado = "✅" if self.activo else "❌"
        rol_display = (
            f" ({self.get_rol_display()})" if self.rol != self.Rol.MIXTO else ""
        )
        return f"{estado} {self.nombre}{rol_display}"

    def clean(self):
        """Validaciones multi-tenant robustas"""
        super().clean()
        # En producción no deberías permitir técnico sin empresa
        if self.empresa_id is None:
            # Si aún estás migrando datos, cambia a warning/log. En estable, levanta error:
            from django.core.exceptions import ValidationError

            raise ValidationError("Todo Técnico debe pertenecer a una empresa.")

    def es_vendedor(self):
        """Helper para verificar si es vendedor (incluye MIXTO)"""
        return self.rol in [self.Rol.VENDEDOR, self.Rol.MIXTO]

    def es_tecnico(self):
        """Helper para verificar si es técnico (incluye MIXTO)"""
        return self.rol in [self.Rol.TECNICO, self.Rol.MIXTO]

    class Meta:
        verbose_name = "Técnico"
        verbose_name_plural = "Técnicos"
        ordering = ["-activo", "nombre"]
        constraints = [
            # Unicidad por empresa + nombre case-insensitive
            UniqueConstraint(
                Lower("nombre"),
                "empresa",
                name="uq_tecnico_empresa_nombre_lower",
                condition=Q(nombre__isnull=False) & ~Q(nombre=""),
            ),
        ]
        indexes = [
            models.Index(fields=["empresa", "activo"]),
            models.Index(fields=["empresa", "rol"]),
            models.Index(fields=["empresa", "nombre"]),
        ]
