# Generated manually on 2025-08-22

from django.db import migrations, models
from decimal import Decimal

class Migration(migrations.Migration):

    dependencies = [
        ('taller', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='documento',
            name='neto_otros_servicios',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='Neto Otros Servicios'),
        ),
    ]
