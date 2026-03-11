# Merge migration (puede existir en servidor con este nombre).
# Une ramas para que el grafo tenga un solo leaf con 0090.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0085_plantilla_desarme_estado_pieza"),
        ("taller", "0086_repuesto_zona_mapa_vista"),
    ]

    operations = []
