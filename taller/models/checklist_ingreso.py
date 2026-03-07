"""
Checklist de recepción (evidencia) asociado a un Documento en el flujo de ingreso.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class ChecklistIngreso(models.Model):
    """
    OneToOne con Documento: nivel combustible, luces, objetos de valor,
    daños (JSON con marcas en esquema 2D), fotos 4 ángulos.
    """

    documento = models.OneToOneField(
        "taller.Documento",
        on_delete=models.CASCADE,
        related_name="checklist_ingreso",
    )
    nivel_combustible = models.PositiveIntegerField(
        default=0,
        help_text=_("0 a 100"),
    )
    luces_funcionan = models.BooleanField(default=True)
    objetos_valor = models.TextField(blank=True)
    danos = models.JSONField(
        default=dict,
        blank=True,
        help_text=_(
            'Ej: {"marks": [{"zone":"front_left","type":"rayon","note":"...","severity":1}]}'
        ),
    )
    fotos_4_angulos = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Lista de rutas/urls de fotos"),
    )
    foto_frontal = models.ImageField(
        upload_to="ingresos/auto/%Y/%m/",
        blank=True,
        null=True,
    )
    foto_trasera = models.ImageField(
        upload_to="ingresos/auto/%Y/%m/",
        blank=True,
        null=True,
    )
    foto_lateral_1 = models.ImageField(
        upload_to="ingresos/auto/%Y/%m/",
        blank=True,
        null=True,
    )
    foto_lateral_2 = models.ImageField(
        upload_to="ingresos/auto/%Y/%m/",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Checklist ingreso")
        verbose_name_plural = _("Checklists ingreso")

    def __str__(self):
        return f"Checklist doc #{self.documento_id}"

    def clean(self):
        super().clean()
        if self.documento_id and hasattr(self.documento, "empresa_id"):
            # La validación de mismo empresa se hace a nivel vista (documento.empresa == request.user.empresa)
            pass
