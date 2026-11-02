from decimal import Decimal

from django.db import models


class ConfiguracionComisionEmpresa(models.Model):
    """
    Configuración de participación en kiosko y modo de comisiones por empresa.
    OneToOne con Empresa — creada por el admin de eGarage, no por el subscriptor.
    """

    MODO_COMISION_CHOICES = [
        ("NINGUNA", "Sin comisión"),
        ("POR_VENDEDOR", "Por vendedor (% uniforme por vendedor)"),
        ("POR_CATEGORIA", "Por categoría (% según categoría de repuesto)"),
    ]

    empresa = models.OneToOneField(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="configuracion_comision",
    )
    kiosko_autorizado = models.BooleanField(
        default=False,
        help_text="Activa/desactiva la participación de esta empresa en el kiosko. Solo lo cambia el admin de eGarage.",
    )
    modo_comision = models.CharField(
        max_length=20,
        choices=MODO_COMISION_CHOICES,
        default="NINGUNA",
        help_text="Modo de cálculo de comisiones para ventas internas. Independiente del kiosko.",
    )

    class Meta:
        verbose_name = "Configuración de comisión"
        verbose_name_plural = "Configuraciones de comisión"

    def __str__(self):
        estado = "✓ kiosko" if self.kiosko_autorizado else "✗ kiosko"
        return f"{self.empresa.nombre_taller} — {estado} / comisión: {self.get_modo_comision_display()}"


class VendedorComision(models.Model):
    """
    Porcentaje de comisión asignado a un vendedor (TeamMember) de la empresa.

    El historial NO se borra: cuando cambia el %, se cierra el registro anterior
    (vigente_hasta) y se crea uno nuevo. El % activo es el que tiene vigente_hasta=None.

    Al registrar una venta, el % se congela en la línea del documento (snapshot),
    nunca se recalcula consultando esta tabla después.
    """

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="comisiones_vendedor",
    )
    vendedor = models.ForeignKey(
        "taller.TeamMember",
        on_delete=models.CASCADE,
        related_name="comisiones",
    )
    categoria = models.CharField(
        max_length=100,
        blank=True,
        help_text="Categoría de repuesto a la que aplica (modo POR_CATEGORIA). Vacío = aplica a todas.",
    )
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje de comisión. Ej: 5.00 = 5%",
    )
    vigente_desde = models.DateField(auto_now_add=True)
    vigente_hasta = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de cierre de esta regla. Null = vigente actualmente.",
    )

    class Meta:
        verbose_name = "Comisión de vendedor"
        verbose_name_plural = "Comisiones de vendedores"
        indexes = [
            models.Index(fields=["empresa", "vendedor", "vigente_hasta"]),
        ]

    def __str__(self):
        estado = "vigente" if self.vigente_hasta is None else f"cerrada {self.vigente_hasta}"
        cat = f" [{self.categoria}]" if self.categoria else ""
        return f"{self.vendedor} — {self.porcentaje}%{cat} ({estado})"
