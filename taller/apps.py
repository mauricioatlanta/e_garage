from django.apps import AppConfig


class TallerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "taller"
    verbose_name = "Gestión de Talleres"

    def ready(self):
        """
        Registrar signals cuando la app está lista.
        IMPORTANTE: mantener un solo ready() (si hay 2, el último pisa al primero).
        """
        # Signals de totales de documento (recompute_totals persistente)
        import taller.models.signals_documento  # noqa: F401

        # (Opcional) si aún usas un módulo agregado legacy
        try:
            import taller.signals  # noqa: F401
        except Exception:
            pass

        # Signals de memoria / cleanup de archivos (no crítico)
        try:
            import taller.models.signals_memoria  # noqa: F401
        except ImportError:
            pass
