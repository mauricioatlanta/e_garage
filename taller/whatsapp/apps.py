"""
AppConfig para taller.whatsapp
Define el label como 'whatsapp' para compatibilidad con comandos Django
"""

from django.apps import AppConfig


class WhatsappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "taller.whatsapp"
    label = "whatsapp"  # Label corto para comandos: makemigrations whatsapp, migrate whatsapp
    verbose_name = "WhatsApp eGarage"

    def ready(self):
        """Importar señales si es necesario"""
        # Si necesitas importar señales aquí, hazlo
        # import taller.whatsapp.signals  # noqa
        pass
