# Merge migration: unifica hojas 0075_registroembudosuscriptor_and_more y 0077_configuracionempresa_sales_tax_rate

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0075_registroembudosuscriptor_and_more"),
        ("taller", "0077_configuracionempresa_sales_tax_rate"),
    ]

    operations = []
