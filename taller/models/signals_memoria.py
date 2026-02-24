"""
Signals para cleanup de archivos físicos de EvidenciaDocumento
"""

import os

from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from taller.models.memoria_seguimiento import EvidenciaDocumento


@receiver(post_delete, sender=EvidenciaDocumento)
def delete_evidencia_archivo(sender, instance, **kwargs):
    """
    Elimina el archivo físico cuando se borra una EvidenciaDocumento.
    """
    if instance.archivo:
        try:
            if os.path.isfile(instance.archivo.path):
                os.remove(instance.archivo.path)
        except Exception:
            # Si hay error al borrar (archivo no existe, permisos, etc), ignorar
            # No queremos que un error de cleanup rompa el delete del objeto
            pass


@receiver(pre_save, sender=EvidenciaDocumento)
def delete_evidencia_archivo_old(sender, instance, **kwargs):
    """
    Elimina el archivo físico antiguo cuando se reemplaza un archivo.
    Solo se ejecuta si el archivo está siendo reemplazado (update con nuevo archivo).
    """
    if instance.pk:
        try:
            old_instance = EvidenciaDocumento.objects.get(pk=instance.pk)
            # Si el archivo cambió, borrar el antiguo
            if old_instance.archivo and old_instance.archivo != instance.archivo:
                try:
                    if os.path.isfile(old_instance.archivo.path):
                        os.remove(old_instance.archivo.path)
                except Exception:
                    # Si hay error, ignorar (no romper el save)
                    pass
        except EvidenciaDocumento.DoesNotExist:
            # Si no existe el objeto antiguo (no debería pasar), continuar
            pass
