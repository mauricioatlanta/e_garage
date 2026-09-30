from django.db import migrations, models
from django.utils import timezone


CHECKPOINT_KEY = "public_analytics_legacy_v1"
STATUS_READY = "READY"


def capture_checkpoint(apps, schema_editor):
    Event = apps.get_model("taller", "PublicAnalyticsEvent")
    PageView = apps.get_model("taller", "PublicPageView")
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")

    cutoff_event_pk = Event.objects.order_by("-pk").values_list("pk", flat=True).first()
    cutoff_pageview_pk = PageView.objects.order_by("-pk").values_list("pk", flat=True).first()
    Checkpoint.objects.get_or_create(
        key=CHECKPOINT_KEY,
        defaults={
            "cutoff_event_pk": cutoff_event_pk,
            "cutoff_pageview_pk": cutoff_pageview_pk,
            "captured_at": timezone.now(),
            "status": STATUS_READY,
        },
    )


def ensure_checkpoint_ready(apps, schema_editor):
    Checkpoint = apps.get_model("taller", "PublicAnalyticsBackfillCheckpoint")
    checkpoint = Checkpoint.objects.filter(key=CHECKPOINT_KEY).first()
    if checkpoint is not None and checkpoint.status != STATUS_READY:
        raise RuntimeError(
            "0183 checkpoint can only be reversed after 0184 has been reversed"
        )


class Migration(migrations.Migration):
    dependencies = [
        ("taller", "0182_public_analytics_event_transition_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="PublicAnalyticsBackfillCheckpoint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=80, unique=True)),
                ("cutoff_event_pk", models.BigIntegerField(blank=True, null=True)),
                ("cutoff_pageview_pk", models.BigIntegerField(blank=True, null=True)),
                ("captured_at", models.DateTimeField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("READY", "Ready"),
                            ("RUNNING", "Running"),
                            ("COMPLETED", "Completed"),
                            ("FAILED", "Failed"),
                        ],
                        max_length=20,
                    ),
                ),
                ("owner_token", models.CharField(blank=True, max_length=64, null=True)),
                ("lease_expires_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("summary", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Public analytics backfill checkpoint",
                "verbose_name_plural": "Public analytics backfill checkpoints",
            },
        ),
        migrations.RunPython(capture_checkpoint, ensure_checkpoint_ready),
    ]
