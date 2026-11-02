from django.core.management.base import BaseCommand

from taller.services.snapshot_scheduler import SnapshotScheduler


class Command(BaseCommand):
    help = "Procesa la cola de snapshots pendientes usando el scheduler"

    def add_arguments(self, parser):
        parser.add_argument("--batch", type=int, default=100, help="Tamaño del lote a procesar")

    def handle(self, *args, **options):
        batch = options.get("batch")
        results = SnapshotScheduler.process_pending(batch=batch)
        processed = sum(1 for _, ok, _ in results if ok)
        failed = len(results) - processed
        self.stdout.write(f"Processed: {processed}, Failed: {failed}")