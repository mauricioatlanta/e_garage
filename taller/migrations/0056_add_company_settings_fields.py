# Compatibility migration.
#
# The CompanySettings fields originally added here are already created by
# 0055_remove_logauditoria_empresa_and_more in the tracked migration graph.
# Keeping this migration as a no-op preserves history for databases that have
# applied 0056, while avoiding duplicate-column failures on fresh databases.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0055_remove_logauditoria_empresa_and_more"),
    ]

    operations = []
