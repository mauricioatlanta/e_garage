from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import importlib
import threading
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.db import close_old_connections, connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder
from django.db.models import Count
from django.utils import timezone

checkpoint_migration = importlib.import_module(
    "taller.migrations.0183_public_analytics_backfill_checkpoint"
)
backfill = importlib.import_module(
    "taller.migrations.0184_backfill_public_analytics_sessions"
)


TARGET_0182 = ("taller", "0182_public_analytics_event_transition_fields")
TARGET_0183 = ("taller", "0183_public_analytics_backfill_checkpoint")
TARGET_0184 = ("taller", "0184_backfill_public_analytics_sessions")


@pytest.fixture
def migration_0182_apps():
    executor = MigrationExecutor(connection)
    executor.migrate([TARGET_0183])
    call_command("flush", interactive=False, verbosity=0)
    apps = executor.loader.project_state([TARGET_0183]).apps
    apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint").objects.create(
        key=backfill.CHECKPOINT_KEY,
        captured_at=timezone.now(),
        status=backfill.CHECKPOINT_READY,
    )
    yield apps, executor
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    if Checkpoint._meta.db_table in connection.introspection.table_names():
        Checkpoint.objects.filter(key=backfill.CHECKPOINT_KEY).update(
            status=backfill.CHECKPOINT_READY,
            owner_token=None,
            lease_expires_at=None,
            completed_at=None,
        )
    MigrationExecutor(connection).migrate([TARGET_0184])


def _models(apps):
    return (
        apps.get_model("taller", "PublicAnalyticsEvent"),
        apps.get_model("taller", "PublicAnalyticsSession"),
        apps.get_model("taller", "PublicPageView"),
    )


def _page(PageView, *, session_key="", created_at=None, **kwargs):
    return PageView.objects.create(
        path=kwargs.pop("path", "/cl/desarmadurias/"),
        page_type=kwargs.pop("page_type", "landing"),
        country=kwargs.pop("country", "cl"),
        language=kwargs.pop("language", "es"),
        visitor_hash=kwargs.pop("visitor_hash", "v" * 64),
        session_key=session_key,
        referrer=kwargs.pop("referrer", "https://example.test"),
        user_agent=kwargs.pop("user_agent", "Mozilla/5.0"),
        created_at=created_at or timezone.now(),
        **kwargs,
    )


def _event(Event, *, event_type="signup_start", session_key="", created_at=None, **kwargs):
    return Event.objects.create(
        event_type=event_type,
        path=kwargs.pop("path", "/cl/desarmadurias/"),
        session_key=session_key,
        metadata=kwargs.pop("metadata", {}),
        created_at=created_at or timezone.now(),
        **kwargs,
    )


def _run_forward(apps, cutoffs=None):
    Event, _, PageView = _models(apps)
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    checkpoint = Checkpoint.objects.get(key=backfill.CHECKPOINT_KEY)
    if cutoffs is None:
        cutoffs = (
            Event.objects.order_by("-pk").values_list("pk", flat=True).first(),
            PageView.objects.order_by("-pk").values_list("pk", flat=True).first(),
        )
    checkpoint.cutoff_event_pk, checkpoint.cutoff_pageview_pk = cutoffs
    checkpoint.status = backfill.CHECKPOINT_READY
    checkpoint.completed_at = None
    checkpoint.save(update_fields=["cutoff_event_pk", "cutoff_pageview_pk", "status", "completed_at"])
    with connection.schema_editor(atomic=False) as schema_editor:
        backfill.forwards(apps, schema_editor)


@pytest.mark.django_db(transaction=True)
def test_same_key_groups_rows_and_preserves_first_touch(migration_0182_apps):
    apps, executor = migration_0182_apps
    Event, Session, PageView = _models(apps)
    first = timezone.now() - timedelta(days=4)
    page = _page(
        PageView,
        session_key="  same-key  ",
        created_at=first,
        utm_source="google",
        utm_campaign="first",
    )
    first_event = _event(
        Event,
        event_type="signup_start",
        session_key="same-key",
        page_view=page,
        created_at=first + timedelta(minutes=1),
        utm_source="meta",
        utm_campaign="later",
    )
    second_event = _event(
        Event,
        event_type="signup_complete",
        session_key="same-key",
        page_view=page,
        created_at=first + timedelta(minutes=2),
    )

    _run_forward(apps)

    page.refresh_from_db()
    first_event.refresh_from_db()
    second_event.refresh_from_db()
    assert Session.objects.count() == 1
    assert page.public_session_id == first_event.session_id == second_event.session_id
    assert Session.objects.get().utm_campaign == "first"
    assert first_event.event_type == "signup_started"
    assert second_event.event_type == "signup_completed"
    assert first_event.dedupe_key == f"legacy-event-{first_event.pk}"
    assert first_event.occurred_at == first_event.created_at
    assert first_event.metadata["_legacy_reconstruction"]["fields_changed"] == [
        "metadata",
        "event_type",
    ]


