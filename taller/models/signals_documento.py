# -*- coding: utf-8 -*-
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .lineas_documento import LineaRepuesto, LineaServicio, LineaOtroServicio

def _recalc_documento(instance):
    doc = getattr(instance, "documento", None)
    if doc:
        # Evita recursión infinita: recalcula totales del documento sin volver a tocar las líneas
        doc.recalcular_totales(save=True)

@receiver(post_save, sender=LineaRepuesto)
def _recalc_doc_repuesto_save(sender, instance, **kwargs):
    _recalc_documento(instance)

@receiver(post_delete, sender=LineaRepuesto)
def _recalc_doc_repuesto_delete(sender, instance, **kwargs):
    _recalc_documento(instance)

@receiver(post_save, sender=LineaServicio)
def _recalc_doc_servicio_save(sender, instance, **kwargs):
    _recalc_documento(instance)

@receiver(post_delete, sender=LineaServicio)
def _recalc_doc_servicio_delete(sender, instance, **kwargs):
    _recalc_documento(instance)

@receiver(post_save, sender=LineaOtroServicio)
def _recalc_doc_otro_save(sender, instance, **kwargs):
    _recalc_documento(instance)

@receiver(post_delete, sender=LineaOtroServicio)
def _recalc_doc_otro_delete(sender, instance, **kwargs):
    _recalc_documento(instance)
