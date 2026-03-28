from django.apps import AppConfig


class TallerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "taller"
    verbose_name = "Gestión de Talleres"

    def ready(self):
        """
        Importar signals cuando la app esté lista.
        La app instalada es 'taller', no 'taller.documentos', por eso las señales
        de documentos deben cargarse aquí para que se ejecuten al arrancar.
        """
        import taller.signals  # noqa: F401

        # Señales de inventario (pre_save Documento → mover stock al cambiar estado)
        try:
            import taller.documentos.signals_inventory  # noqa: F401
        except ImportError:
            pass

        # Señales legacy de LineaDocumento desactivadas.
        # El sistema operativo actual usa LineaRepuesto / LineaServicio / LineaOtroServicio.

        # Señales de memoria para cleanup de archivos
        try:
            import taller.models.signals_memoria  # noqa: F401
        except ImportError:
            pass
