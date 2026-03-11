# Reglas 4.x: Tres naturalezas de repuesto (stock, compra directa, desarme)
# - tipo_origen: stock | direct | desarme
# - vehiculo_origen: FK opcional para repuestos de desarme
# - origen_costo: compra | desarme | consignacion (reportes financieros)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0082_empresa_is_trial_if_not_exists"),
    ]

    operations = [
        migrations.AddField(
            model_name="repuesto",
            name="tipo_origen",
            field=models.CharField(
                choices=[
                    ("stock", "En stock"),
                    ("direct", "Compra directa"),
                    ("desarme", "Desarme"),
                ],
                db_index=True,
                default="stock",
                help_text="STOCK=inventario, DIRECT=compra directa sin almacenar, DESARME=pieza de vehículo desarmado",
                max_length=20,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="repuesto",
            name="origen_costo",
            field=models.CharField(
                blank=True,
                choices=[
                    ("compra", "Compra"),
                    ("desarme", "Desarme"),
                    ("consignacion", "Consignación"),
                ],
                db_index=True,
                help_text="Compra, desarme o consignación",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="repuesto",
            name="vehiculo_origen",
            field=models.ForeignKey(
                blank=True,
                help_text="Vehículo origen (solo para repuestos de desarme)",
                null=True,
                on_delete=models.SET_NULL,
                related_name="repuestos_desarme",
                to="taller.vehiculo",
            ),
        ),
    ]
