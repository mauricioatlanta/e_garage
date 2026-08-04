"""
python manage.py process_outbox [--event-type commerce.order.submitted] [--limit 100]

Procesa eventos PENDING del outbox transaccional.
Seguro para ejecutar en cron — idempotente por event_id.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Procesa eventos pendientes del outbox transaccional."

    def add_arguments(self, parser):
        parser.add_argument(
            "--event-type",
            default=None,
            help="Filtrar por tipo de evento. Ej: commerce.order.submitted",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Número máximo de eventos a procesar por ejecución (default: 100)",
        )

    def handle(self, *args, **options):
        from runtime.services.outbox_service import OutboxService

        event_type = options["event_type"]
        limit = options["limit"]

        self.stdout.write(
            f"Procesando outbox (event_type={event_type or 'todos'}, limit={limit})…\n"
        )

        stats = OutboxService.process_pending(event_type=event_type, limit=limit)

        self.stdout.write(
            self.style.SUCCESS(
                f"✔ Procesados: {stats['processed']}  "
                f"Fallidos: {stats['failed']}  "
                f"Sin consumer: {stats['skipped']}\n"
            )
        )
