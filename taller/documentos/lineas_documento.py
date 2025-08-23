from django.db import models
from django.db.models import Index, CheckConstraint, Q
from decimal import Decimal
from core.models import TenantScoped
from taller.models.documento import Documento

class LineaDocumento(TenantScoped):
    class ItemType(models.TextChoices):
        PART = "PART", "Repuesto"
        SERV = "SERV", "Servicio"

    documento   = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name="lineas", db_index=True)
    item_type   = models.CharField(max_length=4, choices=ItemType.choices, db_index=True)
    descripcion = models.CharField(max_length=255)
    qty         = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    unit_price  = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    subtotal    = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        indexes = [
            Index(fields=["empresa", "item_type"]),
            Index(fields=["empresa", "documento"]),
        ]
        constraints = [
            CheckConstraint(check=Q(qty__gt=0), name="ck_linea_qty_pos"),
            CheckConstraint(check=Q(unit_price__gte=0), name="ck_linea_price_nonneg"),
        ]

    def clean(self):
        if self.documento and self.documento.estado != "DRAFT":
            from django.core.exceptions import ValidationError
            raise ValidationError("No puedes modificar líneas de un documento emitido/anulado.")

    def save(self, *args, **kwargs):
        # Guard-rail: empresa igual a documento
        if self.documento_id and self.empresa_id != self.documento.empresa_id:
            self.empresa_id = self.documento.empresa_id
        # Subtotal exacto
        self.subtotal = (self.qty or Decimal('0.00')) * (self.unit_price or Decimal('0.00'))
        super().save(*args, **kwargs)
