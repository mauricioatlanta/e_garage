# Fase A: Crear modelo VehiculoDesarme (sin tocar Vehiculo ni PiezaDesarme)

import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0076_empresa_is_trial_restore"),
    ]

    operations = [
        migrations.CreateModel(
            name="VehiculoDesarme",
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
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "vehiculo_origen_id",
                    models.IntegerField(
                        blank=True,
                        db_index=True,
                        help_text="ID del Vehiculo origen (solo para migración; null en registros nuevos).",
                        null=True,
                    ),
                ),
                (
                    "marca_texto",
                    models.CharField(
                        blank=True,
                        help_text="Marca como texto (USA catálogo global).",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "modelo_texto",
                    models.CharField(
                        blank=True,
                        help_text="Modelo como texto (USA catálogo global).",
                        max_length=150,
                        null=True,
                    ),
                ),
                (
                    "patente",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        default="",
                        help_text="Patente o placa; vacío si solo VIN.",
                        max_length=20,
                    ),
                ),
                (
                    "anio",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="No inventar valores; copiar tal cual del origen.",
                        null=True,
                        verbose_name="Año",
                    ),
                ),
                ("vin", models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                (
                    "millas",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Millas/Kilometraje",
                    ),
                ),
                (
                    "costo_adquisicion",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=12,
                        null=True,
                    ),
                ),
                (
                    "fecha_ingreso_desarme",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "estado_desarme",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("INGRESADO", "Ingresado"),
                            ("DESARMANDO", "Desarmando"),
                            ("DESARMADO", "Desarmado"),
                            ("BAJA", "Baja"),
                        ],
                        max_length=20,
                        null=True,
                    ),
                ),
                (
                    "ubicacion_fisica",
                    models.CharField(
                        blank=True,
                        help_text="Ubicación en la yarda (ej: fila 3, posición 12).",
                        max_length=120,
                        null=True,
                    ),
                ),
                (
                    "fecha_baja_desarme",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "observaciones_desarme",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "caja",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="taller.cajavehiculo",
                    ),
                ),
                (
                    "color",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="taller.colorvehiculo",
                    ),
                ),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="taller.empresa",
                    ),
                ),
                (
                    "marca",
                    models.ForeignKey(
                        blank=True,
                        help_text="Marca del vehículo (Chile: FK; USA: usar marca_texto).",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="taller.marca",
                    ),
                ),
                (
                    "modelo",
                    models.ForeignKey(
                        blank=True,
                        help_text="Modelo del vehículo (Chile: FK; USA: usar modelo_texto).",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="taller.modelo",
                    ),
                ),
                (
                    "motor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="taller.motorvehiculo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Vehículo de desarme",
                "verbose_name_plural": "Vehículos de desarme",
                "ordering": ["-fecha_ingreso_desarme", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="vehiculodesarme",
            index=models.Index(fields=["empresa"], name="taller_vd_empresa_idx"),
        ),
        migrations.AddIndex(
            model_name="vehiculodesarme",
            index=models.Index(
                fields=["empresa", "estado_desarme"],
                name="taller_vd_emp_est_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="vehiculodesarme",
            index=models.Index(
                fields=["vehiculo_origen_id"],
                name="taller_vd_orig_idx",
            ),
        ),
    ]
