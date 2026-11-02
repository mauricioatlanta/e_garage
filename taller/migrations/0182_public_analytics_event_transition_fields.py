from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0181_public_analytics_session_links"),
    ]

    operations = [
        migrations.AddField(
            model_name="publicanalyticsevent",
            name="session",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="events", to="taller.publicanalyticssession"),
        ),
        migrations.AddField(
            model_name="publicanalyticsevent",
            name="dedupe_key",
            field=models.CharField(blank=True, db_index=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name="publicanalyticsevent",
            name="occurred_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddIndex(
            model_name="publicanalyticsevent",
            index=models.Index(fields=["event_type", "occurred_at"], name="taller_publ_event_occur_idx"),
        ),
        migrations.AddIndex(
            model_name="publicanalyticsevent",
            index=models.Index(fields=["path", "occurred_at"], name="taller_publ_path_occur_idx"),
        ),
        migrations.AddIndex(
            model_name="publicanalyticsevent",
            index=models.Index(fields=["session", "event_type"], name="taller_publ_session_event_idx"),
        ),
    ]
