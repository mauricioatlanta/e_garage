from django.core.management.base import BaseCommand

from taller.models.comprobante_pago import ComprobantePago
from taller.models.pago import PagoPendiente
from taller.services.suscripcion_transaccion_service import (
    sync_from_comprobante_pago,
    sync_from_pago_pendiente,
)


class Command(BaseCommand):
    help = "Backfill de la tabla unificada SuscripcionTransaccion desde modelos legacy."

    def handle(self, *args, **options):
        pagos = 0
        comprobantes = 0

        for pago in PagoPendiente.objects.select_related("empresa", "verificado_por"):
            sync_from_pago_pendiente(pago)
            pagos += 1

        for comprobante in ComprobantePago.objects.select_related("empresa"):
            sync_from_comprobante_pago(comprobante)
            comprobantes += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill completado: {pagos} PagoPendiente y {comprobantes} ComprobantePago sincronizados."
            )
        )

