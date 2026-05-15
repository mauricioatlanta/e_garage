from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0100_align_linearepuesto_desarme_columns"),
    ]

    operations = [
        migrations.AddField(
            model_name="repuesto",
            name="stock_minimo",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Stock minimo recomendado para reabastecimiento",
                null=True,
            ),
        ),
    ]
