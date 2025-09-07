from decimal import Decimal

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .lineas_documento import LineaDocumento
from .models import Documento


@receiver([post_save, post_delete], sender=LineaDocumento)
def recalc_on_line_change(sender, instance, **kwargs):
    doc_id = instance.documento_id
    if not doc_id:
        return
    with transaction.atomic():
        doc = Documento.objects.select_for_update().get(pk=doc_id)
        if doc.estado != "DRAFT":
            return
        net_parts = sum(l.subtotal for l in doc.lineas.filter(item_type="PART"))
        net_serv = sum(l.subtotal for l in doc.lineas.filter(item_type="SERV"))
        doc.neto_repuestos = net_parts
        doc.neto_servicios = net_serv
        rate = (doc.tax_rate_applied or Decimal("0.00")) / Decimal("100")
        base = net_parts  # CL por defecto; en US ajustarás con TaxRule en Fase 3
        doc.tax_amount = (base * rate).quantize(Decimal("0.01"))
        doc.total = (
            doc.neto_repuestos + doc.neto_servicios - doc.descuento + doc.tax_amount
        ).quantize(Decimal("0.01"))
        doc.save(
            update_fields=["neto_repuestos", "neto_servicios", "tax_amount", "total"]
        )
