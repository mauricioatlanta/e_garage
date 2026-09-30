import hashlib
from pathlib import Path

from django.db import migrations
from django.db.migrations.loader import MigrationLoader

from taller.models.public_analytics_event import PublicAnalyticsEvent


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


def _migration(name):
    loader = MigrationLoader(None, ignore_no_migrations=True)
    return loader.disk_migrations[("taller", name)]


def _operation_types(migration):
    return {type(operation) for operation in migration.operations}


def test_transitional_graph_has_one_production_0180_and_linear_dependencies():
    names = sorted(path.name for path in MIGRATIONS_DIR.glob("0180_*.py"))
    assert names == ["0180_public_analytics_events.py"]
    assert _migration("0181_public_analytics_session_links").dependencies == [
        ("taller", "0180_public_analytics_events")
    ]
    assert _migration("0182_public_analytics_event_transition_fields").dependencies == [
        ("taller", "0181_public_analytics_session_links")
    ]


def test_0180_is_the_production_file():
    expected_sha256 = "73ce364ef60ed5032d425d6f452f60397f55eec8372f17c04ba7d64c3f3a2934"
    migration_path = MIGRATIONS_DIR / "0180_public_analytics_events.py"
    assert hashlib.sha256(migration_path.read_bytes()).hexdigest() == expected_sha256

    migration = _migration("0180_public_analytics_events")
    operation_names = [type(operation).__name__ for operation in migration.operations]
    assert migration.dependencies == [("taller", "0179_grandfather_existing_empresas_onboarding")]
    assert "CreateModel" in operation_names
    assert [
        operation.name
        for operation in migration.operations
        if isinstance(operation, migrations.CreateModel)
    ] == ["PublicAnalyticsEvent"]
    assert not any(
        isinstance(operation, migrations.CreateModel)
        and operation.name == "PublicAnalyticsSession"
        for operation in migration.operations
    )
    event_fields = next(
        operation.fields
        for operation in migration.operations
        if isinstance(operation, migrations.CreateModel)
        and operation.name == "PublicAnalyticsEvent"
    )
    assert {name for name, _ in event_fields} >= {"session_key", "empresa", "page_view"}


def test_0181_contains_only_session_and_nullable_link_operations():
    migration = _migration("0181_public_analytics_session_links")
    assert migrations.RunPython not in _operation_types(migration)
    assert migrations.RemoveField not in _operation_types(migration)
    assert migrations.DeleteModel not in _operation_types(migration)
    assert [operation.name for operation in migration.operations if isinstance(operation, migrations.CreateModel)] == [
        "PublicAnalyticsSession"
    ]
    add_fields = {
        (operation.model_name, operation.name)
        for operation in migration.operations
        if isinstance(operation, migrations.AddField)
    }
    assert add_fields == {
        ("publicpageview", "public_session"),
        ("registroembudosuscriptor", "public_session"),
    }


def test_no_migration_after_production_0180_recreates_public_analytics_event():
    loader = MigrationLoader(None, ignore_no_migrations=True)
    for (app_label, name), migration in loader.disk_migrations.items():
        if app_label != "taller" or name <= "0180_public_analytics_events":
            continue
        assert not any(
            isinstance(operation, migrations.CreateModel)
            and operation.name == "PublicAnalyticsEvent"
            for operation in migration.operations
        )


def test_0182_is_additive_and_does_not_recreate_events():
    migration = _migration("0182_public_analytics_event_transition_fields")
    assert migrations.RunPython not in _operation_types(migration)
    assert migrations.RemoveField not in _operation_types(migration)
    assert migrations.DeleteModel not in _operation_types(migration)
    assert migrations.CreateModel not in _operation_types(migration)
    assert {
        operation.name
        for operation in migration.operations
        if isinstance(operation, migrations.AddField)
    } == {"session", "dedupe_key", "occurred_at"}


def test_0183_creates_checkpoint_and_captures_once():
    migration = _migration("0183_public_analytics_backfill_checkpoint")
    assert migration.dependencies == [
        ("taller", "0182_public_analytics_event_transition_fields")
    ]
    assert any(isinstance(operation, migrations.CreateModel) and operation.name == "PublicAnalyticsBackfillCheckpoint" for operation in migration.operations)
    assert any(isinstance(operation, migrations.RunPython) for operation in migration.operations)
    fields = next(
        operation.fields
        for operation in migration.operations
        if isinstance(operation, migrations.CreateModel)
        and operation.name == "PublicAnalyticsBackfillCheckpoint"
    )
    assert {name for name, _ in fields} >= {
        "key",
        "cutoff_event_pk",
        "cutoff_pageview_pk",
        "captured_at",
        "status",
        "owner_token",
        "lease_expires_at",
        "completed_at",
        "summary",
    }


def test_0184_is_runpython_only_and_depends_on_checkpoint():
    migration = _migration("0184_backfill_public_analytics_sessions")
    assert migration.atomic is False
    assert migration.dependencies == [("taller", "0183_public_analytics_backfill_checkpoint")]
    assert len(migration.operations) == 1
    assert isinstance(migration.operations[0], migrations.RunPython)


def test_0186_hardens_public_analytics_without_recreating_models():
    migration = _migration("0186_public_analytics_hardening")
    operation_names = [type(operation).__name__ for operation in migration.operations]

    assert "CreateModel" not in operation_names
    assert "DeleteModel" not in operation_names
    assert any(isinstance(operation, migrations.RunPython) for operation in migration.operations)
    assert any(isinstance(operation, migrations.AddConstraint) for operation in migration.operations)
    assert {
        operation.name
        for operation in migration.operations
        if isinstance(operation, migrations.AlterField)
    } == {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}


def test_transition_model_keeps_nullable_fields_and_legacy_columns():
    assert PublicAnalyticsEvent._meta.get_field("session").null is True
    assert PublicAnalyticsEvent._meta.get_field("dedupe_key").null is True
    assert PublicAnalyticsEvent._meta.get_field("occurred_at").null is True
    for name in (
        "page_view",
        "empresa",
        "created_at",
        "session_key",
        "visitor_hash",
        "country",
        "language",
        "rubro",
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_content",
        "utm_term",
        "landing_initial",
        "referrer",
        "source_label",
        "is_mobile",
        "is_bot",
        "is_internal",
        "is_staff",
        "is_server",
        "value",
        "currency",
        "metadata",
    ):
        assert PublicAnalyticsEvent._meta.get_field(name)


def test_navigation_template_has_no_analytics_reconciliation_content():
    template = (Path(__file__).resolve().parents[2] / "templates" / "base.html").read_text()
    assert "0180_public_analytics_events" not in template
    assert "/analytics/public/event/" not in template
