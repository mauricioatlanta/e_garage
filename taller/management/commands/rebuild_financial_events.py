from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vehiculo_financial import VehicleFinancialEvent
from taller.services.financial_event_service import FinancialEventService
from taller.services.snapshot_generator_service import SnapshotGeneratorService
from taller.services.snapshot_queue import SnapshotQueue


class Command(BaseCommand):
    help = (
        "Rebuild missing VehicleFinancialEvent event_hash values, detect event collisions "
        "and enqueue snapshot generation for affected documents."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Solo reporta sin cambiar datos.")
        parser.add_argument("--fix", action="store_true", help="Aplica event_hash faltantes y encola snapshots.")
        parser.add_argument("--documento-id", type=int, help="Limita el proceso a un documento específico.")
        parser.add_argument("--vehiculo-id", type=int, help="Limita el proceso a un vehículo específico.")

    def handle(self, *args, **options):
        dry_run = options.get("dry_run")
        fix = options.get("fix") and not dry_run
        documento_id = options.get("documento_id")
        vehiculo_id = options.get("vehiculo_id")

        if dry_run and fix:
            self.stdout.write(self.style.WARNING("--dry-run activo, no se aplicarán cambios."))

        query = VehicleFinancialEvent.objects.filter(event_hash__isnull=True)
        if documento_id:
            query = query.filter(documento_id=documento_id)
        if vehiculo_id:
            query = query.filter(vehiculo_desarme_id=vehiculo_id)

        total_missing = query.count()
        self.stdout.write(f"Eventos financieros con event_hash NULL: {total_missing}")

        existing_collisions = list(
            VehicleFinancialEvent.objects.values("event_hash")
            .annotate(count=Count("id"))
            .filter(event_hash__isnull=False, count__gt=1)
        )
        if existing_collisions:
            self.stdout.write(self.style.WARNING("Eventos con event_hash duplicado ya existentes:"))
            for row in existing_collisions:
                self.stdout.write(f"  - {row['event_hash']} => {row['count']} eventos")

        candidate_events = list(query.order_by("created_at", "id").select_related("documento", "vehiculo_desarme", "empresa", "linea_repuesto"))
        hash_groups = defaultdict(list)
        skipped = []

        for event in candidate_events:
            event_hash = self._compute_hash_for_event(event)
            if event_hash is None:
                skipped.append(event)
                continue
            hash_groups[event_hash].append(event)

        fixed_count = 0
        collision_count = 0
        skipped_count = len(skipped)
        duplicate_count = 0
        affected_document_ids = set()
        affected_vehicle_ids = set()

        for event_hash, events in hash_groups.items():
            if not events:
                continue

            existing = VehicleFinancialEvent.objects.filter(event_hash=event_hash).order_by("created_at", "id").first()
            if existing:
                duplicate_count += len(events)
                self.stdout.write(
                    self.style.WARNING(
                        f"Colisión detectada para hash {event_hash}: existe evento {existing.id}, {len(events)} duplicados pendientes."
                    )
                )
                for event in events:
                    self.stdout.write(
                        f"    - evento #{event.id} tipo={event.event_type} vehiculo={event.vehiculo_desarme_id} documento={event.documento_id}"
                    )
                continue

            winner = events[0]
            duplicate_count += max(0, len(events) - 1)
            if len(events) > 1:
                self.stdout.write(
                    self.style.WARNING(
                        f"Múltiples eventos con mismo hash candidato {event_hash}: manteniendo evento #{winner.id}."
                    )
                )
                for event in events[1:]:
                    self.stdout.write(
                        f"    - evento duplicado #{event.id} tipo={event.event_type} vehiculo={event.vehiculo_desarme_id} documento={event.documento_id}"
                    )

            if fix:
                winner.event_hash = event_hash
                winner.save(update_fields=["event_hash"])
                fixed_count += 1
                self.stdout.write(self.style.SUCCESS(f"Asignado hash {event_hash} al evento #{winner.id}."))

            if winner.documento_id:
                affected_document_ids.add(winner.documento_id)
            if winner.vehiculo_desarme_id:
                affected_vehicle_ids.add(winner.vehiculo_desarme_id)

        for event in skipped:
            self.stdout.write(
                self.style.WARNING(
                    f"No se pudo regenerar hash para evento #{event.id} tipo={event.event_type} documento={event.documento_id} vehiculo={event.vehiculo_desarme_id}"
                )
            )

        self.stdout.write(f"Eventos procesados: {len(candidate_events)}")
        self.stdout.write(f"Hashes fijados: {fixed_count}")
        self.stdout.write(f"Hashes skippeados: {skipped_count}")
        self.stdout.write(f"Duplicados reportados: {duplicate_count}")

        if fix:
            with transaction.atomic():
                if affected_document_ids:
                    self.stdout.write("Encolando snapshots para documentos afectados...")
                    for doc_id in sorted(affected_document_ids):
                        documento = Documento.objects.filter(id=doc_id).first()
                        if not documento:
                            continue
                        if documento.estado == "EMITIDO":
                            SnapshotQueue.enqueue_for_document(documento)
                            self.stdout.write(f"  - Snapshot queued para documento #{doc_id}")
                        else:
                            self.stdout.write(f"  - Documento #{doc_id} no está EMITIDO, no se encola.")

                if affected_vehicle_ids:
                    self.stdout.write("Generando snapshots directos para vehículos sin documento asociado...")
                    for vehiculo_id in sorted(affected_vehicle_ids):
                        vehiculo = VehiculoDesarme.objects.filter(id=vehiculo_id).first()
                        if not vehiculo:
                            continue
                        SnapshotGeneratorService.generate_snapshot_for_vehicle(vehiculo)
                        self.stdout.write(f"  - Snapshot generado/validado para vehiculo #{vehiculo_id}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Este fue un dry run; no se aplicaron cambios."))

    def _compute_hash_for_event(self, event):
        if event.event_type == VehicleFinancialEvent.EVENT_TYPE_VENTA:
            if not event.linea_repuesto_id:
                return None
            linea = LineaRepuesto.objects.filter(id=event.linea_repuesto_id).first()
            if not linea:
                return None
            return FinancialEventService._compute_sale_hash(linea)

        if event.event_type == VehicleFinancialEvent.EVENT_TYPE_COMPRA:
            return FinancialEventService._compute_purchase_hash(
                event.vehiculo_desarme,
                event.empresa,
                event.monto,
                event.descripcion,
            )

        if event.event_type == VehicleFinancialEvent.EVENT_TYPE_COSTO:
            return FinancialEventService._compute_cost_hash(
                event.vehiculo_desarme,
                event.empresa,
                event.monto,
                event.descripcion,
            )

        return None