@pytest.mark.django_db(transaction=True)
def test_distinct_and_keyless_identities_are_not_grouped(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, Session, PageView = _models(apps)
    page = _page(PageView, session_key="")
    linked = _event(Event, page_view=page, session_key="")
    orphan = _event(Event, session_key="")
    different = _event(Event, session_key="different")
    standalone = _page(PageView, session_key="")

    _run_forward(apps)

    linked.refresh_from_db()
    orphan.refresh_from_db()
    different.refresh_from_db()
    page.refresh_from_db()
    standalone.refresh_from_db()
    assert linked.session_id == page.public_session_id
    assert orphan.session_id != linked.session_id
    assert different.session_id not in {linked.session_id, orphan.session_id}
    assert standalone.public_session_id is None
    assert Session.objects.count() == 3


@pytest.mark.django_db(transaction=True)
def test_multiple_existing_sessions_leave_group_pending_without_third_session(
    migration_0182_apps,
):
    apps, _ = migration_0182_apps
    Event, Session, PageView = _models(apps)
    first_session = Session.objects.create(
        anonymous_visitor_hash="a" * 64,
        anonymous_session_hash="b" * 64,
        first_path="/one",
        expires_at=timezone.now() + timedelta(days=30),
    )
    second_session = Session.objects.create(
        anonymous_visitor_hash="c" * 64,
        anonymous_session_hash="d" * 64,
        first_path="/two",
        expires_at=timezone.now() + timedelta(days=30),
    )
    first_page = _page(PageView, session_key="conflict")
    second_page = _page(PageView, session_key="conflict")
    PageView.objects.filter(pk=first_page.pk).update(public_session_id=first_session.pk)
    PageView.objects.filter(pk=second_page.pk).update(public_session_id=second_session.pk)
    event = _event(Event, session_key="conflict")

    _run_forward(apps)

    event.refresh_from_db()
    assert event.session_id is None
    assert event.dedupe_key is None
    assert event.occurred_at is None
    assert Session.objects.count() == 2


@pytest.mark.django_db(transaction=True)
def test_conflicting_group_terminates_and_does_not_repeat_mutations(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, Session, PageView = _models(apps)
    first_page = _page(PageView, session_key="persistent-conflict")
    second_page = _page(PageView, session_key="persistent-conflict")
    for page, marker in ((first_page, "a"), (second_page, "b")):
        session = Session.objects.create(
            anonymous_visitor_hash=marker * 64,
            anonymous_session_hash=(marker.upper() * 64),
            first_path="/",
            expires_at=timezone.now() + timedelta(days=30),
        )
        PageView.objects.filter(pk=page.pk).update(public_session_id=session.pk)
    event = _event(Event, session_key="persistent-conflict")

    _run_forward(apps)
    before = Session.objects.count()
    _run_forward(apps)

    event.refresh_from_db()
    assert event.session_id is None
    assert Session.objects.count() == before


@pytest.mark.django_db(transaction=True)
def test_existing_session_values_and_metadata_ledger_are_idempotent(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, Session, PageView = _models(apps)
    event = _event(
        Event,
        event_type="signup_start",
        session_key="existing",
        dedupe_key="existing-key",
        occurred_at=timezone.now() - timedelta(days=2),
        metadata={"source": "legacy"},
    )

    _run_forward(apps)
    event.refresh_from_db()
    snapshot = (event.session_id, event.dedupe_key, event.occurred_at, event.metadata)
    count = Session.objects.count()
    _run_forward(apps)
    event.refresh_from_db()
    assert (event.session_id, event.dedupe_key, event.occurred_at, event.metadata) == snapshot
    assert Session.objects.count() == count


@pytest.mark.django_db(transaction=True)
def test_mapping_rules_and_legacy_events(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, _, _ = _models(apps)
    landing = _event(Event, event_type="landing_view")
    internal = _event(Event, event_type="landing_view", is_internal=True)
    signup = _event(Event, event_type="signup_complete")
    cta = _event(Event, event_type="cta_click", metadata={"cta_id": "trial_30"})
    ambiguous = _event(Event, event_type="cta_click", metadata={"cta_label": "Prueba"})
    onboarding = _event(Event, event_type="onboarding_complete")
    paid = _event(Event, event_type="subscription_paid")

    _run_forward(apps)

    for event in (landing, internal, signup, cta, ambiguous, onboarding, paid):
        event.refresh_from_db()
    assert landing.event_type == "human_visit"
    assert internal.event_type == "landing_view"
    assert signup.event_type == "signup_completed"
    assert cta.event_type == "cta_trial_30_click"
    assert ambiguous.event_type == "cta_click"
    assert onboarding.event_type == "onboarding_complete"
    assert paid.event_type == "subscription_paid"


@pytest.mark.django_db(transaction=True)
def test_metadata_scalars_are_wrapped_and_reserved_keys_are_untouched(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, _, _ = _models(apps)
    values = [None, [1, "x"], "legacy", 12.5, True]
    events = [_event(Event, metadata=value) for value in values[1:]]
    reserved = _event(Event, metadata={"_legacy_reconstruction": {"version": 99}})

    for value in values:
        fake = SimpleNamespace(metadata=value, event_type="signup_start", pk=9000)
        wrapped, ledger = backfill._prepare_metadata(fake, "signup_started")
        assert ledger["original_metadata_kind"] in {
            "json_null",
            "list",
            "string",
            "number",
            "boolean",
        }
        assert wrapped["_legacy_reconstruction"]["version"] == 1

    _run_forward(apps)
    reserved.refresh_from_db()
    assert reserved.metadata == {"_legacy_reconstruction": {"version": 99}}
    for event in events:
        event.refresh_from_db()
        assert "_legacy_reconstruction" in event.metadata
        assert "_legacy_original_metadata" in event.metadata


@pytest.mark.django_db(transaction=True)
def test_reverse_is_conservative_and_keeps_sessions_and_pageview_links(migration_0182_apps):
    apps, executor = migration_0182_apps
    Event, Session, PageView = _models(apps)
    page = _page(PageView, session_key="reverse-key")
    event = _event(Event, event_type="signup_start", session_key="reverse-key", page_view=page)

    _run_forward(apps)
    page.refresh_from_db()
    session_id = page.public_session_id
    with connection.schema_editor() as schema_editor:
        backfill.backwards(apps, schema_editor)

    apps_after_reverse = executor.loader.project_state([TARGET_0182]).apps
    EventAfter, SessionAfter, PageAfter = _models(apps_after_reverse)
    restored = EventAfter.objects.get(pk=event.pk)
    assert restored.event_type == "signup_start"
    assert restored.session_id is None
    assert restored.dedupe_key is None
    assert restored.occurred_at is None
    assert restored.metadata == {}
    assert SessionAfter.objects.filter(pk=session_id).exists()
    assert PageAfter.objects.get(pk=page.pk).public_session_id == session_id


@pytest.mark.django_db(transaction=True)
def test_register_funnel_is_never_touched(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, _, _ = _models(apps)
    assert apps.get_model("taller", "RegistroEmbudoSuscriptor").objects.count() == 0
    _event(Event)
    _run_forward(apps)
    assert apps.get_model("taller", "RegistroEmbudoSuscriptor").objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_session_hashes_are_deterministic_and_unique(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, Session, _ = _models(apps)
    first = _event(Event, session_key="hash-a")
    second = _event(Event, session_key="hash-b")
    _run_forward(apps)
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.session_id != second.session_id
    assert Session.objects.values("anonymous_session_hash").annotate(
        total=Count("id")
    ).filter(total__gt=1).count() == 0


@pytest.mark.django_db(transaction=True)
def test_legacy_event_key_links_related_keyless_pageview(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, _, PageView = _models(apps)
    page = _page(PageView, session_key="")
    event = _event(Event, session_key="related-key", page_view=page)

    _run_forward(apps)

    page.refresh_from_db()
    event.refresh_from_db()
    assert page.public_session_id == event.session_id


@pytest.mark.django_db(transaction=True)
def test_related_nonmatching_keys_are_an_intact_conflict(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, Session, PageView = _models(apps)
    page = _page(PageView, session_key="A")
    event = _event(Event, session_key="B", page_view=page)

    _run_forward(apps)

    page.refresh_from_db()
    event.refresh_from_db()
    assert page.public_session_id is None
    assert event.session_id is None
    assert event.dedupe_key is None
    assert event.occurred_at is None
    assert event.metadata == {}
    assert Session.objects.count() == 0


def _valid_object_ledger(event):
    ledger = {
        "version": 1,
        "legacy_event_id": event.pk,
        "legacy_event_type": event.event_type,
        "mapped_event_type": event.event_type,
        "fields_filled": [],
        "fields_changed": ["metadata"],
        "original_metadata_kind": "object",
        "original_metadata_wrapped": False,
        "original_metadata_digest": backfill._json_digest({"source": "legacy"}),
    }
    ledger["ledger_digest"] = backfill._json_digest(ledger)
    return ledger


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("variant", ["missing", "altered", "content", "version", "event_id"])
def test_invalid_preexisting_ledger_is_left_completely_intact(migration_0182_apps, variant):
    apps, _ = migration_0182_apps
    Event, Session, _ = _models(apps)
    event = _event(Event, metadata={"source": "legacy"})
    ledger = _valid_object_ledger(event)
    if variant == "missing":
        del ledger["ledger_digest"]
    elif variant == "altered":
        ledger["ledger_digest"] = "0" * 64
    elif variant == "content":
        ledger["legacy_event_type"] = "cta_click"
    elif variant == "version":
        ledger["version"] = 99
        ledger["ledger_digest"] = backfill._json_digest(ledger)
    elif variant == "event_id":
        ledger["legacy_event_id"] = event.pk + 1
        ledger["ledger_digest"] = backfill._json_digest(ledger)
    metadata = {"source": "legacy", "_legacy_reconstruction": ledger}
    Event.objects.filter(pk=event.pk).update(metadata=metadata)

    _run_forward(apps)

    event.refresh_from_db()
    assert event.metadata == metadata
    assert event.session_id is None
    assert event.dedupe_key is None
    assert event.occurred_at is None
    assert Session.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_valid_ledger_is_idempotent_and_digest_protected(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, Session, _ = _models(apps)
    event = _event(Event, metadata={"source": "legacy"})
    _run_forward(apps)
    event.refresh_from_db()
    snapshot = event.metadata
    session_id = event.session_id

    _run_forward(apps)

    event.refresh_from_db()
    assert event.metadata == snapshot
    assert event.session_id == session_id
    assert Session.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_key_union_processes_shared_key_once(migration_0182_apps, monkeypatch):
    apps, _ = migration_0182_apps
    Event, _, PageView = _models(apps)
    page = _page(PageView, session_key=" shared-key ")
    _event(Event, session_key="shared-key", page_view=page)
    calls = []
    original = backfill._process_group

    def counted(*args, **kwargs):
        calls.append(args[3])
        return original(*args, **kwargs)

    monkeypatch.setattr(backfill, "_process_group", counted)
    counters = backfill._new_counters()
    backfill._process_key_groups(
        Event,
        PageView,
        apps.get_model("taller", "PublicAnalyticsSession"),
        counters,
        Event.objects.order_by("-pk").values_list("pk", flat=True).first(),
        PageView.objects.order_by("-pk").values_list("pk", flat=True).first(),
    )

    assert calls == ["key:shared-key"]
    assert counters["sessions_created"] == 1


@pytest.mark.django_db(transaction=True)
def test_canonical_and_unknown_only_pageviews_are_not_legacy_evidence(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, Session, PageView = _models(apps)
    canonical_page = _page(PageView, session_key="canonical-only")
    unknown_page = _page(PageView, session_key="unknown-only")
    _event(Event, event_type="signup_started", session_key="canonical-only", page_view=canonical_page)
    _event(Event, event_type="future_event", session_key="unknown-only", page_view=unknown_page)

    _run_forward(apps)

    canonical_page.refresh_from_db()
    unknown_page.refresh_from_db()
    assert canonical_page.public_session_id is None
    assert unknown_page.public_session_id is None
    assert Session.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_existing_single_session_is_reused(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, Session, _ = _models(apps)
    identity = "key:existing-authority"
    session = Session.objects.create(
        anonymous_visitor_hash=backfill._visitor_hash(identity),
        anonymous_session_hash=backfill._session_hash(identity),
        first_path="/existing",
        expires_at=timezone.now() + timedelta(days=30),
    )
    event = _event(Event, session_key="existing-authority")

    _run_forward(apps)

    event.refresh_from_db()
    assert event.session_id == session.pk
    assert Session.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_invalid_visitor_hash_uses_deterministic_fallback(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, Session, PageView = _models(apps)
    page = _page(PageView, session_key="visitor-fallback", visitor_hash="not-a-hash")
    event = _event(Event, session_key="visitor-fallback", page_view=page)

    _run_forward(apps)

    event.refresh_from_db()
    session = Session.objects.get(pk=event.session_id)
    assert session.anonymous_visitor_hash == backfill._visitor_hash("key:visitor-fallback")
    assert len(session.anonymous_visitor_hash) == 64


@pytest.mark.parametrize(
    "value, expected",
    [
        ("a" * 64, True),
        ("A" * 64, True),
        ("  " + "a" * 64 + "  ", True),
        ("g" * 64, False),
        ("a" * 63, False),
        ("a" * 65, False),
    ],
)
def test_visitor_hash_validation_is_hex_and_normalizes_outer_spaces(value, expected):
    assert backfill._valid_visitor_hash(value) is expected


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("flag", ["is_bot", "is_internal", "is_staff", "is_server"])
def test_bot_and_internal_flags_preserve_legacy_mapping(migration_0182_apps, flag):
    apps, _ = migration_0182_apps
    Event, _, _ = _models(apps)
    event = _event(Event, event_type="signup_start", **{flag: True})

    _run_forward(apps)

    event.refresh_from_db()
    assert event.event_type == "signup_start"


@pytest.mark.django_db(transaction=True)
def test_expiration_and_presentation_fields_are_historical_and_bounded(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, Session, PageView = _models(apps)
    first = timezone.now() - timedelta(days=9)
    page = _page(
        PageView,
        session_key="bounded-fields",
        created_at=first,
        path="/" + "p" * 400,
        referrer="r" * 700,
        utm_campaign="c" * 300,
    )
    event = _event(Event, session_key="bounded-fields", page_view=page, created_at=first)

    _run_forward(apps)

    event.refresh_from_db()
    session = Session.objects.get(pk=event.session_id)
    assert session.expires_at == first + timedelta(days=30)
    assert len(session.first_path) <= 255
    assert len(session.initial_referrer) <= 500
    assert len(session.utm_campaign) <= 150


@pytest.mark.django_db(transaction=True)
def test_shared_identity_volume_is_idempotent(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, Session, _ = _models(apps)
    events = [_event(Event, session_key="volume-key") for _ in range(40)]

    _run_forward(apps)
    first_snapshot = list(Event.objects.filter(pk__in=[e.pk for e in events]).values_list("session_id", "dedupe_key"))
    _run_forward(apps)

    assert Session.objects.count() == 1
    assert list(Event.objects.filter(pk__in=[e.pk for e in events]).values_list("session_id", "dedupe_key")) == first_snapshot


@pytest.mark.django_db(transaction=True)
def test_technical_group_failure_rolls_back_and_can_resume(migration_0182_apps, monkeypatch):
    apps, _ = migration_0182_apps
    Event, Session, _ = _models(apps)
    event = _event(Event, session_key="resume-key")
    original_save = Event.save
    failed = []

    def fail_once(self, *args, **kwargs):
        if self.pk == event.pk and not failed:
            failed.append(True)
            raise RuntimeError("synthetic batch failure")
        return original_save(self, *args, **kwargs)

    monkeypatch.setattr(Event, "save", fail_once)
    with pytest.raises(RuntimeError):
        _run_forward(apps)
    event.refresh_from_db()
    assert event.session_id is None
    assert Session.objects.count() == 0

    monkeypatch.setattr(Event, "save", original_save)
    _run_forward(apps)
    event.refresh_from_db()
    assert event.session_id is not None
    assert Session.objects.count() == 1


def _checkpoint(apps):
    return apps.get_model(
        "taller", "PublicAnalyticsBackfillCheckpoint"
    ).objects.get(key=backfill.CHECKPOINT_KEY)


@pytest.mark.django_db(transaction=True)
def test_ready_checkpoint_acquires_a_lease(migration_0182_apps):
    apps, _ = migration_0182_apps
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    checkpoint, token = backfill._acquire_lease(Checkpoint)
    checkpoint.refresh_from_db()
    assert checkpoint.status == backfill.CHECKPOINT_RUNNING
    assert checkpoint.owner_token == token
    assert checkpoint.lease_expires_at > timezone.now()


@pytest.mark.django_db(transaction=True)
def test_failed_checkpoint_acquires_a_lease(migration_0182_apps):
    apps, _ = migration_0182_apps
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    Checkpoint.objects.filter(key=backfill.CHECKPOINT_KEY).update(
        status=backfill.CHECKPOINT_FAILED,
        owner_token=None,
        lease_expires_at=None,
    )
    checkpoint, token = backfill._acquire_lease(Checkpoint)
    assert checkpoint.owner_token == token


@pytest.mark.django_db(transaction=True)
def test_live_lease_rejects_second_executor_without_mutating_checkpoint(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, Session, _ = _models(apps)
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    event = _event(Event, session_key="single-owner")
    first, first_token = backfill._acquire_lease(Checkpoint)
    first.refresh_from_db()
    before = (
        first.status,
        first.owner_token,
        first.lease_expires_at,
        first.cutoff_event_pk,
        first.cutoff_pageview_pk,
        first.captured_at,
        first.summary,
    )
    with pytest.raises(backfill.LeaseBusy):
        backfill._acquire_lease(Checkpoint)
    with pytest.raises(backfill.LeaseBusy):
        with connection.schema_editor(atomic=False) as schema_editor:
            backfill.forwards(apps, schema_editor)
    event.refresh_from_db()
    first.refresh_from_db()
    after = (
        first.status,
        first.owner_token,
        first.lease_expires_at,
        first.cutoff_event_pk,
        first.cutoff_pageview_pk,
        first.captured_at,
        first.summary,
    )
    assert event.session_id is None
    assert Session.objects.count() == 0
    assert first_token == first.owner_token
    assert before == after


@pytest.mark.django_db(transaction=True)
def test_migration_executor_rejects_live_lease_without_recording_0184(migration_0182_apps):
    apps, _ = migration_0182_apps
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    _, token = backfill._acquire_lease(Checkpoint)
    executor = MigrationExecutor(connection)
    with pytest.raises(backfill.LeaseBusy):
        executor.migrate([TARGET_0184])
    assert not MigrationRecorder.Migration.objects.filter(
        app="taller", name="0184_backfill_public_analytics_sessions"
    ).exists()
    assert _checkpoint(apps).owner_token == token


@pytest.mark.django_db(transaction=True)
def test_expired_lease_is_recoverable_and_token_changes(migration_0182_apps):
    apps, _ = migration_0182_apps
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    first, first_token = backfill._acquire_lease(Checkpoint)
    Checkpoint.objects.filter(pk=first.pk).update(
        lease_expires_at=timezone.now() - timedelta(seconds=1),
    )
    recovered, recovered_token = backfill._acquire_lease(Checkpoint)
    assert recovered.owner_token == recovered_token
    assert recovered_token != first_token
    assert recovered.lease_expires_at > timezone.now()


@pytest.mark.django_db(transaction=True)
def test_completed_checkpoint_is_permanent_noop_for_acquisition(migration_0182_apps):
    apps, _ = migration_0182_apps
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    Checkpoint.objects.filter(key=backfill.CHECKPOINT_KEY).update(
        status=backfill.CHECKPOINT_COMPLETED,
        owner_token=None,
        lease_expires_at=None,
    )
    checkpoint, token = backfill._acquire_lease(Checkpoint)
    assert checkpoint is None
    assert token
    assert _checkpoint(apps).status == backfill.CHECKPOINT_COMPLETED


@pytest.mark.django_db(transaction=True)
def test_stale_token_cannot_renew_update_fail_or_complete(migration_0182_apps):
    apps, _ = migration_0182_apps
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    _, current_token = backfill._acquire_lease(Checkpoint)
    with pytest.raises(backfill.LeaseLost):
        backfill._renew_lease(Checkpoint, "stale-token")
    with pytest.raises(backfill.LeaseLost):
        backfill._owned_update(Checkpoint, "stale-token", summary={"stale": True})
    with pytest.raises(backfill.LeaseLost):
        backfill._owned_update(
            Checkpoint,
            "stale-token",
            status=backfill.CHECKPOINT_COMPLETED,
            owner_token=None,
            lease_expires_at=None,
        )
    checkpoint = _checkpoint(apps)
    assert checkpoint.owner_token == current_token
    assert checkpoint.status == backfill.CHECKPOINT_RUNNING


@pytest.mark.django_db(transaction=True)
def test_current_owner_can_renew_and_finalize_without_changing_cutoffs(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, _, PageView = _models(apps)
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    event = _event(Event, session_key="lease-fields")
    page = _page(PageView, session_key="lease-fields")
    Checkpoint.objects.filter(key=backfill.CHECKPOINT_KEY).update(
        cutoff_event_pk=event.pk,
        cutoff_pageview_pk=page.pk,
    )
    checkpoint, token = backfill._acquire_lease(Checkpoint)
    original = (checkpoint.cutoff_event_pk, checkpoint.cutoff_pageview_pk, checkpoint.captured_at)
    backfill._renew_lease(Checkpoint, token)
    backfill._owned_update(Checkpoint, token, summary={"owned": True})
    backfill._owned_update(
        Checkpoint,
        token,
        status=backfill.CHECKPOINT_COMPLETED,
        completed_at=timezone.now(),
        owner_token=None,
        lease_expires_at=None,
    )
    checkpoint.refresh_from_db()
    assert (checkpoint.cutoff_event_pk, checkpoint.cutoff_pageview_pk, checkpoint.captured_at) == original
    assert checkpoint.status == backfill.CHECKPOINT_COMPLETED


@pytest.mark.django_db(transaction=True)
def test_failure_clears_only_current_owner_and_allows_resume(migration_0182_apps, monkeypatch):
    apps, _ = migration_0182_apps
    Event, _, _ = _models(apps)
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    _event(Event, session_key="lease-resume")
    original_save = Event.save
    failed = []

    def fail_once(self, *args, **kwargs):
        if self.pk and not failed:
            failed.append(True)
            raise RuntimeError("lease failure")
        return original_save(self, *args, **kwargs)

    monkeypatch.setattr(Event, "save", fail_once)
    with pytest.raises(RuntimeError, match="lease failure"):
        _run_forward(apps)
    checkpoint = _checkpoint(apps)
    assert checkpoint.status == backfill.CHECKPOINT_FAILED
    assert checkpoint.owner_token is None
    assert checkpoint.lease_expires_at is None
    cutoffs = (checkpoint.cutoff_event_pk, checkpoint.cutoff_pageview_pk, checkpoint.captured_at)
    monkeypatch.setattr(Event, "save", original_save)
    _run_forward(apps)
    checkpoint.refresh_from_db()
    assert checkpoint.status == backfill.CHECKPOINT_COMPLETED
    assert (checkpoint.cutoff_event_pk, checkpoint.cutoff_pageview_pk, checkpoint.captured_at) == cutoffs


@pytest.mark.django_db(transaction=True)
def test_lost_lease_between_groups_stops_before_processing_next_group(migration_0182_apps, monkeypatch):
    apps, _ = migration_0182_apps
    Event, Session, _ = _models(apps)
    first = _event(Event, session_key="lease-first")
    second = _event(Event, session_key="lease-second")
    calls = []
    original_renew = backfill._renew_lease

    def lose_after_first(Checkpoint, token):
        calls.append(True)
        if len(calls) == 3:
            Checkpoint.objects.filter(key=backfill.CHECKPOINT_KEY).update(
                owner_token="new-owner",
                lease_expires_at=timezone.now() + timedelta(minutes=15),
            )
        return original_renew(Checkpoint, token)

    monkeypatch.setattr(backfill, "_renew_lease", lose_after_first)
    with pytest.raises(backfill.LeaseLost):
        _run_forward(apps)
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.session_id is not None
    assert second.session_id is None
    assert Session.objects.count() == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="PostgreSQL concurrency test requires a PostgreSQL test database",
)
def test_postgresql_two_acquisitions_have_one_owner(migration_0182_apps):
    apps, _ = migration_0182_apps
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    barrier = threading.Barrier(2)

    def acquire(token):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return backfill._acquire_lease(Checkpoint, token=token)[1]
        except backfill.LeaseBusy:
            return None
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(acquire, ("pg-owner-a", "pg-owner-b")))

    assert sorted(result is not None for result in results) == [False, True]
    assert _checkpoint(apps).owner_token in {"pg-owner-a", "pg-owner-b"}


@pytest.mark.django_db(transaction=True)
def test_checkpoint_captures_once_and_preserves_limits(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, _, PageView = _models(apps)
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    Checkpoint.objects.all().delete()
    event = _event(Event, session_key="captured-once")
    page = _page(PageView, session_key="captured-once")
    with connection.schema_editor() as schema_editor:
        checkpoint_migration.capture_checkpoint(apps, schema_editor)
    saved = Checkpoint.objects.get(key=backfill.CHECKPOINT_KEY)
    snapshot = (saved.cutoff_event_pk, saved.cutoff_pageview_pk, saved.captured_at)

    _event(Event, session_key="after-capture")
    _page(PageView, session_key="after-capture")
    with connection.schema_editor() as schema_editor:
        checkpoint_migration.capture_checkpoint(apps, schema_editor)

    saved.refresh_from_db()
    assert snapshot == (saved.cutoff_event_pk, saved.cutoff_pageview_pk, saved.captured_at)
    assert snapshot[:2] == (event.pk, page.pk)


@pytest.mark.django_db(transaction=True)
def test_empty_tables_capture_null_cutoffs(migration_0182_apps):
    apps, _ = migration_0182_apps
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    Checkpoint.objects.all().delete()
    with connection.schema_editor() as schema_editor:
        checkpoint_migration.capture_checkpoint(apps, schema_editor)
    saved = Checkpoint.objects.get(key=backfill.CHECKPOINT_KEY)
    assert saved.cutoff_event_pk is None
    assert saved.cutoff_pageview_pk is None


@pytest.mark.django_db(transaction=True)
def test_cutoff_excludes_later_events_and_pageviews(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, Session, PageView = _models(apps)
    inside = _event(Event, session_key="inside")
    later = _event(Event, session_key="later")
    inside_page = _page(PageView, session_key="inside")
    later_page = _page(PageView, session_key="later")

    _run_forward(apps, (inside.pk, inside_page.pk))

    inside.refresh_from_db()
    later.refresh_from_db()
    later_page.refresh_from_db()
    assert inside.session_id is not None
    assert later.session_id is None
    assert later.dedupe_key is None
    assert later_page.public_session_id is None
    assert Session.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_cross_cutoff_relations_are_conservative(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, _, PageView = _models(apps)
    inside_event = _event(Event, session_key="event-before-page")
    later_page = _page(PageView, session_key="event-before-page")
    Event.objects.filter(pk=inside_event.pk).update(page_view_id=later_page.pk)

    _run_forward(apps, (inside_event.pk, None))

    inside_event.refresh_from_db()
    later_page.refresh_from_db()
    assert inside_event.session_id is not None
    assert later_page.public_session_id is None


@pytest.mark.django_db(transaction=True)
def test_in_cutoff_page_does_not_import_later_event(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, _, PageView = _models(apps)
    page = _page(PageView, session_key="page-before-event")
    later_event = _event(
        Event,
        session_key="page-before-event",
        page_view=page,
    )

    _run_forward(apps, (None, page.pk))

    page.refresh_from_db()
    later_event.refresh_from_db()
    assert page.public_session_id is None
    assert later_event.session_id is None
    assert later_event.dedupe_key is None


@pytest.mark.django_db(transaction=True)
def test_completed_checkpoint_is_a_stable_noop(migration_0182_apps):
    apps, _ = migration_0182_apps
    Event, _, _ = _models(apps)
    first = _event(Event, session_key="completed")
    _run_forward(apps)
    checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint").objects.get(
        key=backfill.CHECKPOINT_KEY
    )
    assert checkpoint.status == backfill.CHECKPOINT_COMPLETED
    assert checkpoint.summary["events_seen"] == 1
    snapshot = (checkpoint.cutoff_event_pk, checkpoint.cutoff_pageview_pk, checkpoint.captured_at)
    later = _event(Event, session_key="completed-later")
    with connection.schema_editor() as schema_editor:
        backfill.forwards(apps, schema_editor)
    first.refresh_from_db()
    later.refresh_from_db()
    checkpoint.refresh_from_db()
    assert first.session_id is not None
    assert later.session_id is None
    assert snapshot == (checkpoint.cutoff_event_pk, checkpoint.cutoff_pageview_pk, checkpoint.captured_at)


@pytest.mark.django_db(transaction=True)
def test_real_migration_executor_runs_forward_and_reverse(migration_0182_apps):
    _, _ = migration_0182_apps
    executor = MigrationExecutor(connection)
    executor.migrate([TARGET_0182])
    apps_0182 = executor.loader.project_state([TARGET_0182]).apps
    Event, _, PageView = _models(apps_0182)
    page = _page(PageView, session_key="executor-key")
    event = _event(Event, session_key="executor-key", page_view=page)

    executor = MigrationExecutor(connection)
    executor.migrate([TARGET_0183])
    apps_0183 = executor.loader.project_state([TARGET_0183]).apps
    checkpoint = apps_0183.get_model(
        "taller", "PublicAnalyticsBackfillCheckpoint"
    ).objects.get(key=backfill.CHECKPOINT_KEY)
    assert checkpoint.cutoff_event_pk == event.pk
    assert checkpoint.cutoff_pageview_pk == page.pk

    executor = MigrationExecutor(connection)
    executor.migrate([TARGET_0184])
    apps_0184 = executor.loader.project_state([TARGET_0184]).apps
    event_0184 = apps_0184.get_model("taller", "PublicAnalyticsEvent").objects.get(pk=event.pk)
    page_0184 = apps_0184.get_model("taller", "PublicPageView").objects.get(pk=page.pk)
    session_id = event_0184.session_id
    assert session_id is not None
    assert page_0184.public_session_id == session_id
    ledger = event_0184.metadata["_legacy_reconstruction"]
    assert backfill._ledger_digest_is_valid(ledger)
    assert apps_0184.get_model("taller", "PublicAnalyticsSession").objects.get(
        pk=session_id
    ).anonymous_session_hash == backfill._session_hash("key:executor-key")

    executor = MigrationExecutor(connection)
    executor.migrate([TARGET_0183])
    apps_after_reverse = executor.loader.project_state([TARGET_0183]).apps
    restored = apps_after_reverse.get_model("taller", "PublicAnalyticsEvent").objects.get(pk=event.pk)
    assert restored.metadata == {}
    assert restored.session_id is None
    assert restored.dedupe_key is None
    assert restored.occurred_at is None
    assert apps_after_reverse.get_model(
        "taller", "PublicAnalyticsSession"
    ).objects.filter(pk=session_id).exists()
    assert apps_after_reverse.get_model(
        "taller", "PublicAnalyticsBackfillCheckpoint"
    ).objects.filter(key=backfill.CHECKPOINT_KEY).exists()

    executor = MigrationExecutor(connection)
    executor.migrate([TARGET_0182])
    apps_final = executor.loader.project_state([TARGET_0182]).apps
    assert "PublicAnalyticsBackfillCheckpoint" not in {
        model.__name__ for model in apps_final.get_models()
    }
