from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("taller", "0051_configuracionempresa_rubros_serviciobase_rubros"),
    ]

    operations = [
        # Migración anulada: duplicada de 0052_add_is_trial_fields.
        # Se deja vacía para mantener consistencia del grafo sin re-ejecutar operaciones ya aplicadas.
    ]
