# Une las ramas 0091 (regiones Chile) y 0092 (unique teléfono empresa).
# Sin esto, 0091 y 0092 comparten padre 0090 y Django vería dos leaf nodes.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0091_load_regiones_chile_if_empty"),
        ("taller", "0092_empresa_telefono_unique_partial"),
    ]

    operations = []
