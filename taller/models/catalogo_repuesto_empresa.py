"""
Modelo CatalogoRepuestoEmpresa: configuración por empresa sobre el catálogo
operativo global de repuestos de desarme (ver taller/desarme/catalogo_operativo.py).
Permite a cada subscriptor decidir qué tipos de repuesto incluir en el kiosko
y a qué precio de referencia, editable en cualquier momento.
"""

from django.db import models

from core.models import TenantScoped


class CatalogoRepuestoEmpresa(TenantScoped):
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
