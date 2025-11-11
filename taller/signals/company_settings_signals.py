"""
Signals para tracking de cambios en CompanySettings
"""

# from taller.context_processors import invalidate_company_cache

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from taller.models import CompanySettings, CompanySettingsHistory


@receiver(pre_save, sender=CompanySettings)
def track_company_settings_changes(sender, instance, **kwargs):
    """
    Registra cambios en configuración de empresa antes de guardar
    """
    if instance.pk:  # Solo para updates, no para creates
        try:
            # Obtener instancia anterior
            old_instance = CompanySettings.objects.get(pk=instance.pk)

            # Campos a trackear
            tracked_fields = [
                "company_name",
                "tagline",
                "logo",
                "primary_color",
                "secondary_color",
                "address",
                "phone",
                "email",
                "website",
                "tax_id",
                "business_license",
                "currency",
                "invoice_prefix",
                "quote_prefix",
                "work_order_prefix",
                "about_text",
                "terms_and_conditions",
            ]

            changes = []

            for field in tracked_fields:
                old_value = getattr(old_instance, field, None)
                new_value = getattr(instance, field, None)

                # Manejar campos de archivo especialmente
                if field == "logo":
                    old_value = str(old_value) if old_value else None
                    new_value = str(new_value) if new_value else None

                # Solo registrar si hay cambios
                if old_value != new_value:
                    changes.append(
                        {
                            "field": field,
                            "old_value": (str(old_value) if old_value is not None else ""),
                            "new_value": (str(new_value) if new_value is not None else ""),
                        }
                    )

            # Guardar cambios en el contexto de la instancia para usar en post_save
            instance._changes_to_log = changes

        except CompanySettings.DoesNotExist:
            # Primera creación, no hay que trackear cambios
            instance._changes_to_log = []


@receiver(post_save, sender=CompanySettings)
def log_company_settings_changes(sender, instance, created, **kwargs):
    """
    Registra cambios después de guardar y limpia cache
    """
    # Limpiar cache de configuración
    # invalidate_company_cache(instance.user.id)

    # Registrar cambios si no es creación
    if not created and hasattr(instance, "_changes_to_log"):
        changes = instance._changes_to_log

        # Obtener usuario que hizo el cambio (puede ser difícil sin request)
        # Por ahora usamos el usuario propietario
        changed_by = instance.user

        for change in changes:
            CompanySettingsHistory.objects.create(
                company_settings=instance,
                changed_by=changed_by,
                field_changed=change["field"],
                old_value=change["old_value"],
                new_value=change["new_value"],
            )

        # Limpiar cambios temporales
        delattr(instance, "_changes_to_log")


@receiver(post_save, sender=User)
def create_default_company_settings(sender, instance, created, **kwargs):
    """
    Crea configuración por defecto para nuevos usuarios
    """
    if created:
        # Crear configuración básica por defecto
        CompanySettings.objects.create(
            user=instance,
            company_name=f"Taller de {instance.get_full_name() or instance.username}",
            primary_color="#0d6efd",
            secondary_color="#6c757d",
            currency="CLP",
        )
