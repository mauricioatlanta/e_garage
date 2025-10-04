from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from taller.models.documento import Documento

def _touch_documento(doc):
    """
    Actualiza los totales de un documento cuando cambian sus líneas.
    """
    if not isinstance(doc, Documento):
        return
    doc.recompute_totals(persist=True)

@receiver(post_save, sender="taller.LineaRepuesto")
@receiver(post_delete, sender="taller.LineaRepuesto")
def _recalc_repuesto(sender, instance, **kwargs):
    """Recalcula totales cuando se crea/edita/elimina una línea de repuesto"""
    if hasattr(instance, 'documento'):
        _touch_documento(instance.documento)

@receiver(post_save, sender="taller.LineaServicio")
@receiver(post_delete, sender="taller.LineaServicio")
def _recalc_servicio(sender, instance, **kwargs):
    """Recalcula totales cuando se crea/edita/elimina una línea de servicio"""
    if hasattr(instance, 'documento'):
        _touch_documento(instance.documento)

@receiver(post_save, sender="taller.LineaOtroServicio")
@receiver(post_delete, sender="taller.LineaOtroServicio")
def _recalc_otro(sender, instance, **kwargs):
    """Recalcula totales cuando se crea/edita/elimina una línea de otro servicio"""
    if hasattr(instance, 'documento'):
        _touch_documento(instance.documento)
