from django.apps import AppConfig


class TallerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "taller"

    def ready(self):
        """Registra signals cuando la app está lista"""
        # Importar signals para registro automático
        try:
            import taller.models.signals_memoria  # noqa: F401
        except ImportError:
            # Si no existe, continuar (no crítico)
            pass
    verbose_name = "Gestión de Talleres"

    def ready(self):
        """
        Importar signals cuando la app esté lista
        """
        import taller.signals  # noqa
        # Importar signals de memoria para cleanup de archivos
        try:
            import taller.models.signals_memoria  # noqa: F401
        except ImportError:
            pass  # Signals de memoria no disponibles