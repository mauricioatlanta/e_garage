from unittest.mock import Mock
from contextlib import nullcontext

import pytest

from taller.services.snapshot_queue import SnapshotQueue
from taller.services.snapshot_scheduler import SnapshotScheduler
from taller.models import snapshot_queue as snapshot_queue_models


def test_snapshot_queue_enqueue_for_document_uses_pending_item(monkeypatch):
    documento = Mock()
    documento.empresa = Mock()
    expected_item = Mock()

    monkeypatch.setattr(
        snapshot_queue_models.SnapshotQueueItem.objects,
        "get_or_create",
        Mock(return_value=(expected_item, True)),
    )

    item = SnapshotQueue.enqueue_for_document(documento, delay_seconds=15)

    assert item is expected_item
    snapshot_queue_models.SnapshotQueueItem.objects.get_or_create.assert_called_once()


def test_snapshot_queue_process_pending_executes_services(monkeypatch):
    documento = Mock()
    documento.empresa = Mock()
    item = Mock(id=123, documento=documento, mark_processed=Mock())
    released_query = Mock()
    released_query.update = Mock(return_value=0)

    candidate_values = Mock()
    candidate_values.__getitem__ = Mock(return_value=[123])

    candidate_order = Mock()
    candidate_order.values_list = Mock(return_value=candidate_values)

    candidate_query = Mock()
    candidate_query.order_by = Mock(return_value=candidate_order)

    candidate_values = Mock()
    candidate_values.__getitem__ = Mock(return_value=[123])

    candidate_order.values_list = Mock(return_value=candidate_values)

    claimed_query = Mock()
    claimed_query.update = Mock(return_value=1)

    worker_query = Mock()
    worker_query.order_by.return_value = [item]

    filter_responses = [
        released_query,
        candidate_query,
        claimed_query,
        worker_query,
    ]

    def fake_filter(*args, **kwargs):
        return filter_responses.pop(0)

    monkeypatch.setattr(
        snapshot_queue_models.SnapshotQueueItem.objects,
        "filter",
        Mock(side_effect=fake_filter),
    )

    called = {"snapshot": False, "events": False, "lifecycle": False}

    monkeypatch.setattr(
        "taller.services.snapshot_queue.SnapshotGeneratorService.generate_snapshot_for_document",
        Mock(side_effect=lambda doc: called.update({"snapshot": True}) or []),
    )
    monkeypatch.setattr(
        "taller.services.snapshot_queue.FinancialEventService.sync_events_for_documento",
        Mock(side_effect=lambda doc: called.update({"events": True}) or []),
    )
    monkeypatch.setattr(
        "taller.services.snapshot_queue.VehicleLifecycleService.update_lifecycle_for_documento",
        Mock(side_effect=lambda doc: called.update({"lifecycle": True}) or []),
    )

    monkeypatch.setattr(
        "taller.services.snapshot_queue.transaction.atomic",
        nullcontext,
    )

    results = SnapshotQueue.process_pending(batch=1)

    assert results == [(123, True, None)]
    item.mark_processed.assert_called_once()
    assert called["snapshot"]
    assert called["events"]
    assert called["lifecycle"]

    monkeypatch.setattr(
        SnapshotQueue,
        "process_pending",
        Mock(return_value=results),
    )

    assert SnapshotScheduler.process_pending(batch=1) == results


def test_snapshot_queue_releases_stale_lock(monkeypatch):
    documento = Mock()
    documento.empresa = Mock()

    stale_item = Mock(
        id=999,
        documento=documento,
        mark_processed=Mock(),
        attempts=0,
        last_error=None,
    )

    released_query = Mock()
    released_query.update = Mock(return_value=1)

    candidate_values = Mock()
    candidate_values.__getitem__ = Mock(return_value=[999])

    candidate_order = Mock()
    candidate_order.values_list = Mock(return_value=candidate_values)

    candidate_query = Mock()
    candidate_query.order_by = Mock(return_value=candidate_order)

    claimed_query = Mock()
    claimed_query.update = Mock(return_value=1)

    worker_query = Mock()
    worker_query.order_by.return_value = [stale_item]

    filter_responses = [
        released_query,
        candidate_query,
        claimed_query,
        worker_query,
    ]

    def fake_filter(*args, **kwargs):
        return filter_responses.pop(0)

    monkeypatch.setattr(
        snapshot_queue_models.SnapshotQueueItem.objects,
        "filter",
        Mock(side_effect=fake_filter),
    )

    monkeypatch.setattr(
        "taller.services.snapshot_queue.SnapshotGeneratorService.generate_snapshot_for_document",
        Mock(return_value=[]),
    )

    monkeypatch.setattr(
        "taller.services.snapshot_queue.FinancialEventService.sync_events_for_documento",
        Mock(return_value=[]),
    )

    monkeypatch.setattr(
        "taller.services.snapshot_queue.VehicleLifecycleService.update_lifecycle_for_documento",
        Mock(return_value=[]),
    )

    monkeypatch.setattr(
        "taller.services.snapshot_queue.transaction.atomic",
        nullcontext,
    )

    results = SnapshotQueue.process_pending(batch=1)

    assert results == [(999, True, None)]
    stale_item.mark_processed.assert_called_once()
