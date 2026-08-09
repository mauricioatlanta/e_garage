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


ROL_SUGERENCIAS = [
    "Técnico",
    "Vendedor",
    "Técnico/Vendedor",
    "Mecánico General",
    "Especialista Eléctrico",
    "Diagnóstico y Escáner",
    "Técnico Diagnóstico",
]


class Tecnico(models.Model):
    """Personal operativo del taller — quién ejecuta el trabajo, sin necesidad de login."""

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
    direccion = models.TextField(blank=True, null=True, help_text="Dirección del técnico")

    rol = models.CharField(
        max_length=100,
        default="Técnico",
        help_text="Especialidad o función del técnico (texto libre).",
    )

    activo = models.BooleanField(default=True, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    objects = TecnicoManager()

    def __str__(self):
        estado = "✅" if self.activo else "❌"
        rol_display = f" ({self.rol})" if self.rol else ""
        return f"{estado} {self.nombre}{rol_display}"

    def clean(self):
        super().clean()
        if self.empresa_id is None:
            from django.core.exceptions import ValidationError
            raise ValidationError("Todo Técnico debe pertenecer a una empresa.")

    def es_vendedor(self):
        return "vendedor" in (self.rol or "").lower()

    def es_tecnico(self):
        rol = (self.rol or "").lower()
        return "técnico" in rol or "tecnico" in rol or "mecánico" in rol or "mecanico" in rol

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
