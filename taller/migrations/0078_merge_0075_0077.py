# Merge migration: unifica hojas 0075_registroembudosuscriptor_and_more y 0077_configuracionempresa_sales_tax_rate

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0076_add_linearepuesto_source_type"),
        ("taller", "0077_configuracionempresa_sales_tax_rate"),
    ]

    operations = []
