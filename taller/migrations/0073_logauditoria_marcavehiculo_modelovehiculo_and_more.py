from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0072_restore_is_trial_field"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Migración anulada por drift de state (RemoveField terms_conditions y/o tablas ya existentes).
        # Se deja vacía para restaurar consistencia del MigrationLoader/graph.
    ]
