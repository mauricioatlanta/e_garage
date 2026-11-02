from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0179_grandfather_existing_empresas_onboarding"),
    ]

    operations = [
        migrations.AddField(
            model_name="publicpageview",
            name="session_key",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AddField(
            model_name="publicpageview",
            name="is_internal",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="publicpageview",
            name="is_staff",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="publicpageview",
            name="is_server",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="publicpageview",
            name="utm_source",
            field=models.CharField(blank=True, db_index=True, max_length=120),
        ),
        migrations.AddField(
            model_name="publicpageview",
            name="utm_medium",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="publicpageview",
            name="utm_campaign",
            field=models.CharField(blank=True, db_index=True, max_length=160),
        ),
        migrations.AddField(
            model_name="publicpageview",
            name="utm_content",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="publicpageview",
            name="utm_term",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="publicpageview",
            name="landing_initial",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="publicpageview",
            name="source_label",
            field=models.CharField(blank=True, db_index=True, max_length=120),
        ),
        migrations.CreateModel(
            name="PublicAnalyticsEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("landing_view", "Landing vista"),
                            ("cta_click", "CTA presionado"),
                            ("signup_start", "Registro iniciado"),
                            ("signup_complete", "Registro completado"),
                            ("onboarding_complete", "Onboarding completado"),
                            ("subscription_paid", "Suscripción pagada"),
                        ],
                        db_index=True,
                        max_length=40,
                    ),
                ),
                ("path", models.CharField(blank=True, db_index=True, max_length=255)),
                ("session_key", models.CharField(blank=True, db_index=True, max_length=64)),
                ("visitor_hash", models.CharField(blank=True, db_index=True, max_length=64)),
                ("country", models.CharField(blank=True, db_index=True, max_length=8)),
                ("language", models.CharField(blank=True, db_index=True, max_length=8)),
                ("rubro", models.CharField(blank=True, db_index=True, max_length=40)),
                ("utm_source", models.CharField(blank=True, db_index=True, max_length=120)),
                ("utm_medium", models.CharField(blank=True, max_length=120)),
                ("utm_campaign", models.CharField(blank=True, db_index=True, max_length=160)),
                ("utm_content", models.CharField(blank=True, max_length=160)),
                ("utm_term", models.CharField(blank=True, max_length=160)),
                ("landing_initial", models.CharField(blank=True, max_length=255)),
                ("referrer", models.CharField(blank=True, max_length=500)),
                ("source_label", models.CharField(blank=True, db_index=True, max_length=120)),
                ("is_mobile", models.BooleanField(db_index=True, default=False)),
                ("is_bot", models.BooleanField(db_index=True, default=False)),
                ("is_internal", models.BooleanField(db_index=True, default=False)),
                ("is_staff", models.BooleanField(db_index=True, default=False)),
                ("is_server", models.BooleanField(db_index=True, default=False)),
                ("value", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("currency", models.CharField(blank=True, max_length=3)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                (
                    "empresa",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="public_analytics_events",
                        to="taller.empresa",
                    ),
                ),
                (
                    "page_view",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="events",
                        to="taller.publicpageview",
                    ),
                ),
            ],
            options={
                "verbose_name": "Evento de adquisición pública",
                "verbose_name_plural": "Eventos de adquisición pública",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="publicanalyticsevent",
            index=models.Index(fields=["event_type", "created_at"], name="taller_publ_event_t_5b7fb7_idx"),
        ),
        migrations.AddIndex(
            model_name="publicanalyticsevent",
            index=models.Index(fields=["session_key", "created_at"], name="taller_publ_session_b4b74f_idx"),
        ),
        migrations.AddIndex(
            model_name="publicanalyticsevent",
            index=models.Index(fields=["utm_campaign", "created_at"], name="taller_publ_utm_cam_9430d0_idx"),
        ),
        migrations.AddIndex(
            model_name="publicanalyticsevent",
            index=models.Index(fields=["source_label", "created_at"], name="taller_publ_source__22ca5a_idx"),
        ),
        migrations.AddIndex(
            model_name="publicanalyticsevent",
            index=models.Index(fields=["is_internal", "created_at"], name="taller_publ_is_inte_4f0ef3_idx"),
        ),
        migrations.AddIndex(
            model_name="publicpageview",
            index=models.Index(fields=["is_internal", "created_at"], name="taller_publ_is_inte_19267f_idx"),
        ),
        migrations.AddIndex(
            model_name="publicpageview",
            index=models.Index(fields=["utm_campaign", "created_at"], name="taller_publ_utm_cam_fa31ef_idx"),
        ),
        migrations.AddIndex(
            model_name="publicpageview",
            index=models.Index(fields=["source_label", "created_at"], name="taller_publ_source__3db700_idx"),
        ),
    ]
