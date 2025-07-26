# Crea automáticamente una Empresa cuando un nuevo usuario se registra
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models.empresa import Empresa

@receiver(post_save, sender=User)
def crear_empresa_al_crear_usuario(sender, instance, created, **kwargs):
    if created:
        Empresa.objects.get_or_create(
            user=instance,
            defaults={
                'nombre_taller': f"Taller de {instance.username}",
                'empresa': instance.username,
            }
        )
