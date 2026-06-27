import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Convierte vehiculo_desarme de nullable → NOT NULL y reemplaza todos los
    constraints e índices que referenciaban la columna vehiculo vieja.

    Nombres de índice auto-generados verificados contra makemigrations --dry-run:
      taller_piez_empresa_864ad2_idx  → (empresa, vehiculo)      en piezadesarme
      taller_vehi_vehicul_211445_idx  → (vehiculo, tipo, fecha)   en vehiclefinancialevent
      taller_vehi_vehicul_10a0fd_idx  → (vehiculo, fecha)         en vehiculofinancialsnapshot
      taller_vehi_vehicul_d07196_idx  → (vehiculo, source_event_count) en vehiculofinancialsnapshot
    """

    dependencies = [
        ("taller", "0143_fase2_poblar_vehiculo_desarme"),
    ]

    operations = [
        # ── PiezaDesarme ──────────────────────────────────────────────────
        migrations.RemoveConstraint(
            model_name="piezadesarme",
            name="unique_codigo_por_empresa_vehiculo",
        ),
        # DROP INDEX IF EXISTS: el índice fue creado por 0075 pero nunca se
        # ejecutó realmente en producción (mismo descuadre que 0077/0078).
        # SeparateDatabaseAndState mantiene el estado de Django sincronizado
        # mientras el database_operation tolera la ausencia del índice.
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="DROP INDEX IF EXISTS taller_piez_empresa_864ad2_idx;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.RemoveIndex(
                    model_name="piezadesarme",
                    name="taller_piez_empresa_864ad2_idx",
                ),
            ],
        ),
        migrations.AlterField(
            model_name="piezadesarme",
            name="vehiculo_desarme",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="piezas_desarme",
                to="taller.vehiculodesarme",
            ),
        ),
        migrations.AddConstraint(
            model_name="piezadesarme",
            constraint=models.UniqueConstraint(
                fields=["empresa", "vehiculo_desarme", "codigo"],
                name="unique_codigo_por_empresa_vehiculo_desarme",
            ),
        ),
        migrations.AddIndex(
            model_name="piezadesarme",
            index=models.Index(fields=["empresa", "vehiculo_desarme"], name="taller_piez_empresa_0d4562_idx"),
        ),

        # ── SugerenciaPiezaDesarme ────────────────────────────────────────
        migrations.RemoveConstraint(
            model_name="sugerenciapiezadesarme",
            name="unique_sugerencia_por_vehiculo",
        ),
        migrations.RemoveIndex(
            model_name="sugerenciapiezadesarme",
            name="sug_pieza_emp_veh_idx",
        ),
        migrations.RemoveIndex(
            model_name="sugerenciapiezadesarme",
            name="sug_pieza_emp_veh_est_idx",
        ),
        migrations.AlterField(
            model_name="sugerenciapiezadesarme",
            name="vehiculo_desarme",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sugerencias_piezas",
                to="taller.vehiculodesarme",
            ),
        ),
        migrations.AddConstraint(
            model_name="sugerenciapiezadesarme",
            constraint=models.UniqueConstraint(
                fields=["vehiculo_desarme", "codigo"],
                name="unique_sugerencia_por_vehiculo_desarme",
            ),
        ),
        migrations.AddIndex(
            model_name="sugerenciapiezadesarme",
            index=models.Index(
                fields=["empresa", "vehiculo_desarme"],
                name="sug_pieza_emp_veh_d_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="sugerenciapiezadesarme",
            index=models.Index(
                fields=["empresa", "vehiculo_desarme", "estado"],
                name="sug_pieza_emp_veh_d_est_idx",
            ),
        ),

        # ── PrecioHistoricoPieza ──────────────────────────────────────────
        # Sin constraints ni índices nombrados sobre vehiculo — solo AlterField.
        migrations.AlterField(
            model_name="preciohistoricopieza",
            name="vehiculo_desarme",
            field=models.ForeignKey(
                help_text="Vehículo de origen (contexto del precio).",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="precios_historicos_pieza",
                to="taller.vehiculodesarme",
            ),
        ),

        # ── VehiculoFinancialSnapshot ─────────────────────────────────────
        migrations.RemoveIndex(
            model_name="vehiculofinancialsnapshot",
            name="taller_vehi_vehicul_10a0fd_idx",
        ),
        migrations.RemoveIndex(
            model_name="vehiculofinancialsnapshot",
            name="taller_vehi_vehicul_d07196_idx",
        ),
        migrations.AlterField(
            model_name="vehiculofinancialsnapshot",
            name="vehiculo_desarme",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="financial_snapshots",
                to="taller.vehiculodesarme",
            ),
        ),
        migrations.AddIndex(
            model_name="vehiculofinancialsnapshot",
            index=models.Index(fields=["vehiculo_desarme", "fecha"], name="taller_vehi_vehicul_ac46db_idx"),
        ),
        migrations.AddIndex(
            model_name="vehiculofinancialsnapshot",
            index=models.Index(fields=["vehiculo_desarme", "source_event_count"], name="taller_vehi_vehicul_13b81d_idx"),
        ),

        # ── VehicleFinancialEvent ─────────────────────────────────────────
        migrations.RemoveIndex(
            model_name="vehiclefinancialevent",
            name="taller_vehi_vehicul_211445_idx",
        ),
        migrations.AlterField(
            model_name="vehiclefinancialevent",
            name="vehiculo_desarme",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="financial_events",
                to="taller.vehiculodesarme",
            ),
        ),
        migrations.AddIndex(
            model_name="vehiclefinancialevent",
            index=models.Index(fields=["vehiculo_desarme", "tipo", "fecha"], name="taller_vehi_vehicul_a36d4a_idx"),
        ),
    ]
