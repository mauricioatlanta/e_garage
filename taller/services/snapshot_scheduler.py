from taller.services.snapshot_queue import SnapshotQueue


class SnapshotScheduler:
    """Scheduler administrativo para procesar snapshots en background."""

    @classmethod
    def schedule_document(cls, documento, delay_seconds=0):
        """Encola un documento para regenerar los snapshots asociados."""
        return SnapshotQueue.enqueue_for_document(documento, delay_seconds=delay_seconds)

    @classmethod
    def process_pending(cls, batch=100):
        """Procesa los items pendientes de la cola de snapshots."""
        return SnapshotQueue.process_pending(batch=batch)

    @classmethod
    def run(cls, batch=100):
        """Alias para ejecutar el scheduler de snapshots."""
        return cls.process_pending(batch=batch)
