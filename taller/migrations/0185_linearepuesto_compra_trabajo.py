from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0184_backfill_public_analytics_sessions"),
    ]

    operations = [
        migrations.AddField(
            model_name="linearepuesto",
            name="proveedor_compra",
            field=models.CharField(
                blank=True,
                help_text="Proveedor informado para una compra asociada a esta linea del documento.",
                max_length=200,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="linearepuesto",
            name="origen_repuesto",
            field=models.CharField(
                choices=[
                    ("EXTERNO", "Externo"),
                    ("STOCK_BODEGA", "Stock bodega"),
                    ("COMPRA_TRABAJO", "Compra para este trabajo"),
                    ("DESARME", "Desarme"),
                ],
                db_index=True,
                default="STOCK_BODEGA",
                max_length=20,
            ),
        ),
    ]
