from django.db.models.signals import pre_save
from django.dispatch import receiver
from taller.models.lineas_documento import LineaRepuesto


@receiver(pre_save, sender=LineaRepuesto)
def enforce_tenant(sender, instance, **kwargs):
    if instance.repuesto and instance.documento:
        if instance.repuesto.empresa_id != instance.documento.empresa_id:
            raise Exception(
                f"[TENANT VIOLATION] repuesto {instance.repuesto_id} "
                f"no pertenece a empresa {instance.documento.empresa_id}"
            )
