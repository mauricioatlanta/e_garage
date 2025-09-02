from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Empresa, ConfiguracionEmpresa, CompanySettings


def _invalidate_cache_keys_for_empresa(empresa_id):
    """Invalidar cache para todos los países conocidos de una empresa"""
    countries = ["CL", "US", "NA"]
    for country in countries:
        cache_key = f"ctx_company:{empresa_id}:{country}"
        cache.delete(cache_key)


@receiver(post_save, sender=Empresa)
def empresa_saved(sender, instance, **kwargs):
    """Invalidar cache cuando se actualiza una Empresa"""
    _invalidate_cache_keys_for_empresa(instance.id)


@receiver(post_save, sender=ConfiguracionEmpresa)
def configuracion_empresa_saved(sender, instance, **kwargs):
    """Invalidar cache cuando se actualiza ConfiguracionEmpresa"""
    if hasattr(instance, 'empresa') and instance.empresa:
        _invalidate_cache_keys_for_empresa(instance.empresa.id)


@receiver(post_save, sender=CompanySettings)
def company_settings_saved(sender, instance, **kwargs):
    """Invalidar cache cuando se actualiza CompanySettings"""
    if hasattr(instance, 'user') and instance.user and hasattr(instance.user, 'empresa'):
        _invalidate_cache_keys_for_empresa(instance.user.empresa.id)