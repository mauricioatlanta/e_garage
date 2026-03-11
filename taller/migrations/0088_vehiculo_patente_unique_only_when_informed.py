# Restaurar unicidad (empresa, patente) solo cuando patente está informada.
# Permite múltiples vehículos con patente vacía o null por empresa (ej. desarme).

from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0087_plantilla_pieza_lado_zona"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="vehiculo",
            name="uq_empresa_patente",
        ),
        migrations.AddConstraint(
            model_name="vehiculo",
            constraint=models.UniqueConstraint(
                condition=Q(patente__isnull=False) & ~Q(patente=""),
                fields=("empresa", "patente"),
                name="uq_empresa_patente",
            ),
        ),
    ]
