"""
Modelo CatalogoRepuestoEmpresa: configuración por empresa sobre el catálogo
operativo global de repuestos de desarme (ver taller/desarme/catalogo_operativo.py).
Permite a cada subscriptor decidir qué tipos de repuesto incluir en el kiosko
y a qué precio de referencia, editable en cualquier momento.
"""

from django.db import models

from core.models import TenantScoped


class CatalogoRepuestoEmpresa(TenantScoped):
    nombre = models.CharField(max_length=160, default='', blank=True, help_text='Nombre comercial del repuesto')
    categoria = models.CharField(max_length=50, default='MOTOR', help_text='Categoría: MOTOR, CARROCERIA, INTERIOR, etc.')
    visual_slot = models.CharField(max_length=80, null=True, blank=True, db_index=True, help_text='Slot anatómico en el visor 3D')
    orden = models.PositiveSmallIntegerField(default=100)

    codigo = models.CharField(max_length=20)
    incluido = models.BooleanField(default=True)
    precio_predeterminado = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    class Meta(TenantScoped.Meta):
        verbose_name = "Catálogo de repuesto por empresa"
        verbose_name_plural = "Catálogos de repuesto por empresa"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="unique_catalogo_repuesto_por_empresa",
            )
        ]

    def __str__(self):
        estado = "incluido" if self.incluido else "excluido"
        return f"{self.codigo} — {estado} (empresa {self.empresa_id})"
