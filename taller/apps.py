from django.apps import AppConfig
from django.db.backends.signals import connection_created


def _sqlite_wal(sender, connection, **kwargs):
    # WAL mode + synchronous NORMAL: previene corrupción con múltiples workers
    # y mejora resiliencia ante apagados sin desmontar el filesystem.
    # Usa la conexión raw (sqlite3.Connection) para saltarse el wrapper de Django.
    # Definida a nivel de módulo para que la referencia débil del signal no la garbage-collect.
    if connection.vendor == "sqlite" and connection.connection is not None:
        connection.connection.execute("PRAGMA journal_mode=WAL")
        connection.connection.execute("PRAGMA synchronous=NORMAL")


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
        connection_created.connect(_sqlite_wal, weak=False)

        import taller.signals
        import taller.signals.tenant_guard  # noqa: F401
        import taller.signals.trust  # noqa: F401

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
