from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .lineas_documento import LineaOtroServicio, LineaRepuesto, LineaServicio


def _recalc_documento(instance, raw=False):
    """Recalcula totales del documento al crear/editar/eliminar líneas. Usa recompute_totals (lógica unificada de impuestos y context)."""
    if raw:
        return  # Evitar durante loaddata/fixtures
    doc = getattr(instance, "documento", None)
    if doc and getattr(doc, "id", None):
        doc.recompute_totals(persist=True)


@receiver(post_save, sender=LineaRepuesto)
def _recalc_doc_repuesto_save(sender, instance, raw=False, **kwargs):
    _recalc_documento(instance, raw=raw)


@receiver(post_delete, sender=LineaRepuesto)
def _recalc_doc_repuesto_delete(sender, instance, **kwargs):
    _recalc_documento(instance)


@receiver(post_save, sender=LineaServicio)
def _recalc_doc_servicio_save(sender, instance, raw=False, **kwargs):
    _recalc_documento(instance, raw=raw)


@receiver(post_delete, sender=LineaServicio)
def _recalc_doc_servicio_delete(sender, instance, **kwargs):
    _recalc_documento(instance)


@receiver(post_save, sender=LineaOtroServicio)
def _recalc_doc_otro_save(sender, instance, raw=False, **kwargs):
    _recalc_documento(instance, raw=raw)


@receiver(post_delete, sender=LineaOtroServicio)
def _recalc_doc_otro_delete(sender, instance, **kwargs):
    _recalc_documento(instance)
