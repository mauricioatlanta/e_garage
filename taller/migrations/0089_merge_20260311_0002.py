# Merge migration (puede haberse generado en servidor con makemigrations --merge).
# Une ramas para resolver conflicto de hojas con 0089_catalogo_anio_desde_hasta.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0088_vehiculo_patente_unique_only_when_informed"),
    ]

    operations = []
