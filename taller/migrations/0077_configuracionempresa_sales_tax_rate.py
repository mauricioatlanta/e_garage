# Generated manually for USA sales tax

from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0075_add_documento_context_and_sequence_serie"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracionempresa",
            name="sales_tax_rate",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                help_text="Porcentaje de sales tax para documentos USA (ej: 7.00). Editable en Ajustes.",
                max_digits=5,
                verbose_name="Sales tax % (USA)",
            ),
        ),
    ]
