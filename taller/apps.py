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
        from django.db.backends.signals import connection_created

        def _sqlite_wal(sender, connection, **kwargs):
            # WAL mode + synchronous NORMAL: previene corrupción con múltiples workers
            # y mejora resiliencia ante apagados sin desmontar el filesystem.
            if connection.vendor == "sqlite":
                cursor = connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")

        connection_created.connect(_sqlite_wal)

        import taller.signals
        import taller.signals.tenant_guard  # noqa: F401

        # Señales de inventario (pre_save Documento → mover stock al cambiar estado)
        try:
            import taller.documentos.signals_inventory  # noqa: F401
        except ImportError:
            pass

        # Señales financieras para desarme: eventos, snapshots y lifecycle
        try:
            import taller.documentos.signals_financial  # noqa: F401
        except ImportError:
            pass

        # Señales legacy de LineaDocumento desactivadas.
        # El sistema operativo actual usa LineaRepuesto / LineaServicio / LineaOtroServicio.

        # Señales de memoria para cleanup de archivos
        try:
            import taller.models.signals_memoria  # noqa: F401
        except ImportError:
            pass
