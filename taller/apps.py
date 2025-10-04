from django.apps import AppConfig


class TallerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'taller'

    def ready(self):
        # Importar señales para activar los receivers
        from . import signals  # noqa