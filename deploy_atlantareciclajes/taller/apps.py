from django.apps import AppConfig


class TallerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "taller"
    verbose_name = "Gestión de Talleres"

    def ready(self):
        """
        Importar signals cuando la app esté lista
        """
        import taller.signals  # noqa
