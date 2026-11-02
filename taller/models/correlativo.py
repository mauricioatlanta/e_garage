# Correlativo por empresa y tipo (Recibo / Invoice) para numeración PRO multi-país.

from django.db import models


class CorrelativoDocumento(models.Model):
    """Correlativo independiente por empresa y tipo (recibo | invoice)."""

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="correlativos_documento",
    )
    tipo = models.CharField(max_length=20, db_index=True)  # "recibo" | "invoice"
    ultimo_numero = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "taller"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "tipo"],
                name="taller_correlativodoc_empresa_tipo_uniq",
            ),
        ]
        verbose_name = "Correlativo de documento"
        verbose_name_plural = "Correlativos de documentos"

    def __str__(self):
        return f"{self.empresa} - {self.tipo} -> {self.ultimo_numero}"
