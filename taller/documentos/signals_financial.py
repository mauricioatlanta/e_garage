from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_DESARME
from taller.services.snapshot_queue import SnapshotQueue


@receiver(post_save, sender=LineaRepuesto)
def _dispatch_financial_event_for_linea_repuesto(sender, instance, created, **kwargs):
    if instance.origen_repuesto != ORIGEN_DESARME:
        return

    if instance.documento and instance.documento.estado == "EMITIDO":
        SnapshotQueue.enqueue_for_document(instance.documento)


@receiver(post_delete, sender=LineaRepuesto)
def _dispatch_remove_financial_event_for_linea_repuesto(sender, instance, **kwargs):
    if instance.origen_repuesto != ORIGEN_DESARME:
        return

    if instance.documento and instance.documento.estado == "EMITIDO":
        SnapshotQueue.enqueue_for_document(instance.documento)


@receiver(post_save, sender=Documento)
def _dispatch_financial_snapshot_for_documento(sender, instance, created, **kwargs):
    if instance.estado != "EMITIDO":
        return

    SnapshotQueue.enqueue_for_document(instance)
