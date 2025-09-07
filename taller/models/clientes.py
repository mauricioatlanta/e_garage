from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .color_cliente import ColorCliente
from .region_ciudad import TallerCiudad, TallerRegion
from .ubicacion import Ciudad as CiudadUSA
from .ubicacion import Estado as EstadoUSA


class AuditModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_%(class)s",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_%(class)s",
    )

    class Meta:
        abstract = True


from django.db.models import Index, Q, UniqueConstraint

from core.models import TenantManager, TenantScoped


class Cliente(AuditModelMixin, TenantScoped):
    # empresa viene de TenantScoped (nullable en migración inicial)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True, db_index=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    # Campos para Chile
    region = models.ForeignKey(TallerRegion, models.DO_NOTHING, blank=True, null=True)
    ciudad = models.ForeignKey(TallerCiudad, models.DO_NOTHING, blank=True, null=True)

    # Campos para USA
    estado_usa = models.ForeignKey(
        EstadoUSA,
        models.DO_NOTHING,
        blank=True,
        null=True,
        help_text="Estado para clientes de USA",
    )
    ciudad_usa = models.ForeignKey(
        CiudadUSA,
        models.DO_NOTHING,
        blank=True,
        null=True,
        help_text="Ciudad para clientes de USA",
    )
    zipcode = models.CharField(
        max_length=10, blank=True, null=True, help_text="Código postal para USA"
    )

    email = models.EmailField(blank=True, null=True, db_index=True)
    tax_id = models.CharField(
        max_length=32, blank=True, null=True, db_index=True, help_text="RUT/SSN/EIN"
    )

    # Campo para identificación por color
    color = models.ForeignKey(
        ColorCliente,
        models.SET_NULL,
        blank=True,
        null=True,
        help_text="Color para identificar al cliente/subscriptor",
    )

    objects = TenantManager()

    class Meta(TenantScoped.Meta):
        db_table = "taller_cliente"
        managed = True
        indexes = [
            Index(fields=["empresa", "apellido", "nombre"]),
            Index(fields=["empresa", "email"]),
            Index(fields=["empresa", "tax_id"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "email"],
                condition=Q(email__isnull=False) & ~Q(email=""),
                name="uq_cliente_empresa_email_present",
            ),
            UniqueConstraint(
                fields=["empresa", "tax_id"],
                condition=Q(tax_id__isnull=False) & ~Q(tax_id=""),
                name="uq_cliente_empresa_taxid_present",
            ),
        ]

    def __str__(self):
        nombre = self.nombre or ""
        apellido = self.apellido or ""
        texto = (nombre + " " + apellido).strip()
        if texto:
            return texto
        if self.email:
            return f"{self.email}"
        if self.telefono:
            return f"Cliente {self.telefono}"
        return f"Cliente #{self.pk}"

    def get_absolute_url(self):
        # Devuelve la URL con el prefijo de país correcto
        if hasattr(self, "empresa") and self.empresa and hasattr(self.empresa, "pais"):
            pais = self.empresa.pais.lower()
            return f"/{pais}/dashboard/suscriptor/{self.pk}/"
        return f"/dashboard/suscriptor/{self.pk}/"

    def get_colores_disponibles(self):
        """Obtiene los colores disponibles según el país de la empresa"""
        if hasattr(self, "empresa") and self.empresa and hasattr(self.empresa, "pais"):
            return ColorCliente.get_colores_para_pais(self.empresa.pais)
        return ColorCliente.get_colores_para_pais("CL")  # Default Chile

    def get_color_display(self):
        """Retorna el color del cliente con su código hexadecimal"""
        if self.color:
            return {
                "nombre": self.color.nombre,
                "codigo": self.color.codigo_color,
                "css_class": self.color.get_css_class(),
                "style": self.color.get_style_attribute(),
            }
        return None
