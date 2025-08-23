# Generated manually on 2025-08-22

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('taller', '0002_add_neto_otros_servicios'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehiculo',
            name='millas',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Millas/Kilometraje'),
        ),
    ]
