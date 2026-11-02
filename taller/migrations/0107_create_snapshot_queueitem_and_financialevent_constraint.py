from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0106_alter_vehiculodesarme_estado_desarme_and_more"),
    ]

    operations = [

        migrations.CreateModel(
            name="SnapshotQueueItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "scheduled_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        db_index=True,
                    ),
                ),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("attempts", models.IntegerField(default=0)),
                ("last_error", models.TextField(blank=True, null=True)),
                (
                    "documento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="snapshot_queue_items",
                        to="taller.documento",
                    ),
                ),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="snapshot_queue",
                        to="taller.empresa",
                    ),
                ),
            ],
            options={
                "verbose_name": "Snapshot Queue Item",
                "verbose_name_plural": "Snapshot Queue Items",
                "indexes": [
                    models.Index(
                        fields=["documento", "scheduled_at"],
                        name="taller_snap_documen_c725a6_idx",
                    ),
                ],
            },
        ),

        migrations.AddField(
            model_name="vehiclefinancialevent",
            name="linea_repuesto",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="financial_events",
                to="taller.linearepuesto",
                help_text="Referencia a la línea de repuesto (identidad del evento)",
            ),
        ),

        migrations.AddField(
            model_name="vehiclefinancialevent",
            name="event_hash",
            field=models.CharField(
                max_length=128,
                null=True,
                blank=True,
                db_index=True,
            ),
        ),

        migrations.AddField(
            model_name="vehiclefinancialevent",
            name="event_version",
            field=models.IntegerField(default=1),
        ),

        migrations.AddField(
            model_name="vehiclefinancialevent",
            name="event_type",
            field=models.CharField(
                max_length=30,
                default="UNKNOWN",
                db_index=True,
                choices=[
                    ("COMPRA", "Compra"),
                    ("COSTO", "Costo"),
                    ("VENTA", "Venta"),
                    ("AJUSTE", "Ajuste"),
                    ("OTRO", "Otro"),
                    ("UNKNOWN", "Unknown"),
                ],
            ),
        ),

        migrations.AddIndex(
            model_name="vehiclefinancialevent",
            index=models.Index(
                fields=["linea_repuesto"],
                name="taller_vehi_linea_r_bbc7a0_idx",
            ),
        ),

        migrations.AddIndex(
            model_name="vehiclefinancialevent",
            index=models.Index(
                fields=["event_hash"],
                name="taller_vehi_event_h_ad6832_idx",
            ),
        ),

        migrations.AddIndex(
            model_name="vehiclefinancialevent",
            index=models.Index(
                fields=["event_type"],
                name="taller_vehi_event_t_198e1e_idx",
            ),
        ),

        migrations.AddConstraint(
            model_name="vehiclefinancialevent",
            constraint=models.UniqueConstraint(
                fields=("event_hash",),
                name="unique_vehicle_financial_event_hash",
            ),
        ),
    ]
