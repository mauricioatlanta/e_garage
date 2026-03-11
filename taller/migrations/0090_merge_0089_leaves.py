# Merge de las dos hojas 0089 para dejar un único leaf y poder aplicar migraciones.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0089_catalogo_anio_desde_hasta"),
        ("taller", "0089_merge_20260311_0002"),
    ]

    operations = []
