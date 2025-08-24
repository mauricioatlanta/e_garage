
from django.db import models
from django.contrib.auth.models import User
from .region_ciudad import TallerRegion, TallerCiudad
from .ubicacion import Estado as EstadoUSA, Ciudad as CiudadUSA
from django.utils import timezone



class AuditModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_%(class)s"
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="updated_%(class)s"
    )

    class Meta:
        abstract = True



from core.models import TenantScoped, TenantManager
from django.db.models import Q, UniqueConstraint, Index

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
    estado_usa = models.ForeignKey(EstadoUSA, models.DO_NOTHING, blank=True, null=True, help_text="Estado para clientes de USA")
    ciudad_usa = models.ForeignKey(CiudadUSA, models.DO_NOTHING, blank=True, null=True, help_text="Ciudad para clientes de USA")
    zipcode = models.CharField(max_length=10, blank=True, null=True, help_text="Código postal para USA")
    
    email = models.EmailField(blank=True, null=True, db_index=True)
    tax_id = models.CharField(max_length=32, blank=True, null=True, db_index=True, help_text="RUT/SSN/EIN")

    objects = TenantManager()

    class Meta(TenantScoped.Meta):
        db_table = 'taller_cliente'
        managed = True
        indexes = [
            Index(fields=['empresa', 'apellido', 'nombre']),
            Index(fields=['empresa', 'email']),
            Index(fields=['empresa', 'tax_id']),
        ]
        constraints = [
            UniqueConstraint(
                fields=['empresa','email'],
                condition=Q(email__isnull=False) & ~Q(email=''),
                name='uq_cliente_empresa_email_present'
            ),
            UniqueConstraint(
                fields=['empresa','tax_id'],
                condition=Q(tax_id__isnull=False) & ~Q(tax_id=''),
                name='uq_cliente_empresa_taxid_present'
            ),
        ]

    def __str__(self):
        nombre = self.nombre or ''
        apellido = self.apellido or ''
        texto = (nombre + ' ' + apellido).strip()
        if texto:
            return texto
        if self.email:
            return f"{self.email}"
        if self.telefono:
            return f"Cliente {self.telefono}"
        return f"Cliente #{self.pk}"
    def get_absolute_url(self):
        # Devuelve la URL con el prefijo de país correcto
        if hasattr(self, 'empresa') and self.empresa and hasattr(self.empresa, 'pais'):
            pais = self.empresa.pais.lower()
            return f"/{pais}/dashboard/suscriptor/{self.pk}/"
        return f"/dashboard/suscriptor/{self.pk}/"
