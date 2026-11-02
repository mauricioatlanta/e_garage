# Generated for Fase 3 — tabla SugerenciaPiezaDesarme
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0137_vehiculo_tipo_carroceria_choices"),
    ]

    operations = [
        migrations.CreateModel(
            name="SugerenciaPiezaDesarme",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                (
                    "empresa",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="taller.empresa",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "vehiculo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sugerencias_piezas",
                        to="taller.vehiculo",
                    ),
                ),
                ("codigo", models.CharField(max_length=100)),
                ("nombre", models.CharField(max_length=255)),
                ("zona", models.CharField(blank=True, default="", max_length=50)),
                (
                    "precio_sugerido",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=12, null=True
                    ),
                ),
                (
                    "condicion_sugerida",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("NUEVO", "Nuevo"),
                            ("EXCELENTE", "Excelente"),
                            ("BUENA", "Buena"),
                            ("REGULAR", "Regular"),
                        ],
                        max_length=10,
                        null=True,
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("PENDIENTE", "Pendiente"),
                            ("CONFIRMADA", "Confirmada"),
                            ("DESCARTADA", "Descartada"),
                        ],
                        db_index=True,
                        default="PENDIENTE",
                        max_length=12,
                    ),
                ),
                (
                    "pieza_creada",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sugerencia_origen",
                        to="taller.piezadesarme",
                    ),
                ),
            ],
            options={
                "verbose_name": "Sugerencia pieza desarme",
                "verbose_name_plural": "Sugerencias piezas desarme",
            },
        ),
        migrations.AddConstraint(
            model_name="sugerenciapiezadesarme",
            constraint=models.UniqueConstraint(
                fields=["vehiculo", "codigo"],
                name="unique_sugerencia_por_vehiculo",
            ),
        ),
        migrations.AddIndex(
            model_name="sugerenciapiezadesarme",
            index=models.Index(
                fields=["empresa", "vehiculo"], name="sug_pieza_emp_veh_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="sugerenciapiezadesarme",
            index=models.Index(
                fields=["empresa", "vehiculo", "estado"],
                name="sug_pieza_emp_veh_est_idx",
            ),
        ),
    ]
