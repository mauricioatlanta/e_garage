import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0141_migrar_vehiculos_desarme_a_vehiculodesarme"),
    ]

    operations = [
        migrations.AddField(
            model_name="piezadesarme",
            name="vehiculo_desarme",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="piezas_desarme",
                to="taller.vehiculodesarme",
            ),
        ),
        migrations.AddField(
            model_name="sugerenciapiezadesarme",
            name="vehiculo_desarme",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sugerencias_piezas",
                to="taller.vehiculodesarme",
            ),
        ),
        migrations.AddField(
            model_name="preciohistoricopieza",
            name="vehiculo_desarme",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="precios_historicos_pieza",
                to="taller.vehiculodesarme",
            ),
        ),
        migrations.AddField(
            model_name="vehiculofinancialsnapshot",
            name="vehiculo_desarme",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="financial_snapshots",
                to="taller.vehiculodesarme",
            ),
        ),
        migrations.AddField(
            model_name="vehiclefinancialevent",
            name="vehiculo_desarme",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="financial_events",
                to="taller.vehiculodesarme",
            ),
        ),
    ]
