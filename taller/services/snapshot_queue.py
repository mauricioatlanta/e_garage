from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from taller.models.snapshot_queue import SnapshotQueueItem
from taller.services.financial_event_service import FinancialEventService
from taller.services.snapshot_generator_service import SnapshotGeneratorService
from taller.services.vehicle_lifecycle_service import VehicleLifecycleService


class SnapshotQueue:
    @classmethod
    def enqueue_for_document(cls, documento, delay_seconds=0):
        empresa = getattr(documento, "empresa", None)
        if not empresa:
            return None

        scheduled_at = timezone.now() + timedelta(seconds=delay_seconds)

        item, created = SnapshotQueueItem.objects.get_or_create(
            documento=documento,
            processed_at__isnull=True,
            defaults={"empresa": empresa, "scheduled_at": scheduled_at},
        )

        if not created and scheduled_at < item.scheduled_at:
            item.scheduled_at = scheduled_at
            item.save(update_fields=["scheduled_at"])

        return item

    @classmethod
    def process_pending(cls, batch=100):
        import os
        import socket
        import uuid

        now = timezone.now()

        worker_id = f"{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:8]}"

        stale_lock_cutoff = now - timedelta(minutes=5)

        SnapshotQueueItem.objects.filter(
            processed_at__isnull=True,
            locked_at__lt=stale_lock_cutoff,
        ).update(
            locked_at=None,
            worker_id=None,
        )

        with transaction.atomic():

            candidate_ids = list(
                SnapshotQueueItem.objects.filter(
                    processed_at__isnull=True,
                    locked_at__isnull=True,
                    scheduled_at__lte=now,
                )
                .order_by("scheduled_at")
                .values_list("id", flat=True)[:batch]
            )

            SnapshotQueueItem.objects.filter(
                id__in=candidate_ids,
                processed_at__isnull=True,
                locked_at__isnull=True,
            ).update(
                locked_at=now,
                worker_id=worker_id,
            )

            items = list(
                SnapshotQueueItem.objects.filter(
                    worker_id=worker_id,
                    processed_at__isnull=True,
                ).order_by("scheduled_at")
            )

        results = []

        for item in items:
            try:
                with transaction.atomic():
                    locked = SnapshotQueueItem.objects.filter(
                        id=item.id,
                        processed_at__isnull=True,
                        worker_id=worker_id,
                    ).exists()

                    if not locked:
                        results.append((item.id, False, "lock_lost"))
                        continue

                    FinancialEventService.sync_events_for_documento(item.documento)
                    VehicleLifecycleService.update_lifecycle_for_documento(item.documento)
                    SnapshotGeneratorService.generate_snapshot_for_document(item.documento)
                    item.mark_processed()

                results.append((item.id, True, None))

            except Exception as exc:  # noqa: BLE001

                current = SnapshotQueueItem.objects.filter(
                    id=item.id
                ).values(
                    "processed_at",
                    "attempts",
                ).first()

                if current and current["processed_at"]:
                    results.append((item.id, False, "already_processed"))
                    continue

                item.attempts = (current or {}).get("attempts", 0) + 1
                item.last_error = str(exc)
                item.locked_at = None
                item.worker_id = None

                item.save(
                    update_fields=[
                        "attempts",
                        "last_error",
                        "locked_at",
                        "worker_id",
                    ]
                )

                results.append((item.id, False, str(exc)))

        return results
