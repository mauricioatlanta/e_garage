"""
P2-DB Migración A — Esquema.

Cambios:
1. VehiculoDesarme.estado_operativo — campo operacional del Centro de Operaciones.
   Coexiste con estado_desarme (legacy) hasta futura consolidación.
2. VehiculoDesarmeEvent — registro append-only de eventos operacionales.
3. Índices y constraints de integridad.

El backfill de estado_operativo va en la migración 0163.
"""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0161_piezadesarme_publicada"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── 1. Campo estado_operativo en VehiculoDesarme ─────────────────────
        migrations.AddField(
            model_name="vehiculodesarme",
            name="estado_operativo",
            field=models.CharField(
                choices=[
                    ("INGRESADO",        "Ingresado"),
                    ("EN_REVISION",      "En revisión"),
                    ("EN_PROCESAMIENTO", "En procesamiento"),
                    ("EN_CIERRE",        "En cierre"),
                    ("CERRADO",          "Cerrado"),
                ],
                default="INGRESADO",
                db_index=True,
                max_length=24,
                help_text=(
                    "Estado operacional del ciclo de vida del vehículo. "
                    "Independiente del campo legacy estado_desarme. "
                    "Alimenta el Centro de Operaciones."
                ),
            ),
        ),
        migrations.AddIndex(
            model_name="vehiculodesarme",
            index=models.Index(
                fields=["empresa", "estado_operativo"],
                name="taller_veh_des_emp_est_op_idx",
            ),
        ),
        # ── 2. Modelo VehiculoDesarmeEvent ────────────────────────────────────
        migrations.CreateModel(
            name="VehiculoDesarmeEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "empresa",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="taller.empresa",
                    ),
                ),
                (
                    "vehiculo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="eventos_operacionales",
                        to="taller.vehiculodesarme",
                    ),
                ),
                (
                    "pieza",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="eventos_operacionales",
                        to="taller.piezadesarme",
                    ),
                ),
                (
                    "documento",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="eventos_desarme",
                        to="taller.documento",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="eventos_desarme_creados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("VEHICULO_CREADO",           "Vehículo creado"),
                            ("ESTADO_OPERATIVO_CAMBIADO", "Estado operativo cambiado"),
                            ("REVISION_INICIADA",         "Revisión iniciada"),
                            ("REVISION_FINALIZADA",       "Revisión finalizada"),
                            ("PIEZA_CONFIRMADA",          "Pieza confirmada"),
                            ("PIEZA_DESCARTADA",          "Pieza descartada"),
                            ("PIEZA_DESMONTADA",          "Pieza desmontada"),
                            ("PIEZA_ALMACENADA",          "Pieza almacenada"),
                            ("PIEZA_PUBLICADA",           "Pieza publicada"),
                            ("PIEZA_DESPUBLICADA",        "Pieza despublicada"),
                            ("PIEZA_RESERVADA",           "Pieza reservada"),
                            ("PIEZA_VENDIDA",             "Pieza vendida"),
                            ("VENTA_ANULADA",             "Venta anulada"),
                            ("COSTO_REGISTRADO",          "Costo registrado"),
                            ("CIERRE_INICIADO",           "Cierre iniciado"),
                            ("VEHICULO_CERRADO",          "Vehículo cerrado"),
                            ("MIGRACION_ESTADO_INICIAL",  "Migración — estado inicial inferido"),
                        ],
                        db_index=True,
                        max_length=40,
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text='Contexto adicional. Ej: {"from": "INGRESADO", "to": "EN_REVISION"}',
                    ),
                ),
                (
                    "idempotency_key",
                    models.CharField(
                        blank=True,
                        max_length=160,
                        null=True,
                        help_text="Clave única por tenant para evitar duplicados.",
                    ),
                ),
                (
                    "occurred_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        help_text="Momento en que ocurrió el hecho de negocio.",
                    ),
                ),
            ],
            options={
                "verbose_name": "Evento operacional de desarme",
                "verbose_name_plural": "Eventos operacionales de desarme",
                "ordering": ["occurred_at"],
            },
        ),
        # ── 3. Índices del modelo de eventos ─────────────────────────────────
        migrations.AddIndex(
            model_name="vehiculodesarmeevent",
            index=models.Index(
                fields=["empresa", "vehiculo", "occurred_at"],
                name="desarme_ev_emp_veh_occ_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="vehiculodesarmeevent",
            index=models.Index(
                fields=["empresa", "tipo", "occurred_at"],
                name="desarme_ev_emp_tipo_occ_idx",
            ),
        ),
        # ── 4. Constraint de idempotencia (partial unique) ───────────────────
        migrations.AddConstraint(
            model_name="vehiculodesarmeevent",
            constraint=models.UniqueConstraint(
                condition=Q(idempotency_key__isnull=False),
                fields=["empresa", "idempotency_key"],
                name="uniq_desarme_event_idempotency_tenant",
            ),
        ),
    ]
