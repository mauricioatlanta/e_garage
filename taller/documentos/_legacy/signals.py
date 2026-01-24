"""
Signals para recálculo automático de totales de documentos
Versión mejorada: performance, precisión, concurrencia
"""

from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from taller.models.documento import Documento
from taller.models.lineas_documento import (
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
)

# Nota: Este signal usa LineaDocumento (legacy) que puede no estar en uso
# Si el sistema usa LineaRepuesto/LineaServicio/LineaOtroServicio, 
# este signal debería adaptarse o desactivarse
try:
    from .lineas_documento import LineaDocumento
except ImportError:
    # Si LineaDocumento no existe o no se usa, desactivar signal
    LineaDocumento = None

# Constantes para evitar "magic strings"
ITEM_PART = "PART"
ITEM_SERV = "SERV"
ESTADO_DRAFT = "DRAFT"  # o Documento.Estados.DRAFT si existe


def _q2(x: Decimal) -> Decimal:
    """Redondeo consistente a 2 decimales con ROUND_HALF_UP"""
    if x is None:
        x = Decimal("0.00")
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Signal solo se activa si LineaDocumento existe y se usa
# Nota: Si el sistema usa LineaRepuesto/LineaServicio/LineaOtroServicio,
# este signal debería adaptarse o desactivarse completamente
if LineaDocumento is not None:
    @receiver(
        [post_save, post_delete],
        sender=LineaDocumento,
        dispatch_uid="doc_recalc_on_line_change_v2",
    )
    def recalc_on_line_change(sender, instance, raw=False, using=None, **kwargs):
        """
        Recalcula totales del documento cuando cambian las líneas.

        Mejoras implementadas:
        - Evita loops durante loaddata/migraciones (raw=True)
        - Performance: ORM Sum + Coalesce (1 query por tipo)
        - Precisión: Decimal con redondeo consistente
        - Concurrencia: select_for_update() con only()
        - Constantes: sin magic strings
        """
        # Evitar ejecuciones durante loaddata/migraciones
        if raw:
            return

        doc_id = getattr(instance, "documento_id", None)
        if not doc_id:
            return

        # Asegura consistencia si se guardan varias líneas en paralelo
        with transaction.atomic():
            # Lock sobre el documento; evita carreras entre pestañas/hilos
            doc = (
                Documento.objects.select_for_update()
                .only("id", "estado", "descuento", "tax_rate_applied")
                .get(pk=doc_id)
            )

            # Solo recalcular en borradores
            if doc.estado != ESTADO_DRAFT:
                return

            # Agrega en DB (más rápido y sin traer todas las líneas a memoria)
            # Nota: si lineas tiene related_name "lineas", esto funciona.
            agg = doc.lineas.values("item_type").annotate(
                neto=Coalesce(Sum("subtotal"), Decimal("0.00"))
            )
            net_parts = Decimal("0.00")
            net_serv = Decimal("0.00")
            for row in agg:
                if row["item_type"] == ITEM_PART:
                    net_parts = Decimal(row["neto"])
                elif row["item_type"] == ITEM_SERV:
                    net_serv = Decimal(row["neto"])

            # Normaliza campos potencialmente nulos
            descuento = Decimal(doc.descuento or Decimal("0.00"))
            rate_pct = Decimal(doc.tax_rate_applied or Decimal("0.00"))

            # CL por defecto: impuesto solo sobre repuestos (si en US cambia, ajusta fuente/base)
            rate = (rate_pct / Decimal("100")).quantize(
                Decimal("0.0001")
            )  # precisión extra antes de q2
            tax_amount = _q2(net_parts * rate)

            # Total = repuestos + servicios - descuento + impuesto
            neto_repuestos = _q2(net_parts)  # alias por claridad
            neto_servicios = _q2(net_serv)
            total = _q2(neto_repuestos + neto_servicios - descuento + tax_amount)

            # Guarda sólo los campos recalculados
            doc.neto_repuestos = neto_repuestos
            doc.neto_servicios = neto_servicios
            doc.tax_amount = tax_amount
            doc.total = total
            doc.save(update_fields=["neto_repuestos", "neto_servicios", "tax_amount", "total"])
